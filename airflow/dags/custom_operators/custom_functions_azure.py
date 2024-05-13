import joblib
from datetime import datetime
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_squared_error, mean_absolute_error
import mlflow
import mlflow.tensorflow
from mlflow.models import infer_signature
from azureml.core import Model, Environment
from azureml.core.model import InferenceConfig
from azureml.core.webservice import AksWebservice
from azureml.core.compute import AksCompute, ComputeTarget
from azureml.core.conda_dependencies import CondaDependencies
from .azure_utils import tickers, read_blob, auth_ws_register_model, container_data
from .model_utils import preprocess_data, build_model, model_name
from .mlflow_utils import compare_and_update_production_stage


def train_model_task() -> str:
    """
    Airflow task\n
    Train new version of model, log it to mlflow model registry with new run of experiment,\n
    | compare with model currently assigned to production and change assignment if new version is better
    """
    mlflow.set_tracking_uri("http://10.4.0.4:5000")
    mlflow.set_experiment(model_name)
    mlflow.set_tag("mlflow.runName", f"{datetime.now()}".replace(' ', 'T'))
    unit_number = 50

    model = build_model((32, 12), unit_number)
    x, y, scaler, y_scaler = preprocess_data(32, read_blob, tickers, container_data)
    x_train, x_val, y_train, y_val = train_test_split(x, y, test_size=0.2, random_state=42)
    history = model.fit(x_train, y_train, epochs=30, batch_size=16, validation_data=(x_val, y_val))

    plt.figure(figsize=(10, 5))
    plt.plot(history.history['loss'], label='Train Loss')
    plt.plot(history.history['val_loss'], label='Validation Loss')
    plt.title('Model Loss Over Epochs')
    plt.ylabel('Loss')
    plt.xlabel('Epoch')
    plt.legend(loc='upper right')
    plt.savefig("loss_plot.png")

    predictions = model.predict(x_val)

    signature = infer_signature(x_val, predictions)
    mlflow.tensorflow.log_model(
        model,
        artifact_path="tfmodel",
        signature=signature,
        registered_model_name=model_name
    )

    mse = mean_squared_error(y_val, predictions)
    mae = mean_absolute_error(y_val, predictions)
    joblib.dump(scaler, "scaler.joblib")
    joblib.dump(y_scaler, "y_scaler.joblib")
    mlflow.log_param("unit_number", unit_number)
    mlflow.log_metric("Mean Squared Error", mse)
    mlflow.log_metric("Mean Absolute Error", mae)
    mlflow.log_artifact("loss_plot.png")
    mlflow.log_artifact("scaler.joblib")
    mlflow.log_artifact("y_scaler.joblib")

    return compare_and_update_production_stage(model_name, mse, x_val, y_val)


def deploy_azureml_task(**kwargs) -> None:
    """
    Airflow task\n
    | Deploy mlflow production version of trained model to Azure ML real-time inference endpoint using AKS\n
    Invoke only if new version is set to production in train_model_task
    """
    ti = kwargs['ti']
    controller = ti.xcom_pull(task_ids='train_model_task')
    if controller == 'old_version':
        pass
    elif controller == 'new_model':
        # Auth to Azure ML Workspace and register production version of trained model
        ws, model = auth_ws_register_model(model_name)

        # Create conda environment for score.py
        env = Environment('my-env')
        cd = CondaDependencies.create(pip_packages=['mlflow==2.12.1', 'azureml-defaults', 'numpy==1.23.5', 
                                                    'scikit-learn==1.4.2', 'tensorflow==2.15.1'],
                                      python_version='3.10')
        env.python.conda_dependencies = cd

        # Create an inference configuration
        inference_config = InferenceConfig(entry_script='score.py', environment=env)

        # Create if not exists and set AKS deployment configuration
        deployment_config = AksWebservice.deploy_configuration(cpu_cores=1, memory_gb=1)
        try:
            aks_target = ws.compute_targets['lstm-aks-cluster']
        except:
            prov_config = AksCompute.provisioning_configuration(location='polandcentral')
            aks_target = ComputeTarget.create(workspace=ws, name='lstm-aks-cluster', provisioning_configuration=prov_config)
            aks_target.wait_for_completion(show_output=True)

        # Deploy model to AKS target
        service = Model.deploy(workspace=ws,
                               name='lstm-service',
                               models=[model],
                               inference_config=inference_config,
                               deployment_config=deployment_config,
                               deployment_target=aks_target)
        service.wait_for_deployment(show_output=True)
    elif controller == 'new_version':
        # Auth to Azure ML Workspace and register production version of trained model
        ws, model = auth_ws_register_model(model_name)

        # Create conda environment for score.py
        env = Environment('my-env')
        cd = CondaDependencies.create(pip_packages=['mlflow==2.12.1', 'azureml-defaults', 'numpy==1.23.5', 
                                                    'scikit-learn==1.4.2', 'tensorflow==2.15.1'],
                                      python_version='3.10')
        env.python.conda_dependencies = cd

        # Create an inference configuration
        inference_config = InferenceConfig(entry_script='score.py', environment=env)

        # set AKS deployment configuration
        deployment_config = AksWebservice.deploy_configuration(cpu_cores=1, memory_gb=1)
        aks_target = ws.compute_targets['lstm-aks-cluster']

        # Deploy model to AKS target
        service = Model.deploy(workspace=ws,
                               name='lstm-service',
                               models=[model],
                               inference_config=inference_config,
                               deployment_config=deployment_config,
                               deployment_target=aks_target,
                               overwrite=True)
        service.wait_for_deployment(show_output=True)
    else:
        raise Exception("train_model_task return error")
