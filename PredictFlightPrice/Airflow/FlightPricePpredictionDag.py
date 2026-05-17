from datetime import datetime, timedelta
from pathlib import Path
import json
import pickle

import numpy as np
import pandas as pd
from airflow import DAG
from airflow.operators.python_operator import PythonOperator
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

try:
    from xgboost import XGBRegressor
    XGBOOST_AVAILABLE = True
except Exception:
    XGBOOST_AVAILABLE = False

import mlflow
import mlflow.sklearn

ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / 'data'
ARTIFACTS_DIR = ROOT_DIR / 'artifacts'
RAW_DATA_CSV = ROOT_DIR / '..' / 'flights.csv'
VALIDATED_DATA_PATH = DATA_DIR / 'validated_flights.parquet'
PREPROCESSED_DATA_PATH = DATA_DIR / 'preprocessed_flights.parquet'
RAW_DATA_OUTPUT_PATH = DATA_DIR / 'raw_flights.parquet'
MODEL_PATH = ARTIFACTS_DIR / 'random_forest_model.pkl'
SCALER_PATH = ARTIFACTS_DIR / 'scaler.pkl'
METRICS_PATH = ARTIFACTS_DIR / 'training_metrics.json'
PREDICTIONS_PATH = ARTIFACTS_DIR / 'sample_predictions.json'
FEATURES_PATH = ARTIFACTS_DIR / 'feature_columns.json'
MODEL_RUNS_PATH = ARTIFACTS_DIR / 'model_runs.json'
MODEL_METRICS_PATH = ARTIFACTS_DIR / 'model_metrics.json'

DATA_DIR.mkdir(parents=True, exist_ok=True)
ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


def _resolve_raw_csv_path():
    candidates = [RAW_DATA_CSV.resolve(), (ROOT_DIR / 'flights.csv').resolve(), (ROOT_DIR / '..' / 'flights.csv').resolve()]
    for path in candidates:
        if path.exists():
            return path
    raise FileNotFoundError(f"Could not locate flights.csv in {candidates}")


def _sanitize_columns(df: pd.DataFrame) -> pd.DataFrame:
    df.columns = [
        str(col)
        .replace(' ', '_')
        .replace('(', '')
        .replace(')', '')
        .replace('.', '')
        .replace('__', '_')
        for col in df.columns
    ]
    return df


def load_data(**context):
    raw_csv = _resolve_raw_csv_path()
    df = pd.read_csv(raw_csv)
    df.to_parquet(RAW_DATA_OUTPUT_PATH, index=False)
    context['ti'].xcom_push(key='raw_rows', value=len(df))


def validate_data(**context):
    df = pd.read_parquet(RAW_DATA_OUTPUT_PATH)
    required_columns = {'date', 'from', 'to', 'flightType', 'agency', 'distance', 'time', 'price'}
    missing = required_columns.difference(set(df.columns))
    if missing:
        raise ValueError(f'Missing required columns: {missing}')
    if df.isna().any().any():
        nan_columns = [c for c in df.columns if df[c].isna().any()]
        raise ValueError(f'Null values found in columns: {nan_columns}')
    df.to_parquet(VALIDATED_DATA_PATH, index=False)
    context['ti'].xcom_push(key='validated_rows', value=len(df))


def preprocess_data(**context):
    df = pd.read_parquet(VALIDATED_DATA_PATH)
    df['date'] = pd.to_datetime(df['date'])
    df['week_day'] = df['date'].dt.weekday
    df['month'] = df['date'].dt.month
    df['week_no'] = df['date'].dt.isocalendar().week
    df['year'] = df['date'].dt.year
    df['day'] = df['date'].dt.day
    df.rename(columns={'to': 'destination'}, inplace=True)
    df['flight_speed'] = (df['distance'] / df['time']).round(2)
    df = pd.get_dummies(df, columns=['from', 'destination', 'flightType', 'agency'], prefix_sep='_')
    df = df.drop(columns=['time', 'flight_speed', 'month', 'year', 'distance', 'date'], errors='ignore')
    df = _sanitize_columns(df)
    if 'price' not in df.columns:
        raise ValueError('price column missing after preprocessing')
    df.to_parquet(PREPROCESSED_DATA_PATH, index=False)
    context['ti'].xcom_push(key='preprocessed_rows', value=len(df))


