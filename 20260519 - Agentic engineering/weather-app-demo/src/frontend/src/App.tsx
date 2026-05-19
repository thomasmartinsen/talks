import { useCallback, useEffect, useRef, useState } from 'react'
import aspireLogo from '/Aspire.png'
import './App.css'

interface WeatherForecast {
  date: string
  temperatureC: number
  temperatureF: number
  summary: string
}

type LanguageCode = 'da' | 'en' | 'fi' | 'no' | 'sv'

const fallbackErrorKey = 'fetch-fallback'

interface TranslationSet {
  languageLabel: string
  languageSelectorAriaLabel: string
  appTitle: string
  appSubtitle: string
  weatherHeading: string
  temperatureUnitLegend: string
  fahrenheitLabel: string
  celsiusLabel: string
  refreshLabel: string
  refreshAriaLabel: string
  loadingLabel: string
  loadingWeatherAriaLabel: string
  loadingWeatherText: string
  weatherCardAriaLabel: string
  temperatureAriaLabel: string
  degreesLabel: string
  footerNavLabel: string
  learnMoreLabel: string
  opensInNewTabLabel: string
  visitAspireLabel: string
  viewOnGitHubLabel: string
  fetchErrorFallback: string
}

const languages: Array<{ code: LanguageCode; label: string }> = [
  { code: 'da', label: 'Dansk' },
  { code: 'en', label: 'English' },
  { code: 'fi', label: 'Suomi' },
  { code: 'no', label: 'Norsk' },
  { code: 'sv', label: 'Svenska' },
]

const localeByLanguage: Record<LanguageCode, string> = {
  da: 'da-DK',
  en: 'en-US',
  fi: 'fi-FI',
  no: 'nb-NO',
  sv: 'sv-SE',
}

