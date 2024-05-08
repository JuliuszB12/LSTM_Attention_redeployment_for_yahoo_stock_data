#!/bin/bash

set -e

echo "Updating packages..."
sudo apt-get update -y

echo "Installing required packages..."
sudo apt-get install apt-transport-https ca-certificates curl gnupg lsb-release -y

echo "Configuring Docker repository..."
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg

echo "deb [arch=amd64 signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

sudo apt-get update

echo "Installing Docker..."
sudo apt-get install docker-ce docker-ce-cli -y

echo "Adding user to Docker group..."
sudo usermod -a -G docker $USER

echo "Installing Docker Compose..."
sudo apt-get install docker-compose-plugin -y

echo "Creating directories for configuration and logs..."
mkdir -p ./logs ./plugins ./config

echo "Setting up environment variables..."
echo -e "AIRFLOW_UID=$(id -u)" > .env

echo "Initializing Airflow..."
docker compose up airflow-init -- build

echo "Starting Airflow..."
docker compose up --build

echo "Setup complete!"
