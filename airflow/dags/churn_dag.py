from airflow import DAG
from airflow.operators.bash import BashOperator
from airflow.operators.python import PythonOperator
from airflow.providers.amazon.aws.sensors.glue import GlueJobSensor
from datetime import datetime
import boto3
import time

# Paths
BASE = "/home/ubuntu/churn_project"
PYTHON = f"{BASE}/python"
DATA = f"{BASE}/data"
VENV_PYTHON = f"{BASE}/venv/bin/python"


# Function to trigger Glue job
def glue_job_s3_redshift_transfer(job_name, **kwargs):
    glue_client = boto3.client('glue', region_name='us-east-1')  # explicit region
    glue_client.start_job_run(JobName=job_name)


# Function to get the latest Glue job run ID
def get_run_id():
    time.sleep(8)
    glue_client = boto3.client('glue', region_name='us-east-1')  # explicit region
    response = glue_client.get_job_runs(JobName="s3_upload_to_redshift_job")
    job_run_id = response["JobRuns"][0]["Id"]
    return job_run_id


with DAG(
    dag_id="churn_pipeline",
    start_date=datetime(2025, 1, 1),
    schedule="@daily",
    catchup=False,
) as dag:

    download_data = BashOperator(
        task_id="download_data",
        bash_command=f"{VENV_PYTHON} {PYTHON}/data_downloading.py"
    )

    copy_data = BashOperator(
        task_id="copy_downloaded_data",
        bash_command=f"""
        CACHE=$(find ~/.cache/kagglehub/datasets/yeanzc/telco-customer-churn-ibm-dataset/versions -maxdepth 1 -mindepth 1 | sort | tail -n 1)
        echo "Using cache directory: $CACHE"
        mkdir -p {DATA}
        cp -r $CACHE/* {DATA}/
        """
    )

    run_chunking = BashOperator(
        task_id="run_chunking",
        bash_command=f"{VENV_PYTHON} {PYTHON}/data_chunks.py"
    )

    upload_to_s3 = BashOperator(
        task_id="upload_to_s3",
        bash_command=f"{VENV_PYTHON} {PYTHON}/upload_chunks.py"
    )

    glue_job_trigger = PythonOperator(
        task_id="glue_job_trigger",
        python_callable=glue_job_s3_redshift_transfer,
        op_kwargs={"job_name": "s3_upload_to_redshift_job"}
    )

    grab_glue_job_id = PythonOperator(
        task_id="grab_glue_job_id",
        python_callable=get_run_id
    )

    is_glue_job_finished = GlueJobSensor(
        task_id="is_glue_job_finished",
        job_name="s3_upload_to_redshift_job",
        run_id='{{ task_instance.xcom_pull("grab_glue_job_id") }}',
        verbose=True,
        aws_conn_id=None,  # will use EC2 IAM role,
        region_name="us-east-1",
        poke_interval=60,
        timeout=3600
    )

    # DAG dependencies
    download_data >> copy_data >> run_chunking >> upload_to_s3 >> glue_job_trigger >> grab_glue_job_id >> is_glue_job_finished
