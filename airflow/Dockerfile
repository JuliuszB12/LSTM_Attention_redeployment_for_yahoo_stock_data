FROM apache/airflow:2.9.0-python3.10
COPY requirements.txt .
COPY score.py .
RUN pip install --no-cache-dir -r requirements.txt