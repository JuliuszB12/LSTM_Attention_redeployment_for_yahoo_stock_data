param (
    [string]$resourceGroupName,
    [string]$functionAppName
)

$vmName = "airflow"
$storageAccountName = "kafkastockdata1"
$amlWorkspaceName = "mlserving"
$vm = Get-AzVM -ResourceGroupName $resourceGroupName -Name $vmName
$storageAccount = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
$functionApp = Get-AzWebApp -ResourceGroupName $resourceGroupName -Name $functionAppName
$amlWorkspace = Get-AzResource -ResourceGroupName $resourceGroupName -ResourceType "Microsoft.MachineLearningServices/workspaces" -Name $amlWorkspaceName
$vmResourceId = $vm.Identity.PrincipalId
$storageAccountResourceId = $storageAccount.Id
$amlWorkspaceResourceId = $amlWorkspace.ResourceId
$principalId = $functionApp.Identity.PrincipalId
New-AzRoleAssignment -ObjectId $vmResourceId -RoleDefinitionName "Contributor" -Scope $storageAccountResourceId
New-AzRoleAssignment -ObjectId $vmResourceId -RoleDefinitionName "Storage Blob Data Contributor" -Scope $storageAccountResourceId
New-AzRoleAssignment -ObjectId $vmResourceId -RoleDefinitionName "Contributor" -Scope $amlWorkspaceResourceId
New-AzRoleAssignment -ObjectId $principalId -RoleDefinitionName "Contributor" -Scope $amlWorkspaceResourceId
