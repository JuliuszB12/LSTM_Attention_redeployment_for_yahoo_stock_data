$subscriptionId = "38ca6696-5c82-4571-b2af-bf3f256cf663"
$resourceGroupName = "rocket_test_trial"
$vmName = "airflow"
$storageAccountName = "kafkastockdata1"
$vm = Get-AzVM -ResourceGroupName $resourceGroupName -Name $vmName
$storageAccount = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
$storageAccountResourceId = $storageAccount.Id
New-AzRoleAssignment -ObjectId $vm.Identity.PrincipalId -RoleDefinitionName "Contributor" -Scope $storageAccountResourceId
$vmName = "airflow"
$storageAccountName = "kafkastockdata1"
$vm = Get-AzVM -ResourceGroupName $resourceGroupName -Name $vmName
$storageAccount = Get-AzStorageAccount -ResourceGroupName $resourceGroupName -Name $storageAccountName
$storageAccountResourceId = $storageAccount.Id
New-AzRoleAssignment -ObjectId $vm.Identity.PrincipalId -RoleDefinitionName "Storage Blob Data Contributor" -Scope $storageAccountResourceId
$vmName = "airflow"
$amlWorkspaceName = "mlserving"
$vm = Get-AzVM -ResourceGroupName $resourceGroupName -Name $vmName
$amlWorkspace = Get-AzResource -ResourceGroupName $resourceGroupName -ResourceType "Microsoft.MachineLearningServices/workspaces" -Name $amlWorkspaceName
$amlWorkspaceResourceId = $amlWorkspace.ResourceId
 New-AzRoleAssignment -ObjectId $vm.Identity.PrincipalId -RoleDefinitionName "Contributor" -Scope $amlWorkspaceResourceId
