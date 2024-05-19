#!/bin/bash

# Assigning parameters to variables
RESOURCE_GROUP=$1
LOCATION=$2
APIM_NAME=$3
FUNCTION_APP_NAME=$4
API_NAME="function"

# Create API Management instance
az apim create \
  --resource-group $RESOURCE_GROUP \
  --name $APIM_NAME \
  --location $LOCATION \
  --publisher-email "randomemail7564231@gmail.com" \
  --publisher-name "Publisher Name"

# Get the function key
FUNCTION_KEY=$(az functionapp function keys list \
  --resource-group $RESOURCE_GROUP \
  --name $FUNCTION_APP_NAME \
  --function-name $API_NAME \
  --query "default" -o tsv)

# Create API in API Management
az apim api create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id $API_NAME \
  --path $API_NAME \
  --display-name $API_NAME \
  --service-url "https://$FUNCTION_APP_NAME.azurewebsites.net/api/$API_NAME" \
  --protocols https

# Create an operation in the API
az apim api operation create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --api-id $API_NAME \
  --operation-id "post-operation" \
  --display-name "Post Operation" \
  --method POST \
  --url-template "/"

# Create a named value in API Management for the function key
az apim nv create \
  --resource-group $RESOURCE_GROUP \
  --service-name $APIM_NAME \
  --named-value-id "function-key" \
  --display-name "FunctionKey" \
  --value $FUNCTION_KEY \
  --secret true
