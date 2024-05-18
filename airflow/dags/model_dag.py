from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from custom_operators.custom_functions_model import train_model_task, deploy_azureml_task


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=15),
}

dag = DAG(
    'train_and_deploy_model_dag',
    default_args=default_args,
    description='DAG for training model and deploy it to Azure ML Endpoint',
    schedule_interval=timedelta(minutes=15),
    is_paused_upon_creation=False,
    max_active_runs=1,
    catchup=False
)

train_task = PythonOperator(
    task_id='train_model_task',
    python_callable=train_model_task,
    execution_timeout=timedelta(minutes=10),
    provide_context=True,
    dag=dag
)

deploy_task = PythonOperator(
    task_id='deploy_azureml_task',
    python_callable=deploy_azureml_task,
    execution_timeout=timedelta(minutes=55),
    provide_context=True,
    dag=dag
)

train_task >> deploy_task
