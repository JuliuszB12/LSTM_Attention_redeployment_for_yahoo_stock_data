[![Build Status](https://dev.azure.com/jjuzaszek/LSTM_Attention_redeployment_for_yahoo_stock_data/_apis/build/status%2FJuliuszB12.LSTM_Attention_redeployment_for_yahoo_stock_data?branchName=main)](https://dev.azure.com/jjuzaszek/LSTM_Attention_redeployment_for_yahoo_stock_data/_build/latest?definitionId=20&branchName=main)

## High-level architecture overview
![architecture](https://github.com/JuliuszB12/LSTM_Attention_redeployment_for_yahoo_stock_data/assets/68758875/e71dc045-df45-497d-8fc4-bea09abbfcb2)

## Abstract
Airbyte with yahoo source connector is sending data to Kafka topic at 1-minute intervals about 1-minute prices and volumes of chosen stocks.
At the same time Airflow DAG consuming that data and storing it in Azure blob storage. Every 15 minutes different Airflow DAG fetches updated blob storage data to retrain LSTM Attention machine learning model for predicting next 1-minute stock close price based on previous time-series of prices and calculated technical indicators and log it (with related utils like fitted data scalers) as a next run of experiment to MLflow model registry. After that new version of model is compared on new validation data to model assigned in MLflow with production alias to either retain previous version of model as production version or swap alias and deploy new version of model to Azure ML Studio real-time inference endpoint hosted on Azure Kubernetes cluster. Described operations are executed within peered private networks and all privileges to access different resources are result of system-assigned managed identities of resources from which the code is executed without explicit mentioning of any connection secrets. Predictions of hosted model can be fetched from endpoint through Azure Function behind Azure API Management. Checking the quality of Python code and complete deployment of both infrastructure and containers is fully managed by Azure DevOps CI/CD pipelines within azure-pipelines.yaml file.

Development tech stack: TensorFlow/Keras, Kafka Python Client, Azure Python Client, Azure Resource Manager template, Custom Script Extension, Docker Compose, azure-pipelines.yaml, Bash, PowerShell, Azure CLI

## Step-by-step deployment
1. Go Azure Portal -> Azure DevOps organizations -> My Azure DevOps Organizations -> Create new organization -> New Project
2. Go Project settings -> Service connections -> Create new GitHub and Azure Subscription connections
3. Go Pipelines -> Pipelines -> Create Pipeline -> GitHub -> choose repo with project -> azure-pipelines.yaml in repo will be automatically identified
4. Set Azure Subscription ID and name for new resource group in azure-pipelines.yaml
5. Go Azure Portal -> Subscriptions -> choose subscription -> Access control (IAM) -> Add role assignment -> Privileged administrator roles -> User Access Administrator -> select service principal of Azure DevOps project -> set recommended setting in Conditions tab -> Review + assign
6. Run pipeline and wait for completion (around 45 minutes)
7. Project is operational. API call to ht<span>tps://</span>a1l45&lt;resourceGroupName&gt;.azure-api.net/function/ will success after enough time to collect some data, train and initially deploy the first version of a model (around 45 minutes).


## Features overview
Overview of the features provided by the specific files in the project  
  
**azure-pipelines.yaml**  
&emsp;Continuous Integration and Deployment high-level overview:
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
  - Deploy Virtual Network for Azure Function App
  - Deploy Azure Function App (ARM template)
  - Deploy function and all required packages to Azure Function App (Built-in Azure DevOps Pipeline task)
  - Deploy Private Endpoint from Azure Function App to Azure ML Studio Workspace (ARM template)
  - Deploy private DNS zone to connect Azure Function App to Azure ML Studio Workspace (ARM template)
  - Proceed all required roles assignment between services (Azure PowerShell)
  - Deploy API Management service and API for Azure Function App (Azure CLI)
  - Assign inbound policy to API for Azure Function App (Azure PowerShell)

**airbyte**  
&emsp;- setup.sh - script to deploy Airbyte docker containers and invoke Terraform deployment for establish yahoo -> kafka connection pipeline  
  
**airflow**  
&emsp;- dags/kafka_dag.py - Airflow DAG: extract data from kafka, transform it and upload to Azure Blob Storage  
&emsp;- dags/azure_dag.py - Airflow DAG: extract data from Azure Blob Storage, train new version of machine learning model, fetch production version from MLflow, compare versions, if new version is better swap versions in MLflow and deploy new version to Azure Machine Learning Studio real-time inference endpoint hosted on Azure Kubernetes cluster  
&emsp;- dags/custom_operators/custom_functions_kafka.py - functions for PythonOperator tasks in kafka_dag.py  
&emsp;- dags/custom_operators/custom_functions_azure.py - functions for PythonOperator tasks in azure_dag.py  
&emsp;- Custom dependencies for custom_functions_kafka.py and custom_functions_azure.py:  
&emsp;&emsp;&ensp;dags/custom_operators/azure_utils  
&emsp;&emsp;&ensp;dags/custom_operators/model_utils  
&emsp;&emsp;&ensp;dags/custom_operators/mlflow_utils  
&emsp;- score.py - file executed inside Azure ML Studio real-time inference endpoint during its creation and usage,  
the use of global variables in this file is imposed by Azure documentation  
&emsp;- setup.sh - script to deploy Airflow docker containers  
  
**kafka**  
&emsp;- setup.sh - script to deploy Kafka docker containers, config KAFKA_CFG_AUTO_CREATE_TOPICS_ENABLE=true in docker-compose.yaml allows Airbyte to auto-create all required topics  
  
**mlflow**  
&emsp;- setup.sh - script to deploy MLflow docker containers  
  
**function_api**  
&emsp;- function_app/function/\_\_init\_\_.py - function to fetch model result from Azure ML Studio endpoint  
&emsp;- function_app/function/function.json - configuration file for that function  
&emsp;- function_app/host.json - configuration file for Azure Function App  
&emsp;- apimanagement.sh - Azure CLI bash commands to deploy API Management service and API for Function App  
  
**scripts**  
&emsp;- roles_assignment.ps1 - Roles assignment between Azure services  
  
**arm_templates** - all Azure Resource Manager templates used by azure-pipelines.yaml for Continuous Deployment

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
