import sys
import os
import pandas as pd
import subprocess
from datetime import datetime
from airflow import DAG
from airflow.operators.python import PythonOperator

# 加入 scripts 資料夾路徑
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../../scripts')))

# 匯入自定義函數
from extract import fetch_exchange_rates
from transform import transform_exchange_data
from load import load_to_postgresql

# --- 任務函數區 ---

def extract_and_push(**context):
    df = fetch_exchange_rates()
    json_str = df.to_json()
    context["ti"].xcom_push(key="extracted_data", value=json_str)

def transform_and_push(**context):
    json_str = context["ti"].xcom_pull(task_ids="extract_exchange_rates", key="extracted_data")
    if json_str is None:
        raise ValueError("extract_and_push 沒有成功推送資料！")
    df = pd.read_json(json_str)
    df_transformed = transform_exchange_data(df)
    context["ti"].xcom_push(key="transformed_data", value=df_transformed.to_json())

def load_from_transformed(**context):
    json_str = context["ti"].xcom_pull(task_ids="transform_exchange_data", key="transformed_data")
    if json_str is None:
        raise ValueError("transform_and_push 沒有成功推送資料！")
    df = pd.read_json(json_str)
    load_to_postgresql(df)

def run_spark_analysis():
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
    script_path = os.path.join(project_root, 'spark_jobs', 'spark_analysis.py')
    result = subprocess.run(["python", script_path], capture_output=True, text=True)
    print(result.stdout)
    if result.returncode != 0:
        print(result.stderr)
        raise RuntimeError("spark_analysis.py 執行失敗")

# --- DAG 區 ---

with DAG(
    dag_id="currency_etl_dag",
    start_date=datetime(2024, 1, 1),
    schedule=None,  # "0 8 * * *": 每天早上 8:00
    catchup=False,
    tags=["exchange", "daily"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract_exchange_rates",
        python_callable=extract_and_push,
    )

    transform_task = PythonOperator(
        task_id="transform_exchange_data",
        python_callable=transform_and_push,
    )

    load_task = PythonOperator(
        task_id="load_to_postgresql",
        python_callable=load_from_transformed,
    )

    spark_analysis_task = PythonOperator(
        task_id="run_spark_analysis",
        python_callable=run_spark_analysis,
    )

    extract_task >> transform_task >> load_task >> spark_analysis_task
