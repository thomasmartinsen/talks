"""Run LibreOffice in sandboxed environments that block AF_UNIX sockets.

Some container / VM runtimes deny ``socket(AF_UNIX, …)`` at the seccomp
level.  LibreOffice relies on UNIX-domain sockets for internal IPC, so
this module detects the restriction at startup and, when necessary,
compiles a small ``LD_PRELOAD`` shim that transparently falls back to
``socketpair(2)`` plus a wake-pipe so that ``listen``/``accept``/``close``
continue to behave correctly from LibreOffice's point of view.

The shim technique is a standard Unix systems-programming pattern for
intercepting libc calls via ``dlsym(RTLD_NEXT, ...)``.  The specific
application to LibreOffice's AF_UNIX usage follows the well-documented
``LD_PRELOAD`` interposition approach described in the dlsym(3) man page
and various Unix programming references.  The socketpair(2) fallback for
blocked socket(2) calls is the canonical workaround in restricted
container environments.

On Windows, where ``LD_PRELOAD`` and the Unix socket shim do not apply,
this module skips the shim logic and simply resolves the local LibreOffice
binary. That keeps the helper usable across platforms instead of crashing
when ``socket.AF_UNIX`` is unavailable.
"""

from __future__ import annotations

import os
import shutil
import socket
import subprocess
import tempfile
from pathlib import Path
from typing import Sequence

_SHIM_LIB = Path(tempfile.gettempdir()) / "lo_unix_shim.so"


# ---------------------------------------------------------------------------
# Socket restriction detection
# ---------------------------------------------------------------------------

def detect_socket_restriction() -> bool:
    """Return ``True`` if ``AF_UNIX`` sockets cannot be created."""
    if os.name != "posix" or not hasattr(socket, "AF_UNIX"):
        return False
    try:
        probe = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        probe.close()
    except OSError:
        return True
    return False


# ---------------------------------------------------------------------------
# Shim compilation
# ---------------------------------------------------------------------------

_SHIM_C = r"""
/*
 * LD_PRELOAD shim: intercept socket/listen/accept/close for AF_UNIX FDs.
 *
 * When socket(AF_UNIX, …) is blocked by seccomp the shim creates a
 * socketpair instead and records bookkeeping in a per-FD struct.  A
 * wake pipe lets accept() block until close() signals completion.
 */
#define _GNU_SOURCE
#include <dlfcn.h>
#include <errno.h>
#include <stdlib.h>
#include <string.h>
#include <sys/socket.h>
#include <unistd.h>

/* Collected real libc entry points. */
static struct {
    int (*socket)(int, int, int);
    int (*listen)(int, int);
    int (*accept)(int, struct sockaddr *, socklen_t *);
    int (*close)(int);
} real_fns;

/* Per-FD state for shimmed descriptors. */
#define FD_LIMIT 1024
static struct {
    int  active;     /* non-zero if this FD was shimmed   */
    int  partner;    /* other end of the socketpair       */
    int  wake_rd;    /* read end of the notification pipe */
    int  wake_wr;    /* write end of the notification pipe*/
} fd_info[FD_LIMIT];

static int active_listener = -1;  /* FD that received listen() */

static void resolve_symbols(void) {
    if (real_fns.socket)
        return;
    real_fns.socket = dlsym(RTLD_NEXT, "socket");
    real_fns.listen = dlsym(RTLD_NEXT, "listen");
    real_fns.accept = dlsym(RTLD_NEXT, "accept");
    real_fns.close  = dlsym(RTLD_NEXT, "close");

    for (int i = 0; i < FD_LIMIT; i++) {
        fd_info[i].active   = 0;
        fd_info[i].partner  = -1;
        fd_info[i].wake_rd  = -1;
        fd_info[i].wake_wr  = -1;
    }
}

/* ---- socket --------------------------------------------------------- */
int socket(int domain, int type, int protocol) {
    resolve_symbols();
    if (domain != AF_UNIX)
        return real_fns.socket(domain, type, protocol);

    int fd = real_fns.socket(domain, type, protocol);
    if (fd >= 0)
        return fd;

    /* Real call denied; fall back to socketpair. */
    int pair[2];
    if (socketpair(AF_UNIX, type, protocol, pair) < 0) {
        errno = EPERM;
        return -1;
    }
    if (pair[0] < FD_LIMIT) {
        fd_info[pair[0]].active  = 1;
        fd_info[pair[0]].partner = pair[1];
        int pp[2];
        if (pipe(pp) == 0) {
            fd_info[pair[0]].wake_rd = pp[0];
            fd_info[pair[0]].wake_wr = pp[1];
        }
    }
    return pair[0];
}

/* ---- listen --------------------------------------------------------- */
int listen(int fd, int backlog) {
    resolve_symbols();
    if (fd >= 0 && fd < FD_LIMIT && fd_info[fd].active) {
        active_listener = fd;
        return 0;
    }
    return real_fns.listen(fd, backlog);
}

/* ---- accept --------------------------------------------------------- */
int accept(int fd, struct sockaddr *addr, socklen_t *len) {
    resolve_symbols();
    if (fd >= 0 && fd < FD_LIMIT && fd_info[fd].active) {
        if (fd_info[fd].wake_rd >= 0) {
            char byte;
            read(fd_info[fd].wake_rd, &byte, 1);
        }
        errno = ECONNABORTED;
        return -1;
    }
    return real_fns.accept(fd, addr, len);
}

/* ---- close ---------------------------------------------------------- */
int close(int fd) {
    resolve_symbols();
    if (fd >= 0 && fd < FD_LIMIT && fd_info[fd].active) {
        int is_listener = (fd == active_listener);
        fd_info[fd].active = 0;

        if (fd_info[fd].wake_wr >= 0) {
            write(fd_info[fd].wake_wr, "\0", 1);
            real_fns.close(fd_info[fd].wake_wr);
            fd_info[fd].wake_wr = -1;
        }
        if (fd_info[fd].wake_rd >= 0) {
            real_fns.close(fd_info[fd].wake_rd);
            fd_info[fd].wake_rd = -1;
        }
        if (fd_info[fd].partner >= 0) {
            real_fns.close(fd_info[fd].partner);
            fd_info[fd].partner = -1;
        }

        int rc = real_fns.close(fd);
        if (is_listener)
            _exit(0);
        return rc;
    }
    return real_fns.close(fd);
}
"""


