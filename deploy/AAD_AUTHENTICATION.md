# Azure AD Authentication Setup

This application uses Azure Active Directory (AAD) authentication to connect to Azure AI Foundry services.

## Important Note
**Azure AI Foundry (AIProjectClient) only supports AAD authentication**, not API keys. The Azure OpenAI API key in your `.env` file is not used for the AI Foundry connection.

## Local Development Setup

### Prerequisites
1. Install Azure CLI: https://docs.microsoft.com/en-us/cli/azure/install-azure-cli
2. Have access to the Azure AI Foundry project

### Authentication Steps
```bash
# 1. Login to Azure
az login

# 2. Set the correct subscription (if you have multiple)
az account set --subscription "6797c788-362f-45f5-a36e-6b8d83b7121c"

# 3. Verify you're logged in
az account show

# 4. Run the application locally
cd deploy
docker-compose up
```

## CI/CD and Production Setup

For automated environments (CI/CD, production), use a Service Principal:

### 1. Create a Service Principal
```bash
# Create service principal and save the output
az ad sp create-for-rbac \
  --name "calendar-agent-sp" \
  --role "Contributor" \
  --scopes "/subscriptions/6797c788-362f-45f5-a36e-6b8d83b7121c/resourceGroups/azure_for_students_agents_hub"
```

This will output:
```json
{
  "appId": "YOUR_CLIENT_ID",
  "displayName": "calendar-agent-sp",
  "password": "YOUR_CLIENT_SECRET",
  "tenant": "YOUR_TENANT_ID"
}
```

### 2. Grant Access to AI Foundry Project
In Azure Portal:
1. Go to your AI Foundry project
2. Access Control (IAM)
3. Add role assignment
4. Select "Contributor" or "Azure AI Developer" role
5. Select your service principal

### 3. Set Environment Variables
Add these to your `.env` file or CI/CD environment:
```bash
# Service Principal Authentication
AZURE_CLIENT_ID=<appId from above>
AZURE_TENANT_ID=<tenant from above>
AZURE_CLIENT_SECRET=<password from above>
```

### 4. Docker Compose Configuration
Update `docker-compose.yml` to include these environment variables:
```yaml
agent-api:
  environment:
    # ... existing vars ...
    AZURE_CLIENT_ID: ${AZURE_CLIENT_ID}
    AZURE_TENANT_ID: ${AZURE_TENANT_ID}
    AZURE_CLIENT_SECRET: ${AZURE_CLIENT_SECRET}
```

## Troubleshooting

### Error: "Unauthorized"
- Ensure you're logged in: `az login`
- Check subscription: `az account show`
- Verify access to the AI Foundry project

### Error: "DefaultAzureCredential failed"
- For local: Run `az login`
- For CI/CD: Ensure service principal env vars are set
- Check the credential chain order

### Credential Chain Order
DefaultAzureCredential tries these methods in order:
1. Environment variables (AZURE_CLIENT_ID, etc.)
2. Managed Identity (in Azure)
3. Azure CLI (`az login`)
4. Visual Studio Code
5. Azure PowerShell

## Security Best Practices

1. **Never commit secrets**: Keep service principal credentials in secure environment variables
2. **Use Key Vault**: Store sensitive credentials in Azure Key Vault for production
3. **Rotate credentials**: Regularly rotate service principal passwords
4. **Minimal permissions**: Grant only necessary permissions to service principals
5. **Use Managed Identity**: When running in Azure, use Managed Identity instead of service principals

## Environment Variables Reference

| Variable | Description | Required |
|----------|-------------|----------|
| `PROJECT_CONNECTION_STRING` | AI Foundry project connection | Yes |
| `MODEL_DEPLOYMENT_NAME` | Model deployment name (e.g., "gpt-4.1") | Yes |
| `AZURE_CLIENT_ID` | Service principal application ID | For CI/CD |
| `AZURE_TENANT_ID` | Azure AD tenant ID | For CI/CD |
| `AZURE_CLIENT_SECRET` | Service principal password | For CI/CD |

## Links
- [Azure CLI Installation](https://docs.microsoft.com/en-us/cli/azure/install-azure-cli)
- [Service Principal Documentation](https://docs.microsoft.com/en-us/azure/active-directory/develop/app-objects-and-service-principals)
- [DefaultAzureCredential](https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity.defaultazurecredential)
- [Azure AI Foundry Documentation](https://learn.microsoft.com/en-us/azure/ai-foundry/)