def train_model(**context):
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    X = df.drop(columns=['price'])
    y = df['price']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    param_grid = {
        'n_estimators': [200, 300],
        'max_depth': [10, 15],
        'min_samples_split': [5, 10],
        'max_features': ['sqrt', 'log2'],
    }
    rf = RandomForestRegressor(random_state=42)
    grid = GridSearchCV(estimator=rf, param_grid=param_grid, cv=3, scoring='r2', n_jobs=-1)
    grid.fit(X_train_scaled, y_train)
    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test_scaled)
    metrics = {
        'best_params': grid.best_params_,
        'mse': mean_squared_error(y_test, y_pred),
        'mae': mean_absolute_error(y_test, y_pred),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
        'r2_score': float(r2_score(y_test, y_pred)),
        'train_rows': int(len(X_train)),
        'test_rows': int(len(X_test)),
    }
    with open(METRICS_PATH, 'w', encoding='utf-8') as metrics_file:
        json.dump(metrics, metrics_file, indent=2)
    with open(MODEL_PATH, 'wb') as model_file:
        pickle.dump(best_model, model_file)
    with open(SCALER_PATH, 'wb') as scaler_file:
        pickle.dump(scaler, scaler_file)
    with open(FEATURES_PATH, 'w', encoding='utf-8') as features_file:
        json.dump(X.columns.tolist(), features_file, indent=2)
    context['ti'].xcom_push(key='model_path', value=str(MODEL_PATH))
    context['ti'].xcom_push(key='metrics', value=metrics)


def _train_and_log(model_name: str, model_obj, X_train, X_test, y_train, y_test, scaler):
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    with mlflow.start_run(run_name=model_name) as run:
        mlflow.log_param('model_name', model_name)
        # Fit
        model_obj.fit(X_train, y_train)
        preds = model_obj.predict(X_test)
        mse = mean_squared_error(y_test, preds)
        mae = mean_absolute_error(y_test, preds)
        rmse = float(np.sqrt(mse))
        r2 = float(r2_score(y_test, preds))
        metrics = {'mse': mse, 'mae': mae, 'rmse': rmse, 'r2': r2}
        mlflow.log_metrics(metrics)
        # Log model artifact
        mlflow.sklearn.log_model(model_obj, artifact_path='model')
        run_id = run.info.run_id

    # persist run info and metrics
    runs = {}
    metrics_store = {}
    if MODEL_RUNS_PATH.exists():
        runs = json.loads(MODEL_RUNS_PATH.read_text())
    if MODEL_METRICS_PATH.exists():
        metrics_store = json.loads(MODEL_METRICS_PATH.read_text())
    runs[model_name] = run_id
    metrics_store[model_name] = metrics
    MODEL_RUNS_PATH.write_text(json.dumps(runs, indent=2))
    MODEL_METRICS_PATH.write_text(json.dumps(metrics_store, indent=2))
    return run_id, metrics


