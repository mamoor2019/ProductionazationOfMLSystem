# Productionization of ML Systems

A comprehensive, production-grade MLOps implementation demonstrating end-to-end machine learning system deployment and management.

## 📚 Documentation

For a detailed writeup covering all MLOps steps, methodologies, and implementations, please refer to:

### **[→ MLOps Comprehensive Writeup](MLOps_Writeup.md)** ⭐

This document covers:
- ✅ Model Development & Experimentation
- ✅ Version Control & Repository Management
- ✅ Testing & Quality Assurance
- ✅ Containerization with Docker
- ✅ CI/CD Pipeline (Jenkins)
- ✅ Workflow Orchestration (Apache Airflow)
- ✅ Experiment Tracking (MLflow)
- ✅ Kubernetes Deployment
- ✅ Production APIs
- ✅ Monitoring & Best Practices

## 🏗️ Project Structure

```
Productionization-of-ML-Systems/
├── GenderClassificationModel/          # Gender classification service
├── PredictFlightPrice/                 # Flight price prediction service
│   ├── Airflow/                        # Apache Airflow orchestration
│   ├── MLflow/                         # MLflow experiment tracking
│   └── tests/                          # Unit & integration tests
├── PredictHotelPrice/                  # Hotel price prediction service
├── Data/                               # Training datasets
└── MLOps_Writeup.md                    # Comprehensive documentation
```

## 🚀 Quick Start

### Prerequisites
- Git, Docker, Kubernetes, Python 3.8+, Jenkins

### Deploy
```bash
# Clone repository
git clone https://github.com/mamoor2019/ProductionazationOfMLSystem.git

# Run tests
cd PredictFlightPrice && pytest

# Build Docker image
docker build -t mamoor/flight-price-pred .

# Deploy to Kubernetes
kubectl apply -f deployment.yml
kubectl apply -f service.yml
```

## 📊 Tech Stack

| Component | Technology |
|-----------|-----------|
| **Version Control** | Git / GitHub |
| **CI/CD** | Jenkins |
| **Containerization** | Docker |
| **Orchestration** | Apache Airflow |
| **Experiment Tracking** | MLflow |
| **Container Orchestration** | Kubernetes |
| **Testing** | pytest |
| **Web Framework** | Flask, Streamlit |
| **ML Libraries** | scikit-learn, XGBoost, Sentence Transformers |

## 📋 Features

✅ **Three Production-Ready ML Services**
- Gender Classification Model
- Flight Price Prediction API
- Hotel Price Prediction UI

✅ **Complete MLOps Pipeline**
- Automated testing and quality checks
- Docker containerization with version control
- Jenkins CI/CD pipeline for automated deployment
- Apache Airflow DAGs for workflow orchestration
- MLflow for experiment tracking and management

✅ **Kubernetes Orchestration**
- High availability with 3 replicas per service
- Load balancing and service discovery
- Resource management and scaling
- Rolling updates and rollbacks

✅ **Production-Ready Features**
- Comprehensive error handling
- Logging and monitoring
- Resource limits and health checks
- Security best practices

## 📈 Architecture

See [MLOps_Writeup.md](MLOps_Writeup.md#4-complete-mlops-workflow-diagram) for detailed architecture diagrams and workflows.

## 🔗 Repository

**GitHub**: https://github.com/mamoor2019/ProductionazationOfMLSystem.git

## 📝 License

This project is part of the AlmaBetter Capstone Program.

---

**For detailed implementation details, API usage, and troubleshooting, see [MLOps_Writeup.md](MLOps_Writeup.md)**