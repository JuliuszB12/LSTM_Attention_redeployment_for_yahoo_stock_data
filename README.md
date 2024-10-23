[![Build Status](https://dev.azure.com/jjuzaszek/LSTM_Attention_redeployment_for_yahoo_stock_data/_apis/build/status%2FJuliuszB12.LSTM_Attention_redeployment_for_yahoo_stock_data?branchName=main)](https://dev.azure.com/jjuzaszek/LSTM_Attention_redeployment_for_yahoo_stock_data/_build/latest?definitionId=20&branchName=main)

## High-level architecture overview
![architecture](https://github.com/JuliuszB12/LSTM_Attention_redeployment_for_yahoo_stock_data/assets/68758875/e71dc045-df45-497d-8fc4-bea09abbfcb2)

## Abstract
Airbyte with yahoo source connector is sending data to Kafka topic at 1-minute intervals about 1-minute prices and volumes of chosen stocks.
At the same time Airflow DAG consuming that data and storing it in Azure blob storage. Every 15 minutes different Airflow DAG fetches updated blob storage data to retrain LSTM Attention machine learning model for predicting next 1-minute stock close price based on previous time-series of prices and calculated technical indicators and log it (with related utils like fitted data scalers) as a next run of experiment to MLflow model registry. After that new version of model is compared on new validation data to model assigned in MLflow with production alias to either retain previous version of model as production version or swap alias and deploy new version of model to Azure ML Studio real-time inference endpoint hosted on Azure Kubernetes cluster. Described operations are executed within peered private networks and all privileges to access different resources are result of system-assigned managed identities of resources from which the code is executed without explicit mentioning of any connection secrets. Predictions of hosted model can be fetched from endpoint through Azure Function behind Azure API Management. Checking the quality of Python code and complete deployment of both infrastructure and containers is fully managed by Azure DevOps CI/CD pipelines within azure-pipelines.yaml file.

Development tech stack: TensorFlow/Keras, Kafka Python Client, Azure Python Client, Azure Resource Manager template, Custom Script Extension, Docker Compose, azure-pipelines.yaml, Bash, PowerShell, Azure CLI

## Step-by-step deployment
1. Go Azure Portal -> Azure DevOps organizations -> My Azure DevOps Organizations -> Create new organization -> New Project
2. Go Project settings -> Service connections -> Create new GitHub and Azure Subscription connections (select "Azure Resource Manager" connection type)
3. Go Pipelines -> Pipelines -> Create Pipeline -> GitHub -> choose repo with project -> azure-pipelines.yaml in repo will be automatically identified
4. Set Azure Subscription ID and name for new resource group in azure-pipelines.yaml
5. Go Azure Portal -> Subscriptions -> choose subscription -> Access control (IAM) -> Add role assignment -> Privileged administrator roles -> User Access Administrator -> select service principal of Azure DevOps project -> set recommended setting in Conditions tab -> Review + assign
6. Run pipeline and wait for completion (around 50 minutes)
7. Project is operational. API call to ht<span>tps://</span>&lt;resourceGroupName&gt;a1l45.azure-api.net/function/ for model inference will succeed after enough time to collect some data, train and initially deploy the first version of a model (around 45 minutes). To make proper API call follow function_api/example_api_call/example_api_call.py
  
&emsp;NOTE:  
&emsp;Minimal requirements of the compute quotas allowed on chosen Azure subscription  
&emsp;to successfully deploy the project with default settings:  
&emsp;&ensp;Poland Central Standard Dv2 Family vCPUs 12  
&emsp;&ensp;Poland Central Standard Ev4 Family vCPUs 8  
&emsp;&ensp;Poland Central Total Regional vCPUs 20  
&emsp;Estimated cost for default project settings : 2$ per hour

## Content overview
Overview of the files in the repository  
  
**azure-pipelines.yaml** - set of CI/CD instructions for Azure DevOps Pipelines to deploy the entire project from scratch to an operational state  
  
**airbyte**
  - setup.sh - script to deploy Airbyte docker containers and invoke Bash script to establish yahoo -> kafka connection pipeline  
  - connection_setup.sh - script to establish yahoo -> kafka connection pipeline in Airbyte  
  
**airflow**
  - dags/kafka_dag.py - Airflow DAG: extract data from kafka, transform it and upload to Azure Blob Storage  
  - dags/model_dag.py - Airflow DAG: extract data from Azure Blob Storage, train new version of machine learning model, fetch production version from MLflow, compare versions, if new version is better swap versions in MLflow and deploy new version to Azure Machine Learning Studio real-time inference endpoint hosted on Azure Kubernetes cluster  
  - dags/custom_operators/custom_functions_kafka.py - functions for PythonOperator tasks in kafka_dag.py  
  - dags/custom_operators/custom_functions_model.py - functions for PythonOperator tasks in azure_dag.py  
  - Custom dependencies for custom_functions_kafka.py and custom_functions_model.py:  
  &emsp;dags/custom_operators/azure_utils  
  &emsp;dags/custom_operators/model_utils  
  &emsp;dags/custom_operators/mlflow_utils  
  - score.py - file executed inside Azure ML Studio real-time inference endpoint during its creation and usage,  
the use of global variables in this file is imposed by Azure documentation  
  - setup.sh - script to deploy Airflow docker containers  
  
**kafka**
  - setup.sh - script to deploy Kafka docker containers  
  
**mlflow**
  - setup.sh - script to deploy MLflow docker containers  
  
**function_api**
  - function_app/function/\_\_init\_\_.py - function to fetch model result from Azure ML Studio endpoint  
  - function_app/function/function.json - configuration file for that function  
  - function_app/host.json - configuration file for Azure Function App  
  - apimanagement.sh - Azure CLI bash commands to deploy API Management service and API for Function App  
  - example_api_call/example_api_call.py - example post request with test data to the ready API after successful deployment  
  
**scripts**
  - roles_assignment.ps1 - Roles assignment between Azure services  
  
**arm_templates**  
&emsp;All Azure Resource Manager templates serving as Infrastructure as Code used by Azure DevOps Pipelines for Continuous Deployment  
  - airbyte_infra_template.json - Azure Virtual Machine as Airbyte host with dependencies (Azure Virtual Network, Azure Disk Storage, Azure Network Interface and Security Group) and Custom Script Extension that invokes Bash script airbyte/setup.sh on Linux  
  - airflow_infra_template.json - Azure Virtual Machine as Airflow host with dependencies (Azure Virtual Network, Azure Disk Storage, Azure Network Interface and Security Group) and Custom Script Extension that invokes Bash script airflow/setup.sh on Linux  
  - kafka_infra_template.json - Azure Virtual Machine as Kafka host with dependencies (Azure Virtual Network, Azure Disk Storage, Azure Network Interface and Security Group) and Custom Script Extension that invokes Bash script kafka/setup.sh on Linux  
  - mlflow_infra_template.json - Azure Virtual Machine as MLflow host with dependencies (Azure Virtual Network, Azure Disk Storage, Azure Network Interface and Security Group) and Custom Script Extension that invokes Bash script mlflow/setup.sh on Linux  
  - airflow_mlstudio_private_endpoint_template.json - Private endpoint from Airflow host Virtual Network to Azure Machine Learing Studio  
  - airflow_storage_private_endpoint_template.json - Private endpoint from Airflow host Virtual Network to Azure Blob Storage  
  - azureml_private_link_template.json - Private DNS Zone for Azure Machine Learning Studio with necessary DNS records  
  - blob_storage_private_link_template.json - Private DNS Zone for Azure Blob Storage with necessary DNS records  
  - blob_storage_template.json - Azure Blob Storage  
  - temp_blob_storage_template.json - Azure Blob Storage for deployment utilities  
  - azureml_template.json - Azure Machine Learning Studio  
  - function_app_template.json - Azure Function App  
  - functionapp_vnet_template.json - Outbound Virtual Network for Azure Function App  
  - function_azureml_private_endpoint_template.json - Private endpoint from Azure Function App outbound Virtual Network to Azure Machine Learing Studio  
  - function_azureml_private_link_template.json - Private DNS Zone for Azure Machine Learning Studio with necessary DNS records for Azure Function App  
  - vnet_peering_template.json - Virtual Network Peering

## Infrastructure overview
**Azure Virtual Machine**: Provides scalable, on-demand computing resources for running applications and workloads in the cloud.  
**Azure Virtual Network**: Enables secure, isolated, and logically segmented network environments within the Azure cloud.  
**Azure VNet Peering**: Allows seamless, low-latency connectivity between two Azure Virtual Networks.  
**Azure Blob Storage Account**: Offers scalable object storage for unstructured data such as documents, media files, and backups.  
**Azure Machine Learning Studio Workspace**: Provides a collaborative environment for data scientists to build, train, and deploy machine learning models.  
**Azure Function App**: Enables serverless computing by allowing the execution of event-driven functions without managing infrastructure.  
**Azure API Management**: Facilitates the creation, management, and security of APIs at scale.  
**Azure Private Endpoint**: Provides a secure connection to Azure services through a private link, ensuring data remains on the private network.  
**System-assigned Managed Identity**: Automatically manages credentials for accessing Azure services, providing secure identity and access management for applications.  
**Airbyte**: An open-source data integration platform for extracting, transforming, and loading data from various sources.  
**Kafka**: A distributed streaming platform used for building real-time data pipelines and streaming applications, enabling low-latency data transmission and processing.  
**Airflow**: An open-source workflow management platform for scheduling and monitoring complex data pipelines.  
**MLflow**: An open-source platform for managing the machine learning lifecycle, including experimentation, reproducibility, and deployment.  
**Azure Machine Learning real-time inference endpoint on Azure Kubernetes cluster**: Deploys machine learning models to provide real-time predictions via scalable Kubernetes clusters in Azure.

## Features overview
Overview of the project functionalities  
  
**Continuous Integration and Deployment via Azure DevOps Pipelines**  
&emsp;Set of CI/CD instructions is defined within azure-pipelines.yaml. Every time new commit or merge is made to desired repo branch, Azure Pipeline looks for that file in repository and execute it in the context of Azure subscription and newly created Azure Resource Group which are set as parameters. Azure Pipelines App integrated with GitHub repository informs about state of the execution in the details of assigned commit. CI/CD instructions are executed sequentially due to free-tier Azure Pipelines limitations. Order of high-level CI/CD instructions with corresponding tool used:
  - Assign Azure Subscription ID and new resource group name
  - Check the quality of Python code with flake8, isort, mypy, black and pylint (Bash)
  - Pack Azure Function App project and other services utils for deployment (Bash)
  - Dynamically resolve worldwide unique names for services like Azure Blob Storage, Function App or API Management (PowerShell)
  - Deploy temporary Azure Blob Storage for deployment utils (ARM template)
  - Send airbyte, kafka, airflow and mlflow packed content folders to temporary storage (Bash)
  - Deploy Azure ML Studio Workspace and dependencies (ARM template)
  - Deploy Azure Blob Storage for keeping stock prices data (ARM template)
  - Deploy Kafka with its infrastructure (ARM template + Custom Script Extension)
  - Deploy Airbyte with its infrastructure (ARM template + Custom Script Extension) and establish yahoo -> kafka connection pipeline (Bash)
  - Deploy MLflow with its infrastructure (ARM template + Custom Script Extension)
  - Deploy Airflow with its infrastructure (ARM template + Custom Script Extension) and start DAGs
  - Deploy VNet Peering between Virtual Networks for Airbyte and Kafka infra (ARM template)
  - Deploy VNet Peering between Virtual Networks for Kafka and Airflow infra (ARM template)
  - Deploy VNet Peering between Virtual Networks for Aiflow and MLflow infra (ARM template)
  - Deploy Private Endpoint to Azure Blob Storage from Virtual Network for Airflow infra (ARM template)
  - Deploy Private Endpoint to Azure ML Studio Workspace from Virtual Network for Airflow infra (ARM template)
  - Deploy private DNS zone required to connect Airflow infra to Azure Blob Storage (ARM template)
  - Deploy private DNS zone required to connect Airflow infra to Azure ML Studio Workspace (ARM template)
  - Deploy Virtual Network for Azure Function App (ARM template)
  - Deploy Azure Function App (ARM template)
  - Deploy function and all required packages to Azure Function App (Built-in Azure DevOps Pipeline task)
  - Deploy Private Endpoint from Azure Function App to Azure ML Studio Workspace (ARM template)
  - Deploy private DNS zone to connect Azure Function App to Azure ML Studio Workspace (ARM template)
  - Proceed all required roles assignment between services (Azure PowerShell)
  - Deploy API Management service and API for Azure Function App (Azure CLI)
  - Assign inbound policy to API for Azure Function App (Azure PowerShell)
  
**Airbyte data extraction and loading to Kafka**  
&emsp;Airbyte is a tool for data integration between various systems with exisiting Airbyte built-in connectors.
The idea is to choose pre-defined source and destination with proper dedicated configuration and connect them together within Airbyte connection.
The chosen source for this project is Yahoo finance service with real-time stock data. With Kafka set as destination and with proper scheduler configuration, Airbyte can serve a similar role to Kafka Connect, but with less development effort. The configuration for source, destination and connection is specified within airbyte/connection_setup.sh and includes all the necessary dedicated configuration for Yahoo data as well as for Kafka producer and topic. The list of desired stock indexes can be set in "tickers" parameter for Bash "source_id" variable. Although Airbyte call to Yahoo API cannot be made with smaller granularity of "interval" parameter than 1 day, that can be overcome because the raw data from API response contains continuously updated timestamps and stock data with 1 minute granularity and it just requires more complicated post-processing to obtain it (done as part of Airflow DAG consuming that data from Kafka topic). Unprocessed data is sent to Kafka topic via private Azure network. Environement variable KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE=true in Bitnami Kafka docker-compose.yaml allows Airbyte to auto-create all required Kafka topics.  
  
**Airflow ETL from Kafka to Azure Blob Storage**  
&emsp;Airflow DAG "kafka_and_azure_blob_dag" specified within airflow/dags/kafka_dag.py extract raw Airbyte data from Kafka, transform it and load it to Azure Blob Storage Container. The reason for using Kafka instead of ingesting Airbyte data directly within Airflow DAG is the need for asynchronous architecture design due to unpredictable Airbyte and Yahoo behaviour that can result in failure and retry, and to avoid holding Airflow task for processing latest available data. Airflow PythonOperator task "consume_kafka_task" performs data processing in order to obtain desired state of last 1 minute stock data. The final result has structure of Pandas DataFrame with explicitly specified schema that can be read direclty in airflow/dags/custom_operators/custom_functions_kafka.py inside function "consume_kafka_task". DataFrame saved to .pkl format is then uploaded by next Airflow task to Azure Blob Storage as an object with the naming convention {ticker}/yyyy/mm/dd/HH/MM/file_name.pkl to allow efficient querying by ticker and date, and to display data in Azure Portal with folder-oriented structure. Airflow can reach Azure Blob Storage via private Azure network using Private Endpoint and System-Assigned Managed Identity that provides RBAC role to write data to Azure Blob Storage Container and is assigned to Airflow host.  
  
**Airflow LSTM Attention model training**  
&emsp;Airflow DAG "train_and_deploy_model_dag" specified within airflow/dags/model_dag.py extract data from Azure Blob Storage, prepare it for machine learning model training, train the model, compare it to current production version of model on new validation data and possibly decides to deploy it to Azure Machine Learning real-time inference endpoint hosted on Azure Kubernetes cluster. LSTM model is implemented with TensorFlow/Keras framework and with explicit implementation of Attention layer. Training process done by Airflow task "train_model_task" is every time registered as MLflow experiment to log all training statistics, model artifacts and utilities like fitted data scalers and to keep model versions registry. MLflow has system of aliases that allows for specific model versions marking that differentiate them in terms of current utility. Best model version that is currently deployed to production has appropriate alias and is used to assess new model versions.  
  
**Airflow LSTM Attention model deployment**  
&emsp;If new model version beats production model, it takes the production alias and is deployed to Azure inference endpoint by Airflow task "deploy_azureml_task" of Airflow DAG "train_and_deploy_model_dag". Behaviour of model in Azure inference endpoint is determined by airflow/score.py that is prepared according to Azure documentation guidelines. Two functions "init" and "run" from score.py are executed when model is deployed and invoked accordingly. Azure documentation imposes usage of global variables in this file to share them between deploying and invoking functions. Model artifact itself can actually be one of this variables, so all utilities concerning it are initialized during deployment and then used during invoking. Azure allows for creating Python conda environment for score.py execution, which allows to handle model artifact that came from MLflow using dedicated MLflow framework inside Azure inference endpoint. Airflow can reach Azure Machine Learning Studio via private Azure network using Private Endpoint and System-Assigned Managed Identity that provides RBAC role to upload model to Azure registry as well as to create endpoint and deploy model to it.  
  
**API to request model result**  
&emsp;To ensure proper endpoint usage tracking and management, it is not directly accessible for public users and can be reached only through dedicated API. This API is built with Python function deployed via Azure Function App as backend and with Azure API Management as frontend. The function is supposed to handle user request, connect to Azure Machine Learning Studio, request model result from real-time model inference endpoint and return response status to user, possibly with model result data if response status is ok. It is implemented within Azure Function App because of small scope of function task and its frequent but irregular use, which makes serverless computing infrastructure the right choice for the host. Function within Azure Function App can reach Azure Machine Learning Studio via private Azure network using Private Endpoint and System-Assigned Managed Identity that provides RBAC role to access inference endpoint. As Private Endpoint to Azure Machine Learning Studio requires Azure Virtual Network from which it is established and Azure Function App by default operates without it, thus it is required to connect Azure Function App to Azure Virtual Network that is supposed to serve as source network for outbound connections from Azure Function App. Managed Identity, together with custom Azure subscription ID and Azure Resouce Group name as function environment variables delivered from Azure DevOps Pipelines, allow for seamless implicit secure connectivity to Azure Machine Learning Studio and reusability of the project code for different releases and Azure accounts. The similar approach is used in other parts of the project. Function within Azure Function App is reachable through Azure API Management endpoint. Inbound policy is used for request made to Azure API to appropriately forward it to Azure Function App and Azure API Management Named values are used for secrets management.
