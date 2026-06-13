# FlightPricePredictionDag.py - Complete Explanation

## Overview
**FlightPricePredictionDag.py** is an Apache Airflow DAG (Directed Acyclic Graph) that automates the complete machine learning pipeline for flight price prediction. It runs daily, orchestrating data ingestion, validation, preprocessing, model training, comparison, and deployment.

---

## 1. WHAT IS THIS DAG?

### Purpose
Automatically retrain flight price prediction models on a daily schedule with:
- Data quality validation
- Feature engineering
- Hyperparameter tuning
- Model comparison (Random Forest vs Linear Regression)
- Best model registration in MLflow Model Registry
- Sample predictions generation

### Execution Schedule
- **Frequency:** Daily (`@daily`)
- **Start Date:** August 19, 2024
- **Max Active Runs:** 1 (prevents parallel executions)
- **Retries:** 1 attempt per task on failure
- **Retry Delay:** 5 minutes

---

## 2. IMPORTS & DEPENDENCIES

```python
from datetime import datetime, timedelta          # Scheduling
from pathlib import Path                          # File paths
import json, pickle                               # Data serialization
import numpy as np, pandas as pd                  # Data processing
from airflow import DAG                           # Workflow orchestration
from airflow.operators.python_operator import PythonOperator  # Execute Python code
from sklearn.ensemble import RandomForestRegressor # Model 1
from sklearn.linear_model import LinearRegression  # Model 2
from sklearn.model_selection import GridSearchCV   # Hyperparameter tuning
from sklearn.preprocessing import StandardScaler   # Feature scaling
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score  # Evaluation
import mlflow, mlflow.sklearn                     # Model tracking & registry
```

### Key Technology Stack
- **Airflow:** Workflow orchestration
- **MLflow:** Model versioning & registry
- **Scikit-learn:** ML algorithms
- **Pandas:** Data manipulation
- **GridSearchCV:** Automated hyperparameter optimization

---

## 3. CONFIGURATION & PATHS

### Directory Structure
```python
ROOT_DIR = Airflow/                    # DAG root
DATA_DIR = Airflow/data/               # Input/intermediate data
ARTIFACTS_DIR = Airflow/artifacts/     # Models & metrics output

# Input data
RAW_DATA_CSV = flights.csv             # Source data

# Processing stages (Parquet format for efficiency)
RAW_DATA_OUTPUT_PATH = raw_flights.parquet
VALIDATED_DATA_PATH = validated_flights.parquet
PREPROCESSED_DATA_PATH = preprocessed_flights.parquet

# Model artifacts
MODEL_PATH = random_forest_model.pkl
SCALER_PATH = scaler.pkl
FEATURES_PATH = feature_columns.json
METRICS_PATH = training_metrics.json
PREDICTIONS_PATH = sample_predictions.json
MODEL_RUNS_PATH = model_runs.json (MLflow tracking)
MODEL_METRICS_PATH = model_metrics.json (Comparison)
```

### Helper Functions

#### 1. `_resolve_raw_csv_path()`
Finds flights.csv in multiple possible locations:
```
Priority 1: ROOT_DIR/data/flights.csv
Priority 2: ROOT_DIR/data/flights.csv
Priority 3: ROOT_DIR/Airflow/dags/flights.csv
Error: Raises FileNotFoundError if not found
```
**Why?** Handles different deployment configurations and path inconsistencies.

#### 2. `_sanitize_columns(df)`
Cleans column names by:
- Replacing spaces with underscores
- Removing parentheses, dots
- Removing double underscores
```python
Example: "Price (USD)" → "Price_USD"
```
**Why?** SQL and downstream systems often require valid identifiers.

---

## 4. DAG TASKS (8 Total)

### Task 1: Load Data

```python
def load_data(**context):
    raw_csv = _resolve_raw_csv_path()
    df = pd.read_csv(raw_csv)
    df.to_parquet(RAW_DATA_OUTPUT_PATH, index=False)
    context['ti'].xcom_push(key='raw_rows', value=len(df))
```

**What it does:**
1. Locates flights.csv
2. Reads CSV into pandas DataFrame
3. Converts to Parquet format (faster I/O, more efficient)
4. Pushes row count to XCom (cross-task communication)

**Output:** `raw_flights.parquet` + metadata (row count)

**XCom Usage:** Passes `raw_rows` count to downstream tasks

---

### Task 2: Validate Data

```python
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
```

**What it does:**
1. Reads raw data from Parquet
2. Checks if all required 8 columns exist:
   - date, from, to, flightType, agency, distance, time, price
3. Checks for NULL/missing values
4. Raises error if validation fails (stops pipeline)
5. Saves validated data to Parquet

