# Azure Container Apps Deployment Agent

This agent provides expert guidance for deploying .NET Aspire solutions to Azure using Container Apps with GitHub Actions.

## Overview

When deploying .NET Aspire backends to Azure Container Apps, follow this proven architecture and avoid the documented pitfalls.

## How to use

Reference the file in in Copilot Chat: @workspace #file:.github/agents/azure-container-apps-deployment.md deploy my Aspire app to Azure
Or add to copilot-instructions.md: Include a reference to load this agent file for Azure deployment tasks

---

## Architecture

### Deployment Flow (Critical Order)

The deployment MUST be split into phases to avoid image-not-found errors:

1. **Phase 1: Infrastructure** - Deploy ACR, Log Analytics, Container Apps Environment, PostgreSQL, Redis
2. **Phase 2: Build & Push** - Build Docker images and push to ACR
3. **Phase 3: Container Apps** - Deploy Container Apps (only after images exist in ACR)

### Bicep Structure

```
infra/
├── main-infra.bicep          # Infrastructure without Container Apps
├── main-apps.bicep           # Container Apps only (resource group scope)
├── modules/
│   ├── shared.bicep          # Log Analytics + Container Apps Environment
│   ├── postgres.bicep        # PostgreSQL Flexible Server
│   ├── redis.bicep           # Azure Cache for Redis
│   ├── api.bicep             # API Container App
│   ├── container-registry.bicep
│   └── container-registry-standalone.bicep  # Subscription-scoped ACR
└── parameters/
    ├── dev.bicepparam
    └── prod.bicepparam
```

### GitHub Workflow Structure

```
.github/workflows/
├── deploy-dev.yml              # Main dev workflow (triggered on push)
├── deploy-prod.yml             # Main prod workflow (triggered on release)
├── deploy-infrastructure.yml   # Reusable: ACR + infrastructure
├── build-container.yml         # Reusable: Build & push to ACR
└── deploy-container-apps.yml   # Reusable: Deploy Container Apps
```

---

## Known Pitfalls and Solutions

### 1. ACR SKU Not Supported in Certain Regions

**Problem**: Basic and sometimes Standard ACR SKUs are not available in all regions (e.g., swedencentral).

**Solution**: 
- Deploy ACR to `westeurope` (or another region with full SKU support)
- Use `Standard` SKU minimum (Basic often unavailable)
- Remove `retentionPolicy` from ACR config (requires Premium SKU)

```bicep
// ACR module - use separate location parameter
param location string = 'westeurope'  // NOT swedencentral

var skuName = 'Standard'  // NOT Basic

resource acr 'Microsoft.ContainerRegistry/registries@2023-11-01-preview' = {
  name: acrName
  location: location
  sku: { name: skuName }
  properties: {
    adminUserEnabled: false
    publicNetworkAccess: 'Enabled'
    // NO retentionPolicy - requires Premium
  }
}
```

### 2. Container App Fails - Image Not Found

**Problem**: `MANIFEST_UNKNOWN: manifest tagged by "latest" is not found`

**Solution**: 
- Split deployment into infrastructure-first, then apps-after-image-push
- Create `main-infra.bicep` (no Container Apps)
- Create `main-apps.bicep` (Container Apps only, resource group scope)
- Deploy infrastructure → Build/push image → Deploy apps

### 3. Connection Strings with Special Characters Break Deployment

**Problem**: `unrecognized template parameter 'Mode'` - caused by `;`, `=`, `,` in connection strings being parsed as parameter separators.

**Solution**: Use JSON parameters file instead of inline parameters:

```yaml
- name: Get Infrastructure Values
  id: infra
  run: |
    # Build connection strings
    PSQL_CONN="Host=${PSQL_HOST};Database=ads-db;Username=adsadmin;Password=${{ secrets.POSTGRES_ADMIN_PASSWORD }};SSL Mode=Require"
    REDIS_CONN="${REDIS_HOST}:6380,password=${REDIS_KEY},ssl=True,abortConnect=False"
    
    # Create parameters file (handles special characters)
    cat > parameters.json << EOF
    {
      "\$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentParameters.json#",
      "contentVersion": "1.0.0.0",
      "parameters": {
        "postgresConnectionString": { "value": "${PSQL_CONN}" },
        "redisConnectionString": { "value": "${REDIS_CONN}" }
      }
    }
    EOF

- name: Deploy
  run: |
    az deployment group create \
      --template-file ./infra/main-apps.bicep \
      --parameters @parameters.json
```

### 4. Secrets Cannot Be Passed Between Workflow Jobs

