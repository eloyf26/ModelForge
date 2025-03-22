# ModelForge AI

AutoML platform that transforms plain-language requirements into production-ready ML models.

## Project Overview
ModelForge AI is an autonomous AutoML platform that transforms plain-language user requirements into production-ready machine learning models. It leverages open-source model libraries, public EU/Spain APIs, and user-provided datasets to automatically perform end-to-end data discovery, cleaning, feature engineering, model selection, training, evaluation, deployment, and monitoring.

### Key Objectives
- Enable non-technical users to build ML models by describing use cases in natural language
- Integrate public data sources (Eurostat, INE, AEMET, AEMPS CIMA, Copernicus, TED, PCSP) and user-uploaded data
- Automate iterative training/fine-tuning until performance thresholds are met
- Provide human-in-the-loop checkpoints for critical validation steps
- Deploy models as REST endpoints with dashboards and drift monitoring

## Project Structure
```
.
├── .github/
│   └── workflows/
│       └── ci.yml
├── modelforge/
│   ├── __init__.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   └── test_main.py
├── .gitignore
├── Dockerfile
├── README.md
└── requirements.txt
```

## Development Setup

1. Clone the repository:
```bash
git clone https://github.com/eloyf26/ModelForge.git
cd ModelForge
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Run tests:
```bash
pytest
```

4. Start development server:
```bash
uvicorn modelforge.main:app --reload
```

The API will be available at:
- API documentation: http://127.0.0.1:8000/docs
- Alternative API docs: http://127.0.0.1:8000/redoc
- Root endpoint: http://127.0.0.1:8000/

## Docker Support

Build and run with Docker:

```bash
docker build -t modelforge .
docker run -p 8000:8000 modelforge
```