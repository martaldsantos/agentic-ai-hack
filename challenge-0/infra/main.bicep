@allowed([
  'swedencentral'
])
@description('Azure location where resources should be deployed (e.g., swedencentral)')
param location string = 'swedencentral'

@description('Optional: Object ID (Principal ID) of the service principal to grant permissions to AI Foundry resources')
param servicePrincipalObjectId string = ''

var prefix = 'msagthack'
var suffix = uniqueString(resourceGroup().id)

var storageAccountName = replace('${prefix}-sa-${suffix}', '-', '')
var logAnalyticsWorkspaceName = '${prefix}-loganalytics-${suffix}'
var searchServiceName = '${prefix}-search-${suffix}'
var containerRegistryName = replace('${prefix}cr${suffix}', '-', '')
var keyVaultName = '${prefix}kv${suffix}'
var aiFoundryName = '${prefix}-aifoundry-${suffix}'
var aiProjectName = '${prefix}-aiproject-${suffix}'
var applicationInsightsName = '${prefix}-appinsights-${suffix}'
var cosmosDbAccountName = '${prefix}-cosmos-${suffix}'

var cognitiveServicesUserRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'a97b65f3-24c7-4388-baec-2e87135dc908'
)
var searchServiceContributorRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '7ca78c08-252a-4471-8644-bb5ff32d4ba0'
)
var aiDeveloperRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  '64702f94-c441-49e6-a78b-ef80e0188fee'
)
var contributorRoleId = subscriptionResourceId(
  'Microsoft.Authorization/roleDefinitions',
  'b24988ac-6180-42a0-ab88-20f7382dd24c'
)

resource storageAccount 'Microsoft.Storage/storageAccounts@2023-05-01' = {
  name: storageAccountName
  location: location
  sku: {
    name: 'Standard_LRS'
  }
  kind: 'StorageV2'
  properties: {
    allowBlobPublicAccess: false
    networkAcls: {
      defaultAction: 'Allow'
    }
  }
}

resource logAnalyticsWorkspace 'Microsoft.OperationalInsights/workspaces@2021-06-01' = {
  name: logAnalyticsWorkspaceName
  location: location
  properties: {
    retentionInDays: 30
    features: {
      searchVersion: 1
    }
    sku: {
      name: 'PerGB2018'
    }
  }
}

resource cosmosDbAccount 'Microsoft.DocumentDB/databaseAccounts@2023-04-15' = {
  name: cosmosDbAccountName
  location: location
  kind: 'GlobalDocumentDB'
  identity: {
    type: 'SystemAssigned'
  }
  properties: {
    consistencyPolicy: {
      defaultConsistencyLevel: 'Session'
    }
    locations: [
      {
        locationName: location
        failoverPriority: 0
        isZoneRedundant: false
      }
    ]
    databaseAccountOfferType: 'Standard'
    enableAutomaticFailover: false
    enableMultipleWriteLocations: false
    capabilities: [
      {
        name: 'EnableServerless'
      }
    ]
  }
}

resource searchService 'Microsoft.Search/searchServices@2023-11-01' = {
  name: searchServiceName
  location: location
  sku: {
    name: 'basic'
  }
  properties: {
    hostingMode: 'default'
    replicaCount: 1
    partitionCount: 1
  }
}

resource containerRegistry 'Microsoft.ContainerRegistry/registries@2023-07-01' = {
  name: containerRegistryName
  location: location
  sku: {
    name: 'Basic'
  }
  properties: {
    adminUserEnabled: true
  }
}

resource applicationInsights 'Microsoft.Insights/components@2020-02-02' = {
  name: applicationInsightsName
  location: location
  kind: 'web'
  properties: {
    Application_Type: 'web'
    WorkspaceResourceId: logAnalyticsWorkspace.id
  }
}

resource keyVault 'Microsoft.KeyVault/vaults@2023-07-01' = {
  name: keyVaultName
  location: location
  properties: {
    sku: {
      family: 'A'
      name: 'standard'
    }
    tenantId: subscription().tenantId
    accessPolicies: []
    enabledForDeployment: false
    enabledForDiskEncryption: false
    enabledForTemplateDeployment: false
    enableSoftDelete: true
    softDeleteRetentionInDays: 90
    enableRbacAuthorization: true
  }
}

resource aiFoundry 'Microsoft.CognitiveServices/accounts@2025-04-01-preview' = {
  name: aiFoundryName
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  sku: {
    name: 'S0'
  }
  kind: 'AIServices'
  properties: {
    allowProjectManagement: true
    customSubDomainName: aiFoundryName
    disableLocalAuth: false
  }
}