**Problem**: GitHub Actions doesn't reliably pass secrets as job outputs. Connection strings appear empty.

**Solution**: Retrieve values directly from Azure in the job that needs them:

```yaml
- name: Get Infrastructure Values
  run: |
    # Get PostgreSQL host from Azure
    PSQL_HOST=$(az postgres flexible-server show \
      --name "psql-ads-${{ inputs.environment }}" \
      --resource-group "$RG" \
      --query fullyQualifiedDomainName -o tsv)
    
    # Get Redis key from Azure
    REDIS_KEY=$(az redis list-keys \
      --name "redis-ads-${{ inputs.environment }}" \
      --resource-group "$RG" \
      --query primaryKey -o tsv)
```

### 5. Unused Bicep Parameters Cause Warnings

**Problem**: Warnings for unused `containerAppsEnvironmentId` parameters.

**Solution**: Remove unused parameters from modules. Originally added for potential VNet integration but not needed for basic setup.

### 6. Secrets in Bicep Outputs

**Problem**: `outputs-should-not-contain-secrets` warning for connection strings.

**Solution**: Add disable directive (connection strings are passed to Container Apps secrets, not exposed):

```bicep
#disable-next-line outputs-should-not-contain-secrets
output connectionString string = 'Host=...'
```

### 7. vars vs secrets for Passwords

**Problem**: `POSTGRES_ADMIN_PASSWORD` was empty because workflow used `vars.` instead of `secrets.`

**Solution**: Always use `secrets.POSTGRES_ADMIN_PASSWORD` for sensitive values.

---

## Required GitHub Secrets

```
AZURE_CREDENTIALS          # Service principal JSON
AZURE_AD_TENANT_ID         # Azure AD tenant
AZURE_AD_CLIENT_ID         # App registration client ID
AZURE_AD_CLIENT_SECRET     # App registration secret
AZURE_AD_AUDIENCE          # API audience URI
POSTGRES_ADMIN_PASSWORD    # PostgreSQL admin password
```

---

## Resource Naming Convention

| Resource | Pattern | Example |
|----------|---------|---------|
| Resource Group | `rg-{app}-{env}` | `rg-ads-dev` |
| Container Apps Environment | `cae-{app}-{env}` | `cae-ads-dev` |
| Container App | `ca-{app}-{service}-{env}` | `ca-ads-api-dev` |
| PostgreSQL | `psql-{app}-{env}` | `psql-ads-dev` |
| Redis | `redis-{app}-{env}` | `redis-ads-dev` |
| Container Registry | `acr{app}{env}` | `acradsdev` |
| Log Analytics | `log-{app}-{env}` | `log-ads-dev` |
| Managed Identity | `id-{app}-{service}-{env}` | `id-ads-api-dev` |

---

## Environment Differences

| Setting | Dev | Prod |
|---------|-----|------|
| PostgreSQL SKU | Standard_B1ms (Burstable) | Standard_D2ds_v4 (GeneralPurpose) |
| PostgreSQL Storage | 32 GB | 128 GB |
| PostgreSQL HA | Disabled | ZoneRedundant |
| PostgreSQL Backup Retention | 7 days | 35 days |
| Redis SKU | Basic C0 | Standard C1 |
| Container App CPU | 0.5 | 1.0 |
| Container App Memory | 1Gi | 2Gi |
| Container App Min Replicas | 1 | 2 |
| Container App Max Replicas | 3 | 10 |
| Log Retention | 30 days | 90 days |
| Zone Redundancy | No | Yes |

---

## Dockerfile Requirements

Build from backend directory context:

```dockerfile
FROM mcr.microsoft.com/dotnet/sdk:10.0 AS build
WORKDIR /src

# Copy project files (relative to backend/)
COPY ADS.API/ADS.API.csproj ADS.API/
COPY ADS.Application/ADS.Application.csproj ADS.Application/
# ... other projects

RUN dotnet restore ADS.API/ADS.API.csproj
COPY . .
WORKDIR /src/ADS.API
RUN dotnet publish -c Release -o /app/publish

FROM mcr.microsoft.com/dotnet/aspnet:10.0 AS final
WORKDIR /app
COPY --from=build /app/publish .
ENV ASPNETCORE_URLS=http://+:8080
EXPOSE 8080
USER app
ENTRYPOINT ["dotnet", "ADS.API.dll"]
```

---

## Production Deployment Triggers

1. **Automatic**: Create and publish a GitHub Release
2. **Manual**: Actions → Deploy to Production → Run workflow → Type "DEPLOY"

Production has an approval gate - configure in Settings → Environments → prod → Required reviewers.