**Failure Scenarios:**
- Missing required columns → Task fails, pipeline stops
- NULL values present → Task fails, pipeline stops

**Output:** `validated_flights.parquet`

---

### Task 3: Preprocess Data

```python
def preprocess_data(**context):
    df = pd.read_parquet(VALIDATED_DATA_PATH)
    
    # Date feature engineering
    df['date'] = pd.to_datetime(df['date'])
    df['week_day'] = df['date'].dt.weekday        # 0-6 (Monday-Sunday)
    df['month'] = df['date'].dt.month             # 1-12
    df['week_no'] = df['date'].dt.isocalendar().week  # 1-53
    df['year'] = df['date'].dt.year               # 2024, 2025, etc.
    df['day'] = df['date'].dt.day                 # 1-31
    
    # Distance feature engineering
    df.rename(columns={'to': 'destination'}, inplace=True)
    df['flight_speed'] = (df['distance'] / df['time']).round(2)  # km/h
    
    # One-hot encoding for categorical columns
    df = pd.get_dummies(df, columns=['from', 'destination', 'flightType', 'agency'], prefix_sep='_')
    # Result: from_New_York, from_London, destination_Paris, etc.
    
    # Drop unnecessary columns
    df = df.drop(columns=['time', 'flight_speed', 'month', 'year', 'distance', 'date'], errors='ignore')
    
    # Sanitize column names
    df = _sanitize_columns(df)
    
    # Verify price column exists (model target)
    if 'price' not in df.columns:
        raise ValueError('price column missing after preprocessing')
    
    df.to_parquet(PREPROCESSED_DATA_PATH, index=False)
    context['ti'].xcom_push(key='preprocessed_rows', value=len(df))
```

**Feature Engineering Performed:**

| Feature | Type | Derivation | Purpose |
|---------|------|-----------|---------|
| week_day | Categorical | date.weekday() | Day patterns (weekends vs weekdays) |
| month | Categorical | date.month | Seasonal patterns |
| week_no | Categorical | date.isocalendar().week | Holiday/high-season detection |
| year | Categorical | date.year | Yearly trends |
| day | Categorical | date.day | Monthly patterns |
| flight_speed | Continuous | distance/time | Aircraft efficiency |
| from_* | Binary (one-hot) | Departure city | Route origin |
| destination_* | Binary (one-hot) | Arrival city | Route destination |
| flightType_* | Binary (one-hot) | Direct/Connecting | Flight type |
| agency_* | Binary (one-hot) | Booking provider | Supplier effect |

**Output:** 
- `preprocessed_flights.parquet` with ~40-50 features (depends on unique categorical values)
- Removed raw features: time, distance, date (already encoded)
- Ready for model training

---

### Task 4: Train Model (Initial)

```python
def train_model(**context):
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    X = df.drop(columns=['price'])  # Features
    y = df['price']                 # Target
    
    # Split into train/test (80/20)
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    
    # Scale features
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Hyperparameter grid
    param_grid = {
        'n_estimators': [200, 300],      # Number of trees
        'max_depth': [10, 15],           # Tree depth limit
        'min_samples_split': [5, 10],    # Min samples per split
        'max_features': ['sqrt', 'log2'], # Features per split
    }
    
    # Grid search with 3-fold cross-validation
    rf = RandomForestRegressor(random_state=42)
    grid = GridSearchCV(estimator=rf, param_grid=param_grid, cv=3, scoring='r2', n_jobs=-1)
    grid.fit(X_train_scaled, y_train)
    
    # Get best model
    best_model = grid.best_estimator_
    y_pred = best_model.predict(X_test_scaled)
    
    # Calculate metrics
    metrics = {
        'best_params': grid.best_params_,
        'mse': mean_squared_error(y_test, y_pred),
        'mae': mean_absolute_error(y_test, y_pred),
        'rmse': float(np.sqrt(mean_squared_error(y_test, y_pred))),
        'r2_score': float(r2_score(y_test, y_pred)),
        'train_rows': int(len(X_train)),
        'test_rows': int(len(X_test)),
    }
    
    # Save artifacts
    with open(METRICS_PATH, 'w') as f:
        json.dump(metrics, f, indent=2)
    with open(MODEL_PATH, 'wb') as f:
        pickle.dump(best_model, f)
    with open(SCALER_PATH, 'wb') as f:
        pickle.dump(scaler, f)
    with open(FEATURES_PATH, 'w') as f:
        json.dump(X.columns.tolist(), f, indent=2)
    
    # Push to XCom
    context['ti'].xcom_push(key='model_path', value=str(MODEL_PATH))
    context['ti'].xcom_push(key='metrics', value=metrics)
```