resource aiProject 'Microsoft.CognitiveServices/accounts/projects@2025-04-01-preview' = {
  name: aiProjectName
  parent: aiFoundry
  location: location
  identity: {
    type: 'SystemAssigned'
  }
  properties: {}
}

resource gpt4MiniDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  name: 'gpt-4.1-mini'
  parent: aiFoundry
  sku: {
    capacity: 200
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: 'gpt-4.1-mini'
      format: 'OpenAI'
    }
  }
}

resource embeddingDeployment 'Microsoft.CognitiveServices/accounts/deployments@2024-10-01' = {
  name: 'text-embedding-ada-002'
  parent: aiFoundry
  sku: {
    capacity: 200
    name: 'GlobalStandard'
  }
  properties: {
    model: {
      name: 'text-embedding-ada-002'
      format: 'OpenAI'
    }
  }
  dependsOn: [
    gpt4MiniDeployment
  ]
}

resource projectAIFoundryRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(aiFoundry.id, aiProject.id, cognitiveServicesUserRoleId)
  scope: aiFoundry
  properties: {
    roleDefinitionId: cognitiveServicesUserRoleId
    principalId: aiProject.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource aiFoundrySearchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, aiFoundry.id, searchServiceContributorRoleId)
  scope: searchService
  properties: {
    roleDefinitionId: searchServiceContributorRoleId
    principalId: aiFoundry.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource projectSearchRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = {
  name: guid(searchService.id, aiProject.id, searchServiceContributorRoleId)
  scope: searchService
  properties: {
    roleDefinitionId: searchServiceContributorRoleId
    principalId: aiProject.identity.principalId
    principalType: 'ServicePrincipal'
  }
}

resource servicePrincipalCognitiveServicesUserRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(servicePrincipalObjectId)) {
  name: guid(aiFoundry.id, servicePrincipalObjectId, cognitiveServicesUserRoleId)
  scope: aiFoundry
  properties: {
    roleDefinitionId: cognitiveServicesUserRoleId
    principalId: servicePrincipalObjectId
    principalType: 'ServicePrincipal'
  }
}

resource servicePrincipalAIDeveloperRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(servicePrincipalObjectId)) {
  name: guid(aiFoundry.id, servicePrincipalObjectId, aiDeveloperRoleId)
  scope: aiFoundry
  properties: {
    roleDefinitionId: aiDeveloperRoleId
    principalId: servicePrincipalObjectId
    principalType: 'ServicePrincipal'
  }
}

resource servicePrincipalContributorRoleAssignment 'Microsoft.Authorization/roleAssignments@2022-04-01' = if (!empty(servicePrincipalObjectId)) {
  name: guid(aiFoundry.id, servicePrincipalObjectId, contributorRoleId)
  scope: aiFoundry
  properties: {
    roleDefinitionId: contributorRoleId
    principalId: servicePrincipalObjectId
    principalType: 'ServicePrincipal'
  }
}

resource searchConnection 'Microsoft.CognitiveServices/accounts/connections@2025-04-01-preview' = {
  name: '${aiFoundry.name}-aisearch'
  parent: aiFoundry
  properties: {
    category: 'CognitiveSearch'
    target: 'https://${searchServiceName}.search.windows.net'
    authType: 'ApiKey'
    isSharedToAll: true
    credentials: {
      key: searchService.listAdminKeys().primaryKey
    }
    metadata: {
      ApiType: 'Azure'
      ResourceId: searchService.id
      location: location
    }
  }
}

output storageAccountName string = storageAccountName
output logAnalyticsWorkspaceName string = logAnalyticsWorkspaceName
output searchServiceName string = searchServiceName
output aiFoundryHubName string = aiFoundryName
output aiFoundryProjectName string = aiProjectName
output keyVaultName string = keyVaultName
output containerRegistryName string = containerRegistryName
output applicationInsightsName string = applicationInsightsName
output cosmosDbAccountName string = cosmosDbAccountName
output searchServiceEndpoint string = 'https://${searchServiceName}.search.windows.net/'
output aiFoundryHubEndpoint string = 'https://ml.azure.com/home?wsid=${aiFoundry.id}'
output aiFoundryProjectEndpoint string = 'https://ai.azure.com/build/overview?wsid=${aiProject.id}'
output cosmosDbEndpoint string = cosmosDbAccount.properties.documentEndpoint
