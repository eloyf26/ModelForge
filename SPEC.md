# ModelForge AI - LangGraph Technical Specification (v1.1, March 2025)

## 1. Project Overview

ModelForge AI is an autonomous AutoML platform that transforms natural language requirements into production-ready machine learning models. The platform works by:

- Converting user's natural language descriptions into structured ML specifications
- Discovering and integrating relevant datasets from public sources and user uploads
- Automating the entire ML pipeline including data processing, model selection, training, and deployment
- Providing human validation checkpoints at critical decision points
- Deploying models with monitoring capabilities and automatic retraining

### Primary Objectives

- Enable non-technical users to create ML models through natural language descriptions
- Integrate data from multiple European and Spanish public APIs (Eurostat, INE, AEMET, etc.)
- Automate iterative training cycles until performance meets requirements
- Include human validation for critical decisions
- Provide production-ready model deployment with monitoring

## 2. System Architecture

The system follows a directed graph workflow with the following main components:

```
IntentParser → ConfirmSpec → DataDiscovery → SelectDatasets → DataIngestion → 
CleanAgent → ConfirmClean → FeatureEngineering → ModelSelection → 
Training → Evaluation → ConfirmEvaluation → Deploy → Monitor → (Retrain Loop)
```

*Note: The Retrain Loop implementation requires further development to specify how it connects back to earlier components in the workflow.*

## 3. Component Definitions

Each node in the system performs a specific function:

| Component | Purpose | Input | Output | Human Validation | Uses MCP |
|-----------|---------|-------|--------|------------------|----------|
| IntentParser | Converts natural language to ML specification | User text | ML spec JSON | No | No |
| ConfirmSpec | Validates ML specification | ML spec | Approved spec | Yes | No |
| DataDiscovery | Finds relevant datasets | Approved spec | Dataset catalog | No | Yes |
| SelectDatasets | User selects which datasets to use | Dataset catalog | Selected datasets | Yes | No |
| DataIngestion | Loads and unifies data | Selected datasets | Raw dataframe | No | Yes |
| CleanAgent | Performs data cleaning | Raw dataframe | Clean dataframe, cleaning report | No | No |
| ConfirmClean | Validates cleaning results | Clean dataframe, report | Approved dataframe | Yes | No |
| FeatureEngineering | Creates features based on spec | Approved dataframe, spec | Feature dataframe | No | No |
| ModelSelection | Selects appropriate model types | Feature dataframe, spec | Model configurations | No | No |
| Training | Trains and tunes models | Model configs, feature data | Trained models, metrics | No | No |
| Evaluation | Evaluates and selects best model | Trained models, metrics | Best model, evaluation report | No | No |
| ConfirmEvaluation | User approves model or requests retraining | Best model, report | Decision | Yes | No |
| Deploy | Creates API endpoint and dashboard | Best model | API URL, dashboard URL | No | No |
| Monitor | Tracks model performance and data drift | API URL | Drift flag, logs | No | No |

*Note: MCP refers to Model Context Protocol, used for standardized communication with model APIs.*

## 4. Data Schemas

### ML Specification Format
```json
{
  "task_type": "time_series_regression",
  "target": "sales",
  "features": ["temp", "unemployment_rate", "sentiment_score"],
  "metric": "rmse",
  "horizon": "3M"
}
```

### Dataset Metadata Format
```json
{
  "name": "Spain Unemployment",
  "source": "INE API",
  "endpoint": "https://servicios.ine.es/...",
  "schema": {"date": "datetime", "value": "float"}
}
```

## 5. External API Integration

| API | Base URL | Authentication | Rate Limit | Format |
|-----|----------|----------------|------------|--------|
| INE | https://servicios.ine.es | None | 100 req/min | JSON |
| AEMET | https://opendata.aemet.es | API key | 60 req/min | JSON |
| Eurostat | https://ec.europa.eu/eurostat/api | None | 500 req/min | JSON/XML |
| Copernicus | https://cds.climate.copernicus.eu | API key | 10 req/min | NetCDF |
| CIMA | https://cima.aemps.es | None | 100 req/min | JSON |

## 6. Deployment Architecture

- Docker containers for each component
- Kubernetes orchestration with CronJobs for monitoring
- FastAPI with Swagger documentation for API endpoints
- Prometheus and Grafana for monitoring and visualization

## 7. Security Implementation

- OAuth2 authentication for user access
- Role-based access control for dataset selection
- Comprehensive audit logging for data lineage tracking