**What it does:**
1. Prepares X (features) and y (target = price)
2. Splits 80% train / 20% test
3. Scales features with StandardScaler
4. Performs GridSearchCV to find best hyperparameters (12 combinations × 3 folds = 36 fits)
5. Evaluates on test set
6. Saves model, scaler, features list

**Output Metrics:**
```json
{
  "best_params": {
    "n_estimators": 300,
    "max_depth": 15,
    "min_samples_split": 5,
    "max_features": "sqrt"
  },
  "mse": 45000,
  "mae": 150,
  "rmse": 212.13,
  "r2_score": 0.87,
  "train_rows": 800,
  "test_rows": 200
}
```

**Artifacts Saved:**
- `random_forest_model.pkl` - Serialized model
- `scaler.pkl` - Feature scaler
- `training_metrics.json` - Metrics
- `feature_columns.json` - Feature names

---

### Task 5: Train Random Forest (Parallel)

```python
def train_rf(**context):
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    X = df.drop(columns=['price'])
    y = df['price']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    # Simpler grid for faster execution
    param_grid = {'n_estimators': [200], 'max_depth': [15], 'min_samples_split': [5]}
    rf = GridSearchCV(RandomForestRegressor(random_state=42), param_grid=param_grid, cv=3, n_jobs=-1)
    rf.fit(X_train_scaled, y_train)
    best = rf.best_estimator_
    
    # Save locally
    with open(ARTIFACTS_DIR / 'rf_model.pkl', 'wb') as f:
        pickle.dump(best, f)
    with open(ARTIFACTS_DIR / 'scaler.pkl', 'wb') as f:
        pickle.dump(scaler, f)
    
    # Log to MLflow
    _train_and_log('random_forest', best, X_train_scaled, X_test_scaled, y_train, y_test, scaler)
```