const translations: Record<LanguageCode, TranslationSet> = {
  da: {
    languageLabel: 'Sprog',
    languageSelectorAriaLabel: 'V\u00e6lg brugerfladesprog',
    appTitle: 'Aspire Starter',
    appSubtitle: 'Moderne udvikling af distribuerede applikationer',
    weatherHeading: 'Vejrudsigt',
    temperatureUnitLegend: 'Temperaturenhed',
    fahrenheitLabel: 'Fahrenheit',
    celsiusLabel: 'Celsius',
    refreshLabel: 'Opdater',
    refreshAriaLabel: 'Opdater vejrudsigt',
    loadingLabel: 'Indl\u00e6ser...',
    loadingWeatherAriaLabel: 'Indl\u00e6ser vejrudsigt',
    loadingWeatherText: 'Indl\u00e6ser vejrudsigtsdata...',
    weatherCardAriaLabel: 'Vejr for {date}',
    temperatureAriaLabel: 'Temperatur: {value} {degrees} {unit}',
    degreesLabel: 'grader',
    footerNavLabel: 'Sidefodsnavigation',
    learnMoreLabel: 'L\u00e6r mere om Aspire',
    opensInNewTabLabel: '\u00e5bner i en ny fane',
    visitAspireLabel: 'Bes\u00f8g Aspires websted (\u00e5bner i en ny fane)',
    viewOnGitHubLabel: 'Se Aspire p\u00e5 GitHub (\u00e5bner i en ny fane)',
    fetchErrorFallback: 'Kunne ikke hente vejrdata',
  },
  en: {
    languageLabel: 'Language',
    languageSelectorAriaLabel: 'Select interface language',
    appTitle: 'Aspire Starter',
    appSubtitle: 'Modern distributed application development',
    weatherHeading: 'Weather Forecast',
    temperatureUnitLegend: 'Temperature unit',
    fahrenheitLabel: 'Fahrenheit',
    celsiusLabel: 'Celsius',
    refreshLabel: 'Refresh',
    refreshAriaLabel: 'Refresh weather forecast',
    loadingLabel: 'Loading...',
    loadingWeatherAriaLabel: 'Loading weather forecast',
    loadingWeatherText: 'Loading weather forecast data...',
    weatherCardAriaLabel: 'Weather for {date}',
    temperatureAriaLabel: 'Temperature: {value} {degrees} {unit}',
    degreesLabel: 'degrees',
    footerNavLabel: 'Footer navigation',
    learnMoreLabel: 'Learn more about Aspire',
    opensInNewTabLabel: 'opens in new tab',
    visitAspireLabel: 'Visit Aspire website (opens in new tab)',
    viewOnGitHubLabel: 'View Aspire on GitHub (opens in new tab)',
    fetchErrorFallback: 'Failed to fetch weather data',
  },
  fi: {
    languageLabel: 'Kieli',
    languageSelectorAriaLabel: 'Valitse k\u00e4ytt\u00f6liittym\u00e4n kieli',
    appTitle: 'Aspire Starter',
    appSubtitle: 'Nykyaikainen hajautettujen sovellusten kehitys',
    weatherHeading: 'S\u00e4\u00e4ennuste',
    temperatureUnitLegend: 'L\u00e4mp\u00f6tilayksikk\u00f6',
    fahrenheitLabel: 'Fahrenheit',
    celsiusLabel: 'Celsius',
    refreshLabel: 'P\u00e4ivit\u00e4',
    refreshAriaLabel: 'P\u00e4ivit\u00e4 s\u00e4\u00e4ennuste',
    loadingLabel: 'Ladataan...',
    loadingWeatherAriaLabel: 'Ladataan s\u00e4\u00e4ennustetta',
    loadingWeatherText: 'Ladataan s\u00e4\u00e4ennustedataa...',
    weatherCardAriaLabel: 'S\u00e4\u00e4 p\u00e4iv\u00e4lle {date}',
    temperatureAriaLabel: 'L\u00e4mp\u00f6tila: {value} {degrees} {unit}',
    degreesLabel: 'astetta',
    footerNavLabel: 'Alatunnisteen navigointi',
    learnMoreLabel: 'Lue lis\u00e4\u00e4 Aspiresta',
    opensInNewTabLabel: 'avautuu uuteen v\u00e4lilehteen',
    visitAspireLabel: 'Siirry Aspiren sivustolle (avautuu uuteen v\u00e4lilehteen)',
    viewOnGitHubLabel: 'N\u00e4yt\u00e4 Aspire GitHubissa (avautuu uuteen v\u00e4lilehteen)',
    fetchErrorFallback: 'S\u00e4\u00e4tietojen haku ep\u00e4onnistui',
  },
  no: {
    languageLabel: 'Spr\u00e5k',
    languageSelectorAriaLabel: 'Velg grensesnittspr\u00e5k',
    appTitle: 'Aspire Starter',
    appSubtitle: 'Moderne utvikling av distribuerte applikasjoner',
    weatherHeading: 'V\u00e6rvarsel',
    temperatureUnitLegend: 'Temperaturenhet',
    fahrenheitLabel: 'Fahrenheit',
    celsiusLabel: 'Celsius',
    refreshLabel: 'Oppdater',
    refreshAriaLabel: 'Oppdater v\u00e6rvarsel',
    loadingLabel: 'Laster...',
    loadingWeatherAriaLabel: 'Laster v\u00e6rvarsel',
    loadingWeatherText: 'Laster v\u00e6rdata...',
    weatherCardAriaLabel: 'V\u00e6r for {date}',
    temperatureAriaLabel: 'Temperatur: {value} {degrees} {unit}',
    degreesLabel: 'grader',
    footerNavLabel: 'Bunntekstnavigasjon',
    learnMoreLabel: 'L\u00e6r mer om Aspire',
    opensInNewTabLabel: '\u00e5pnes i ny fane',
    visitAspireLabel: 'Bes\u00f8k Aspire-nettstedet (\u00e5pnes i ny fane)',
    viewOnGitHubLabel: 'Vis Aspire p\u00e5 GitHub (\u00e5pnes i ny fane)',
    fetchErrorFallback: 'Kunne ikke hente v\u00e6rdata',
  },
  sv: {
    languageLabel: 'Spr\u00e5k',
    languageSelectorAriaLabel: 'V\u00e4lj gr\u00e4nssnittsspr\u00e5k',
    appTitle: 'Aspire Starter',
    appSubtitle: 'Modern utveckling av distribuerade applikationer',
    weatherHeading: 'V\u00e4derprognos',
    temperatureUnitLegend: 'Temperaturenhet',
    fahrenheitLabel: 'Fahrenheit',
    celsiusLabel: 'Celsius',
    refreshLabel: 'Uppdatera',
    refreshAriaLabel: 'Uppdatera v\u00e4derprognos',
    loadingLabel: 'Laddar...',
    loadingWeatherAriaLabel: 'Laddar v\u00e4derprognos',
    loadingWeatherText: 'Laddar v\u00e4derdata...',
    weatherCardAriaLabel: 'V\u00e4der f\u00f6r {date}',
    temperatureAriaLabel: 'Temperatur: {value} {degrees} {unit}',
    degreesLabel: 'grader',
    footerNavLabel: 'Sidfotsnavigering',
    learnMoreLabel: 'L\u00e4s mer om Aspire',
    opensInNewTabLabel: '\u00f6ppnas i ny flik',
    visitAspireLabel: 'Bes\u00f6k Aspires webbplats (\u00f6ppnas i ny flik)',
    viewOnGitHubLabel: 'Visa Aspire p\u00e5 GitHub (\u00f6ppnas i ny flik)',
    fetchErrorFallback: 'Det gick inte att h\u00e4mta v\u00e4derdata',
  },
}

