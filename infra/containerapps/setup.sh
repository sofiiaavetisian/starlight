#!/usr/bin/env bash

set -euo pipefail

if ! command -v az >/dev/null 2>&1; then
  echo "Azure CLI (az) is required. Install it from https://learn.microsoft.com/cli/azure/install-azure-cli" >&2
  exit 1
fi

# Ensure the Container Apps extension is available
az config set extension.use_dynamic_install=yes_without_prompt >/dev/null
az extension show --name containerapp >/dev/null 2>&1 || az extension add --name containerapp >/dev/null

required_vars=(
  RESOURCE_GROUP
  LOCATION
  CONTAINERAPPS_ENVIRONMENT
  LOG_ANALYTICS_WORKSPACE
  STORAGE_ACCOUNT_NAME
  STORAGE_FILE_SHARE
  POSTGRES_APP_NAME
  POSTGRES_DB
  POSTGRES_USER
  POSTGRES_PASSWORD
)

for var in "${required_vars[@]}"; do
  if [[ -z "${!var:-}" ]]; then
    echo "Environment variable $var is required." >&2
    exit 1
  fi
done

CONTAINERAPPS_STORAGE_NAME=${CONTAINERAPPS_STORAGE_NAME:-postgresdata}
POSTGRES_IMAGE=${POSTGRES_IMAGE:-postgres:16}

echo "Checking Azure providers (Microsoft.App, Microsoft.OperationalInsights)..."
for ns in Microsoft.App Microsoft.OperationalInsights; do
  state=$(az provider show --namespace "$ns" --query "registrationState" -o tsv || echo "Unknown")
  echo "  $ns: $state"
  if [[ "$state" != "Registered" ]]; then
    echo "ERROR: Provider $ns is not registered for this subscription." >&2
    echo "Ask your subscription administrator or instructor to register it, then re-run this script." >&2
    exit 1
  fi
done

echo "Creating (or updating) Log Analytics workspace ${LOG_ANALYTICS_WORKSPACE}..."
az monitor log-analytics workspace create \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${LOG_ANALYTICS_WORKSPACE}" \
  --location "${LOCATION}" \
  --retention-time 30 \
  --output none

LOG_WORKSPACE_ID=$(az monitor log-analytics workspace show \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${LOG_ANALYTICS_WORKSPACE}" \
  --query customerId -o tsv)

LOG_WORKSPACE_KEY=$(az monitor log-analytics workspace get-shared-keys \
  --resource-group "${RESOURCE_GROUP}" \
  --workspace-name "${LOG_ANALYTICS_WORKSPACE}" \
  --query primarySharedKey -o tsv)

echo "Creating Container Apps environment ${CONTAINERAPPS_ENVIRONMENT}..."
az containerapp env create \
  --name "${CONTAINERAPPS_ENVIRONMENT}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --logs-destination log-analytics \
  --logs-workspace-id "${LOG_WORKSPACE_ID}" \
  --logs-workspace-key "${LOG_WORKSPACE_KEY}" \
  --output none

echo "Creating storage account ${STORAGE_ACCOUNT_NAME}..."
az storage account create \
  --name "${STORAGE_ACCOUNT_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --location "${LOCATION}" \
  --sku Standard_LRS \
  --kind StorageV2 \
  --output none

STORAGE_KEY=$(az storage account keys list \
  --account-name "${STORAGE_ACCOUNT_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query "[0].value" -o tsv)

echo "Creating Azure File share ${STORAGE_FILE_SHARE}..."
az storage share create \
  --name "${STORAGE_FILE_SHARE}" \
  --account-name "${STORAGE_ACCOUNT_NAME}" \
  --account-key "${STORAGE_KEY}" \
  --quota 20 \
  --output none

echo "Creating PostgreSQL container app ${POSTGRES_APP_NAME}..."
az containerapp create \
  --name "${POSTGRES_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --environment "${CONTAINERAPPS_ENVIRONMENT}" \
  --image "${POSTGRES_IMAGE}" \
  --target-port 5432 \
  --ingress internal \
  --min-replicas 1 \
  --max-replicas 1 \
  --revisions-mode Single \
  --secrets postgres-password="${POSTGRES_PASSWORD}" \
  --env-vars \
      POSTGRES_DB="${POSTGRES_DB}" \
      POSTGRES_USER="${POSTGRES_USER}" \
      POSTGRES_PASSWORD="secretref:postgres-password" \
  --output none

echo "PostgreSQL container app created. Fetching its internal FQDN..."
POSTGRES_FQDN=$(az containerapp show \
  --name "${POSTGRES_APP_NAME}" \
  --resource-group "${RESOURCE_GROUP}" \
  --query "properties.configuration.ingress.fqdn" -o tsv)

cat <<EOF

Setup complete.

Internal PostgreSQL host: ${POSTGRES_FQDN}
Use the following values in GitHub secrets and the CD workflow:
  POSTGRES_HOST=${POSTGRES_FQDN}
  POSTGRES_DB=${POSTGRES_DB}
  POSTGRES_USER=${POSTGRES_USER}
  POSTGRES_PASSWORD=<store securely>

Remember: the Container Apps secret name is 'postgres-password' (lowercase),
but inside the container it is exposed as POSTGRES_PASSWORD.
EOF