**What it does:**
- Trains Random Forest with simplified grid search
- Logs metrics to MLflow (http://127.0.0.1:5000)
- Runs in parallel with Task 6 (Linear Regression)

**MLflow Integration:**
- Creates run with name: "random_forest"
- Logs parameters, metrics, model artifact
- Stores run_id in MODEL_RUNS_PATH

---

### Task 6: Train Linear Regression (Parallel)

```python
def train_lr(**context):
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    X = df.drop(columns=['price'])
    y = df['price']
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.20, random_state=42)
    
    scaler = StandardScaler()
    X_train_scaled = scaler.fit_transform(X_train)
    X_test_scaled = scaler.transform(X_test)
    
    lr = LinearRegression()
    # No hyperparameter tuning (Linear Regression has few hyperparams)
    # Just fit and log
    _train_and_log('linear_regression', lr, X_train_scaled, X_test_scaled, y_train, y_test, scaler)
```

**What it does:**
- Trains Linear Regression model
- Logs to MLflow with same structure
- Provides baseline comparison (simpler but potentially less accurate)

**Note:** Tasks 5 & 6 run simultaneously (parallel execution)

---

### Task 7: Compare & Register Best Model

```python
def compare_and_register(**context):
    # Read metrics from both models
    metrics_store = json.loads(MODEL_METRICS_PATH.read_text())
    
    # Find highest R² score
    best_model = None
    best_score = -999
    best_run_id = None
    for model_name, mets in metrics_store.items():
        if mets.get('r2', -999) > best_score:
            best_score = mets['r2']
            best_model = model_name
    
    # Get MLflow run ID
    runs = json.loads(MODEL_RUNS_PATH.read_text())
    best_run_id = runs.get(best_model)
    
    # Register in MLflow Model Registry
    mlflow.set_tracking_uri("http://127.0.0.1:5000")
    model_uri = f"runs:/{best_run_id}/model"
    try:
        result = mlflow.register_model(model_uri, "flight_price_best_model")
        print(f"Registered model: {result.name} version: {result.version}")
    except Exception as e:
        print('Model registration failed, falling back...')
        with mlflow.start_run(run_name=f'register_{best_model}'):
            mlflow.log_param('best_model_selected', best_model)
```

**What it does:**
1. Compares R² scores from Random Forest and Linear Regression
2. Selects model with highest R²
3. Registers best model in MLflow Model Registry
4. Assigns version number for deployment tracking

**Selection Logic:**
```
Random Forest R²: 0.87
Linear Regression R²: 0.82
→ Random Forest wins (0.87 > 0.82)
→ Registered as "flight_price_best_model" v1
```

---

### Task 8: Generate Sample Predictions

```python
def generate_sample_predictions(**context):
    # Load trained model & scaler
    with open(MODEL_PATH, 'rb') as model_file:
        model = pickle.load(model_file)
    with open(SCALER_PATH, 'rb') as scaler_file:
        scaler = pickle.load(scaler_file)
    
    # Get first 5 rows from preprocessed data
    df = pd.read_parquet(PREPROCESSED_DATA_PATH)
    sample = df.drop(columns=['price']).head(5)
    
    # Generate predictions
    sample_predictions = model.predict(scaler.transform(sample))
    
    # Output format
    output = {
        'sample_count': len(sample),
        'predictions': [float(round(float(pred), 2)) for pred in sample_predictions],
        'actuals': df['price'].head(5).tolist(),
    }
    
    # Save & push to XCom
    with open(PREDICTIONS_PATH, 'w') as predictions_file:
        json.dump(output, predictions_file, indent=2)
    context['ti'].xcom_push(key='sample_predictions', value=output)
```

**Output Example:**
```json
{
  "sample_count": 5,
  "predictions": [150.25, 200.50, 175.75, 220.00, 190.30],
  "actuals": [145.00, 210.00, 180.00, 215.00, 195.00]
}
```

**Purpose:**
- Quick sanity check: Do predictions look reasonable?
- Stored for pipeline reporting/monitoring

---

### Task 9: Log Completion

```python
def log_completion(**context):
    metrics = context['ti'].xcom_pull(key='metrics')
    print('Model training complete. Metrics:')
    print(json.dumps(metrics, indent=2))
```

**What it does:**
- Retrieves final metrics from XCom
- Logs to Airflow log files
- Final status indicator

---

## 5. TASK ORCHESTRATION & DEPENDENCIES

### DAG Structure

```
load_data
    ↓
validate_data
    ↓
preprocess_data
    ├────────────────────────────┐
    ↓                            ↓
train_random_forest      train_linear_regression
    └────────────────────────────┘
            ↓
    compare_and_register
            ↓
    generate_sample_predictions
            ↓
    log_completion
```

### Dependency Code
```python
# Sequential: load → validate → preprocess
load_data_task >> validate_data_task >> preprocess_data_task

# Parallel: RF and LR train simultaneously
preprocess_data_task >> [train_rf_task, train_lr_task] >> compare_task

# Sequential: compare → sample predictions → completion
compare_task >> sample_predictions_task >> log_completion_task
```

### Execution Timeline
```
Time  |  Task 1  |  Task 2  |  Task 3  |  Task 5 | Task 6 |  Task 7  |  Task 8  |  Task 9
------|----------|----------|----------|---------|--------|----------|----------|----------
T0    |  load    |          |          |         |        |          |          |
T1    |          |validate  |          |         |        |          |          |
T2    |          |          | preprocess|         |        |          |          |
T3    |          |          |          |   RF    |   LR   |          |          |
T4    |          |          |          |  (train)|  (train)|         |          |
T5    |          |          |          |         |        | compare  |          |
T6    |          |          |          |         |        |          | samples  |
T7    |          |          |          |         |        |          |          | log
```

---

## 6. MLflow INTEGRATION

### What is MLflow?
MLflow is an open-source ML experiment tracking and model registry platform.

### How it's Used Here

#### 1. Experiment Tracking
```python
mlflow.set_tracking_uri("http://127.0.0.1:5000")
with mlflow.start_run(run_name="random_forest") as run:
    mlflow.log_param('model_name', 'random_forest')
    mlflow.log_metrics({'r2': 0.87, 'rmse': 212.13})
    mlflow.sklearn.log_model(best_model, artifact_path='model')
```

**Tracks:**
- Model type & hyperparameters
- Performance metrics
- Model binary artifacts
- Run timestamps & duration

#### 2. Model Registry
```python
model_uri = f"runs:/{best_run_id}/model"
result = mlflow.register_model(model_uri, "flight_price_best_model")
# Creates: "flight_price_best_model" v1, v2, v3, ...
```

**Benefits:**
- Version history of all trained models
- Easy rollback to previous version
- Production deployment tracking

### MLflow UI Access
- **URL:** http://127.0.0.1:5000
- **View:** All experiments, runs, metrics, models
- **Action:** Download best model, compare runs, register for production

---

## 7. ERROR HANDLING & RECOVERY

### Validation Errors (Stop Pipeline)
```python
# If columns missing
if missing:
    raise ValueError(f'Missing required columns: {missing}')
    ↓ Task fails → Entire pipeline stops
    ↓ Airflow alerts (if configured)
    ↓ Retries after 5 minutes

# If nulls found
if df.isna().any().any():
    raise ValueError(f'Null values found in columns: {nan_columns}')
    ↓ Same flow as above
```

### Retries
```python
'retries': 1,              # Try once more if failed
'retry_delay': timedelta(minutes=5)  # Wait 5 mins, then retry
```

### Model Registration Fallback
```python
try:
    result = mlflow.register_model(model_uri, "flight_price_best_model")
except Exception as e:
    # If registry fails, still log the model
    with mlflow.start_run(run_name=f'register_{best_model}'):
        mlflow.log_param('best_model_selected', best_model)
```

---

## 8. DATA FLOW SUMMARY

```
flights.csv (raw)
    ↓
[Load] → raw_flights.parquet
    ↓
[Validate] → Check schema & nulls
    ↓
validated_flights.parquet
    ↓
[Preprocess]
├─ Engineer: week_day, month, flight_speed, etc.
├─ Encode: One-hot for cities, flight types
├─ Scale: StandardScaler
└─ 40-50 features total
    ↓
preprocessed_flights.parquet
    ↓
[Train Models] (Parallel)
├─ Random Forest (GridSearchCV)
├─ Linear Regression (baseline)
└─ Compare by R² score
    ↓
[Register] Best Model → MLflow Registry
    ↓
[Predict] Sample predictions
    ↓
sample_predictions.json
```

---

## 9. PRODUCTION USAGE

### How to Trigger Manually
```bash
# Access Airflow UI
http://localhost:8080/

# Navigate to: DAGs → flight_price_prediction_dag
# Click: Trigger DAG
# Or via CLI:
airflow dags trigger flight_price_prediction_dag
```

### How to Access Results
```bash
# Model artifacts
ls Airflow/artifacts/
├── random_forest_model.pkl
├── scaler.pkl
├── training_metrics.json
├── sample_predictions.json
├── feature_columns.json
└── model_metrics.json

# MLflow Registry
http://127.0.0.1:5000/models
# View: flight_price_best_model v1, v2, v3...

# Deploy best model
mlflow.pyfunc.load_model("models:/flight_price_best_model/Production")
```

---

## 10. KEY FEATURES & ADVANTAGES

| Feature | Benefit |
|---------|---------|
| **Automated Scheduling** | Retrains models daily without manual intervention |
| **Data Validation** | Catches issues early (missing columns, nulls) |
| **Feature Engineering** | Extracts temporal & categorical patterns |
| **Hyperparameter Tuning** | GridSearchCV finds optimal parameters automatically |
| **Model Comparison** | Objectively picks best model (Random Forest vs Linear Reg) |
| **MLflow Integration** | Tracks experiments, enables model versioning & registry |
| **Parallel Execution** | RF & LR train simultaneously (faster) |
| **Error Recovery** | Automatic retries on failure |
| **Artifact Persistence** | All models, scalers, metrics saved for reproducibility |
| **XCom Communication** | Tasks share data efficiently |

---

## 11. MONITORING & LOGGING

### Airflow Logs Location
```
~/.airflow/logs/flight_price_prediction_dag/
├── load_data/
├── validate_data/
├── preprocess_data/
├── train_random_forest/
├── train_linear_regression/
├── compare_and_register_best_model/
├── generate_sample_predictions/
└── log_completion/
```

### Key Metrics to Monitor
- **Task Duration:** How long each task takes
- **Success Rate:** % of runs that complete without errors
- **Model Metrics:** R², RMSE, MAE trends over time
- **Data Volume:** Row counts before/after validation
- **Best Model Selection:** Which model wins each day?

---

## 12. TROUBLESHOOTING

| Issue | Cause | Solution |
|-------|-------|----------|
| **Validation fails** | Missing columns or nulls in data | Check flights.csv schema |
| **Model training slow** | Large dataset or slow GridSearchCV | Reduce param_grid size |
| **MLflow registration fails** | MLflow server down | Check http://127.0.0.1:5000 |
| **FileNotFoundError** | flights.csv not found | Verify file paths in config |
| **Out of memory** | Dataset too large | Reduce batch size or sample data |

---

## 13. CONCLUSION

**FlightPricePredictionDag.py** is a production-grade ML pipeline that:

✅ **Automates** daily model retraining
✅ **Validates** data quality before training
✅ **Engineers** features for better predictions
✅ **Compares** multiple algorithms objectively
✅ **Tracks** experiments with MLflow
✅ **Manages** model versions for deployment
✅ **Handles** errors gracefully with retries
✅ **Orchestrates** complex workflows with Airflow

This DAG embodies **MLOps best practices**: reproducibility, automation, monitoring, and continuous improvement through daily model updates.