const formatTranslation = (template: string, values: Record<string, string | number>) =>
  Object.entries(values).reduce(
    (result, [key, value]) => result.replace(`{${key}}`, String(value)),
    template,
  )

function App() {
  const [language, setLanguage] = useState<LanguageCode>('en')
  const [weatherData, setWeatherData] = useState<WeatherForecast[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [useCelsius, setUseCelsius] = useState(false)
  const [isLanguageFlyoutOpen, setIsLanguageFlyoutOpen] = useState(false)
  const languageFlyoutRef = useRef<HTMLDivElement | null>(null)

  const t = translations[language]
  const unitLabel = useCelsius ? t.celsiusLabel : t.fahrenheitLabel
  const selectedLanguageLabel = languages.find((option) => option.code === language)?.label ?? 'English'

  useEffect(() => {
    if (!isLanguageFlyoutOpen) {
      return
    }

    const closeOnEscape = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        setIsLanguageFlyoutOpen(false)
      }
    }

    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!languageFlyoutRef.current?.contains(event.target as Node)) {
        setIsLanguageFlyoutOpen(false)
      }
    }

    window.addEventListener('keydown', closeOnEscape)
    window.addEventListener('mousedown', closeOnOutsideClick)

    return () => {
      window.removeEventListener('keydown', closeOnEscape)
      window.removeEventListener('mousedown', closeOnOutsideClick)
    }
  }, [isLanguageFlyoutOpen])

  const fetchWeatherForecast = useCallback(async () => {
    setLoading(true)
    setError(null)

    try {
      const response = await fetch('/api/weatherforecast')

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }

      const data: WeatherForecast[] = await response.json()
      setWeatherData(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : fallbackErrorKey)
      console.error('Error fetching weather forecast:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void fetchWeatherForecast()
  }, [fetchWeatherForecast])

  const formatDate = (dateString: string) =>
    new Date(dateString).toLocaleDateString(localeByLanguage[language], {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    })

  return (
    <div className="app-container">
      <header className="app-header">
        <div className="language-flyout" ref={languageFlyoutRef}>
          <button
            type="button"
            className="language-flyout-toggle"
            aria-haspopup="menu"
            aria-expanded={isLanguageFlyoutOpen}
            aria-controls="language-flyout-menu"
            aria-label={t.languageSelectorAriaLabel}
            onClick={() => setIsLanguageFlyoutOpen((open) => !open)}
          >
            <span>{t.languageLabel}</span>
            <strong>{selectedLanguageLabel}</strong>
          </button>
          {isLanguageFlyoutOpen && (
            <div id="language-flyout-menu" className="language-flyout-menu" role="menu" aria-label={t.languageSelectorAriaLabel}>
              {languages.map((option) => (
                <button
                  key={option.code}
                  type="button"
                  role="menuitemradio"
                  aria-checked={language === option.code}
                  className={`language-flyout-option ${language === option.code ? 'active' : ''}`}
                  onClick={() => {
                    setLanguage(option.code)
                    setIsLanguageFlyoutOpen(false)
                  }}
                >
                  {option.label}
                </button>
              ))}
            </div>
          )}
        </div>
        <a
          href="https://aspire.dev"
          target="_blank"
          rel="noopener noreferrer"
          aria-label={t.visitAspireLabel}
          className="logo-link"
        >
          <img src={aspireLogo} className="logo" alt="Aspire logo" />
        </a>
        <h1 className="app-title">{t.appTitle}</h1>
        <p className="app-subtitle">{t.appSubtitle}</p>
      </header>

      <main className="main-content">
        <section className="weather-section" aria-labelledby="weather-heading">
          <div className="card">
            <div className="section-header">
              <h2 id="weather-heading" className="section-title">{t.weatherHeading}</h2>
              <div className="header-actions">
                <fieldset className="toggle-switch" aria-label={t.temperatureUnitLegend}>
                  <legend className="visually-hidden">{t.temperatureUnitLegend}</legend>
                  <button
                    className={`toggle-option ${!useCelsius ? 'active' : ''}`}
                    onClick={() => setUseCelsius(false)}
                    aria-pressed={!useCelsius}
                    type="button"
                  >
                    <span aria-hidden="true">&deg;F</span>
                    <span className="visually-hidden">{t.fahrenheitLabel}</span>
                  </button>
                  <button
                    className={`toggle-option ${useCelsius ? 'active' : ''}`}
                    onClick={() => setUseCelsius(true)}
                    aria-pressed={useCelsius}
                    type="button"
                  >
                    <span aria-hidden="true">&deg;C</span>
                    <span className="visually-hidden">{t.celsiusLabel}</span>
                  </button>
                </fieldset>
                <button
                  className="refresh-button"
                  onClick={fetchWeatherForecast}
                  disabled={loading}
                  aria-label={loading ? t.loadingWeatherAriaLabel : t.refreshAriaLabel}
                  type="button"
                >
                  <svg
                    className={`refresh-icon ${loading ? 'spinning' : ''}`}
                    width="20"
                    height="20"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    aria-hidden="true"
                    focusable="false"
                  >
                    <path d="M21.5 2v6h-6M2.5 22v-6h6M2 11.5a10 10 0 0 1 18.8-4.3M22 12.5a10 10 0 0 1-18.8 4.2" />
                  </svg>
                  <span>{loading ? t.loadingLabel : t.refreshLabel}</span>
                </button>
              </div>
            </div>

            {error && (
              <div className="error-message" role="alert" aria-live="polite">
                <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" aria-hidden="true">
                  <circle cx="12" cy="12" r="10" />
                  <line x1="12" y1="8" x2="12" y2="12" />
                  <line x1="12" y1="16" x2="12.01" y2="16" />
                </svg>
                <span>{error === fallbackErrorKey ? t.fetchErrorFallback : error}</span>
              </div>
            )}

            {loading && weatherData.length === 0 && (
              <div className="loading-skeleton" role="status" aria-live="polite" aria-label={t.loadingWeatherAriaLabel}>
                {[...Array(5)].map((_, index) => (
                  <div key={index} className="skeleton-row" aria-hidden="true" />
                ))}
                <span className="visually-hidden">{t.loadingWeatherText}</span>
              </div>
            )}

            {weatherData.length > 0 && (
              <div className="weather-grid">
                {weatherData.map((forecast, index) => (
                  <article
                    key={index}
                    className="weather-card"
                    aria-label={formatTranslation(t.weatherCardAriaLabel, { date: formatDate(forecast.date) })}
                  >
                    <h3 className="weather-date">
                      <time dateTime={forecast.date}>{formatDate(forecast.date)}</time>
                    </h3>
                    <p className="weather-summary">{forecast.summary}</p>
                    <div
                      className="weather-temps"
                      aria-label={formatTranslation(t.temperatureAriaLabel, {
                        value: useCelsius ? forecast.temperatureC : forecast.temperatureF,
                        degrees: t.degreesLabel,
                        unit: unitLabel,
                      })}
                    >
                      <div className="temp-group">
                        <span className="temp-value" aria-hidden="true">
                          {useCelsius ? forecast.temperatureC : forecast.temperatureF}&deg;
                        </span>
                        <span className="temp-unit" aria-hidden="true">{unitLabel}</span>
                      </div>
                    </div>
                  </article>
                ))}
              </div>
            )}
          </div>
        </section>
      </main>

      <footer className="app-footer">
        <nav aria-label={t.footerNavLabel}>
          <a href="https://aspire.dev" target="_blank" rel="noopener noreferrer">
            {t.learnMoreLabel}<span className="visually-hidden"> ({t.opensInNewTabLabel})</span>
          </a>
          <a
            href="https://github.com/dotnet/aspire"
            target="_blank"
            rel="noopener noreferrer"
            className="github-link"
            aria-label={t.viewOnGitHubLabel}
          >
            <img src="/github.svg" alt="" width="24" height="24" aria-hidden="true" />
            <span className="visually-hidden">GitHub</span>
          </a>
        </nav>
      </footer>
    </div>
  )
}

export default App