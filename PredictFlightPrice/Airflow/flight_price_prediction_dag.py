from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from datetime import datetime, timedelta

# Define your default arguments
default_args = {
    'owner': 'airflow',
    'depends_on_past': False,
    'start_date': datetime(2024, 8, 19),  
    'email_on_failure': False,
    'email_on_retry': False,
    'retries': 1,
    'retry_delay': timedelta(minutes=5),
}

# Initialize the DAG
dag = DAG(
    'flight_price_prediction_dag',
    default_args=default_args,
    description='A DAG for flight price prediction model pipeline',
    schedule_interval=timedelta(days=1),  
)

# Define your tasks
def load_data():
    # Code to load data
    pass

def preprocess_data():
    # Code to preprocess data
    pass

def train_model():
    # Code to train model
    pass

def make_predictions():
    # Code to make predictions
    pass

# Creating PythonOperator tasks
load_data_task = PythonOperator(
    task_id='load_data',
    python_callable=load_data,
    dag=dag,
)

preprocess_data_task = PythonOperator(
    task_id='preprocess_data',
    python_callable=preprocess_data,
    dag=dag,
)

train_model_task = PythonOperator(
    task_id='train_model',
    python_callable=train_model,
    dag=dag,
)

make_predictions_task = PythonOperator(
    task_id='make_predictions',
    python_callable=make_predictions,
    dag=dag,
)

# Set up task dependencies
load_data_task >> preprocess_data_task >> train_model_task >> make_predictions_task