## Implementation Plan
| Phase / Step | Subtasks | Owner | Dependencies | Deliverable(s) | Acceptance Criteria | Risks & Mitigation |
|-------------|----------|-------|--------------|----------------|---------------------|--------------------|
| **Environment Setup** | Install Python 3.12, Docker; configure Git repo and directory structure; create base `requirements.txt`, Dockerfile, CI skeleton | DevOps Engineer | None | Git repo with Docker container builds, CI pipeline configured | Docker image builds and runs; CI pipeline passes lint/tests | Missing dependencies → fallback to pip install; CI failure → notify owner |
| **Intent Parser** | Develop LLM prompt templates; implement JSON‑schema validation; build error handling; write unit tests | ML Engineer | Env Setup | `intent_parser` module + spec validation tests | ≥90% unit test coverage; malformed input yields structured error | Ambiguous spec → log and prompt for clarification |
| **DataDiscovery** | Build API connectors (INE, AEMET, Eurostat); implement Model Context Protocol (MCP) client; metadata catalog model; caching & rate‑limiting | Data Engineer | Intent Parser | `data_discovery` microservice + catalog API | Catalog returns ≥5 datasets for test query; caching TTL enforced | API rate limit → backoff & alert; API schema change → schema validation failure |
| **DataIngestion** | Load JSON/CSV/XML/NetCDF; infer & normalize schema; auto-clean missing/outliers; generate cleaning report | ETL Engineer | DataDiscovery | Raw DataFrame in DuckDB | DataFrame schema matches spec; <5% nulls; report auto-generated | Schema drift → fail ingestion & alert |
| **CleanAgent** | Auto-detect and clean data issues; generate cleaning report; normalize data formats | ETL Engineer | DataIngestion | Cleaned DataFrame + cleaning report | DataFrame passes validation checks; cleaning properly documented | Unresolvable data issues → alert for human intervention |
| **FeatureEngineering** | Auto-generate features per spec; implement selection logic; pipeline for scaling/encoding; feature importance report | Transform Engineer | ConfirmClean | Feature DataFrame + importance report | Feature set passes schema validation; top N features selected | Missing features → notify data engineer |
| **ModelSelection** | Map task type to candidate models; produce hyperparameter configs; baseline performance benchmarks | Model Engineer | Feature DataFrame | Model configs + benchmark results | Config list contains ≥3 candidate models; baseline metrics logged | No viable model → fallback to default configuration |
| **Training** | Train candidates with cross-validation; hyperparameter search via Optuna; log metrics; save model artifacts | ML Engineer | Model Configs | Trained models + metrics dashboard | Each model completes training without errors; metrics > baseline | Overfitting detected → early stopping; resource exhaustion → scale out |
| **Evaluation** | Compare models; generate evaluation report with metrics, confusion matrices, business KPIs | ML Engineer | Trained Models | Evaluation report + selected best model | Best model outperforms baseline and meets business metric thresholds | Poor performance → iterate feature engineering |
| **Human Validation** | Build UI for ConfirmSpec, SelectDatasets, ConfirmClean, ConfirmEvaluation; capture feedback/decisions | Product Manager | Evaluation Report | Validation dashboards + decision logs | Approval decisions recorded; rejection triggers correct rollback | Low adoption → UX refinement |
| **LangGraph Integration** | Compose nodes into LangGraph workflow; configure state management; implement retry, logging, observability | ML Engineer | Validated Components | LangGraph graph spec + logs | Workflow executes end-to-end without errors; retry logic works | Workflow deadlock → alert and manual override |
| **Deploy** | Containerize model API with FastAPI; implement model versioning; secure endpoints; Swagger docs | DevOps Engineer | Best Model | Deployed API URL + Swagger docs | API passes auth tests; swagger reachable; model returns predictions | Deployment failure → rollback to previous version |
| **Monitor** | Implement drift detection; set up Prometheus/Grafana dashboards; auto-trigger retrain; alerting | Monitor Engineer | Deployed API | Monitoring dashboards + alert configs | Drift alerts fire on threshold breach; retrain job schedules correctly | False positives → threshold tuning |
| **Testing & Optimization** | Develop end-to-end test suite; load testing; memory profiling; performance tuning | QA Engineer | Monitor | Test reports + optimized container | All tests pass; latency <100ms; memory <1GB | Performance regression → revert changes |
| **Colab MVP Deployment** | Package code for Colab; write demo notebook; configure ngrok tunnel; document usage | ML Engineer | Testing Report | Colab notebook + ngrok endpoint | Notebook runs from zero with minimal instructions; endpoint responds | Ngrok downtime → fallback URL |
| **Documentation & Handoff** | Write technical docs for each component; API docs; user guides; training slides; limitations/future improvements | Technical Writer | Completed Deployment | Comprehensive documentation set | Documentation covers setup, usage, troubleshooting; peer review complete | Outdated docs → quarterly review schedule | 