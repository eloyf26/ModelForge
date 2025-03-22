# ModelForge AI

[View Technical Specification](SPEC.md)

## Project Structure
```
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── modelforge/
│   ├── __init__.py
│   ├── main.py
│   └── intent_parser.py      # Natural language to ML spec conversion
├── tests/
│   ├── __init__.py
│   ├── test_main.py
│   └── test_intent_parser.py # Intent parser tests
├── .gitignore
├── Dockerfile
├── README.md
├── SPEC.md
└── requirements.txt
```

## Components Implementation Status

### Intent Parser (Completed)
The intent parser module (`modelforge/intent_parser.py`) converts natural language descriptions into structured ML specifications:

- **MLSpecification Schema**
  - Task type validation (time_series_regression, classification, regression, clustering)
  - Required fields validation (target, metric)
  - Special validation for time series tasks (horizon requirement)
  - Pydantic V2 compatible models

- **Features**
  - JSON schema validation
  - Comprehensive error handling
  - Unit test coverage
  - LLM prompt template for natural language parsing

Example usage:
```python
from modelforge.intent_parser import parse_intent

# Convert natural language to ML specification
description = "Predict monthly sales using temperature and unemployment rate data"
spec = parse_intent(description)

# Access structured specification
print(spec.task_type)  # time_series_regression
print(spec.target)     # sales
print(spec.features)   # ["temp", "unemployment_rate", "sentiment_score"]
print(spec.metric)     # rmse
print(spec.horizon)    # 3M
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/eloyf26/ModelForge.git
cd ModelForge
```

2. Set up environment variables:
```bash
# Copy the environment template
cp .env.example .env

# Edit .env with your actual values
# Required: OPENAI_API_KEY for intent parsing
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Run tests:
```bash
pytest
```

5. Start development server:
```bash
uvicorn modelforge.main:app --reload
```

The API will be available at:
- API documentation: http://127.0.0.1:8000/docs
- Alternative API docs: http://127.0.0.1:8000/redoc
- Root endpoint: http://127.0.0.1:8000/

## Environment Variables

The following environment variables are required:

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| OPENAI_API_KEY | OpenAI API key for intent parsing | Yes | None |

## Docker Support

Build and run with Docker:
```bash
# Build with your OpenAI API key
docker build -t modelforge --build-arg OPENAI_API_KEY=your_key_here .
docker run -p 8000:8000 modelforge
```

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