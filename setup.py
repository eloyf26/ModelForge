from setuptools import setup, find_packages

setup(
    name="modelforge",
    version="1.0.0",
    description="AutoML platform that transforms plain-language requirements into production-ready ML models",
    author="ModelForge Team",
    packages=find_packages(),
    python_requires=">=3.8",
    install_requires=[
        "fastapi>=0.104.0",
        "pydantic>=2.0.0",
        "openai>=1.0.0",
        "tenacity>=8.0.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "black>=23.0.0",
            "isort>=5.0.0",
            "mypy>=1.0.0",
            "uvicorn>=0.23.0",
        ]
    },
) 