def compile_shim() -> Path:
    """Compile the LD_PRELOAD shared object if it doesn't already exist."""
    if _SHIM_LIB.is_file():
        return _SHIM_LIB

    src = _SHIM_LIB.with_suffix(".c")
    src.write_text(_SHIM_C, encoding="utf-8")
    try:
        subprocess.run(
            ["gcc", "-shared", "-fPIC", "-o", str(_SHIM_LIB), str(src), "-ldl"],
            check=True,
            capture_output=True,
        )
    finally:
        src.unlink(missing_ok=True)
    return _SHIM_LIB


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def libreoffice_env() -> dict[str, str]:
    """Build an environment dict suitable for launching LibreOffice.

    Unconditionally sets ``SAL_USE_VCLPLUGIN=svp`` (headless rendering).
    When AF_UNIX sockets are blocked the compiled shim is added to
    ``LD_PRELOAD``.
    """
    env = os.environ.copy()
    env["SAL_USE_VCLPLUGIN"] = "svp"

    if detect_socket_restriction():
        lib = compile_shim()
        prev = env.get("LD_PRELOAD", "")
        env["LD_PRELOAD"] = f"{lib}:{prev}" if prev else str(lib)

    return env


def libreoffice_binary() -> str:
    """Return the best available LibreOffice executable for this host."""
    candidates: list[str | Path]
    if os.name == "nt":
        candidates = [
            "soffice.com",
            "soffice.exe",
            Path(r"C:\Program Files\LibreOffice\program\soffice.com"),
            Path(r"C:\Program Files\LibreOffice\program\soffice.exe"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.com"),
            Path(r"C:\Program Files (x86)\LibreOffice\program\soffice.exe"),
        ]
    else:
        candidates = ["soffice"]

    for candidate in candidates:
        if isinstance(candidate, Path):
            if candidate.is_file():
                return str(candidate)
            continue

        resolved = shutil.which(candidate)
        if resolved:
            return resolved

    raise FileNotFoundError(
        "LibreOffice executable not found. Install LibreOffice or ensure "
        "`soffice` is available on PATH."
    )


def run_libreoffice(
    args: Sequence[str],
    **subprocess_kwargs,
) -> subprocess.CompletedProcess:
    """Execute ``soffice`` with the sandboxed environment.

    Parameters
    ----------
    args:
        Command-line arguments forwarded to ``soffice``.
    subprocess_kwargs:
        Extra keyword arguments passed to :func:`subprocess.run`.
    """
    env = libreoffice_env()
    return subprocess.run([libreoffice_binary(), *args], env=env, **subprocess_kwargs)


if __name__ == "__main__":
    import sys

    result = run_libreoffice(sys.argv[1:])
    raise SystemExit(result.returncode)
