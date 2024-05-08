from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta
from custom_operators.custom_functions_kafka import consume_kafka_task, upload_blob_task


default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2023, 1, 1),
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 0,
    'retry_delay': timedelta(minutes=1),
}

dag = DAG(
    'kafka_and_azure_blob_dag',
    default_args=default_args,
    description='DAG for consuming Kafka messages and uploading to Blob Storage',
    schedule_interval=timedelta(minutes=1),
    catchup=False
)

consume_task = PythonOperator(
    task_id='consume_kafka_task',
    python_callable=consume_kafka_task,
    execution_timeout=timedelta(minutes=1),
    dag=dag
)

upload_task = PythonOperator(
    task_id='upload_blob_task',
    python_callable=upload_blob_task,
    execution_timeout=timedelta(minutes=1),
    dag=dag
)

consume_task >> upload_task