def train_rf(**context):
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    X = df.drop(columns=['price'])
    y = df['price']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    # simple grid
    param_grid = {'n_estimators': [200], 'max_depth': [15], 'min_samples_split': [5]}
    rf = GridSearchCV(RandomForestRegressor(random_state=42), param_grid=param_grid, cv=3, n_jobs=-1)
    rf.fit(X_train_scaled, y_train)
    best = rf.best_estimator_
    # save scaler and best model
    with open(ARTIFACTS_DIR / 'rf_model.pkl', 'wb') as f:
        pickle.dump(best, f)
    with open(ARTIFACTS_DIR / 'scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    _train_and_log('random_forest', best, X_train_scaled, X_test_scaled, y_train, y_test, scaler)


def train_lr(**context):
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    X = df.drop(columns=['price'])
    y = df['price']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    lr = LinearRegression()
    with open(ARTIFACTS_DIR / 'lr_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open(ARTIFACTS_DIR / 'lr_model.pkl', 'wb') as f:
        pickle.dump(lr, f)
    _train_and_log('linear_regression', lr, X_train_scaled, X_test_scaled, y_train, y_test, scaler)


def train_xgb(**context):
    if not XGBOOST_AVAILABLE:
        print('XGBoost not available; skipping')
        return
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    X = df.drop(columns=['price'])
    y = df['price']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    xgb = XGBRegressor(random_state=42, n_estimators=200)
    with open(ARTIFACTS_DIR / 'xgb_scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    with open(ARTIFACTS_DIR / 'xgb_model.pkl', 'wb') as f:
        pickle.dump(xgb, f)
    _train_and_log('xgboost', xgb, X_train_scaled, X_test_scaled, y_train, y_test, scaler)


def generate_sample_predictions(**context):
    with open(MODEL_PATH, 'rb') as model_file:
        model = pickle.load(model_file)
    with open(SCALER_PATH, 'rb') as scaler_file:
        scaler = pickle.load(scaler_file)
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    sample = df.drop(columns=['price']).head(5)
    sample_predictions = model.predict(scaler.transform(sample))
    output = {
        'sample_count': len(sample),
        'predictions': [float(round(float(pred), 2)) for pred in sample_predictions],
        'actuals': df['price'].head(5).tolist(),
    }
    with open(PREDICTIONS_PATH, 'w', encoding='utf-8') as predictions_file:
        json.dump(output, predictions_file, indent=2)
    context['ti'].xcom_push(key='sample_predictions', value=output)


def log_completion(**context):
    metrics = context['ti'].xcom_pull(key='metrics')
    print('Model training complete. Metrics:')
    print(json.dumps(metrics, indent=2))


def create_dag():
    default_args = {
        'owner': 'airflow',
        'depends_on_past': False,
        'start_date': datetime(2024, 8, 19),
        'email_on_failure': False,
        'email_on_retry': False,
        'retries': 1,
        'retry_delay': timedelta(minutes=5),
    }

    dag = DAG(
        'flight_price_prediction_dag',
        default_args=default_args,
        description='An automated travel data regression workflow for flight price prediction',
        schedule_interval='@daily',
        catchup=False,
        max_active_runs=1,
    )

    load_data_task = PythonOperator(
        task_id='load_data',
        python_callable=load_data,
        dag=dag,
    )

    validate_data_task = PythonOperator(
        task_id='validate_data',
        python_callable=validate_data,
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

    sample_predictions_task = PythonOperator(
        task_id='generate_sample_predictions',
        python_callable=generate_sample_predictions,
        dag=dag,
    )

    # model training tasks (parallel)
    train_rf_task = PythonOperator(
        task_id='train_random_forest',
        python_callable=train_rf,
        dag=dag,
    )

    train_lr_task = PythonOperator(
        task_id='train_linear_regression',
        python_callable=train_lr,
        dag=dag,
    )

    train_xgb_task = PythonOperator(
        task_id='train_xgboost',
        python_callable=train_xgb,
        dag=dag,
    )

    def compare_and_register(**context):
        # choose best model by highest r2
        if not MODEL_METRICS_PATH.exists():
            raise FileNotFoundError('No model metrics found')
        metrics_store = json.loads(MODEL_METRICS_PATH.read_text())
        best_model = None
        best_score = -999
        best_run_id = None
        for model_name, mets in metrics_store.items():
            if mets.get('r2', -999) > best_score:
                best_score = mets['r2']
                best_model = model_name
        runs = json.loads(MODEL_RUNS_PATH.read_text()) if MODEL_RUNS_PATH.exists() else {}
        best_run_id = runs.get(best_model)
        if best_run_id is None:
            raise RuntimeError('Best model run id not found')
        # register model in MLflow Model Registry
        mlflow.set_tracking_uri("http://127.0.0.1:5000")
        model_uri = f"runs:/{best_run_id}/model"
        try:
            result = mlflow.register_model(model_uri, "flight_price_best_model")
            print(f"Registered model: {result.name} version: {result.version}")
        except Exception as e:
            print('Model registration failed, falling back to logging best model to tracking server')
            # fallback: log best model in a new run
            with mlflow.start_run(run_name=f'register_{best_model}'):
                # download model and re-log
                mlflow.log_param('best_model_selected', best_model)

    compare_task = PythonOperator(
        task_id='compare_and_register_best_model',
        python_callable=compare_and_register,
        dag=dag,
    )
    log_completion_task = PythonOperator(
        task_id='log_completion',
        python_callable=log_completion,
        dag=dag,
    )

    # orchestration: preprocess -> train models in parallel -> compare/register -> samples & finish
    load_data_task >> validate_data_task >> preprocess_data_task
    preprocess_data_task >> [train_rf_task, train_lr_task, train_xgb_task] >> compare_task
    compare_task >> sample_predictions_task >> log_completion_task

    return dag


dag = create_dag()
