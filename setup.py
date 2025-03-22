from setuptools import setup, find_packages

setup(
    name="modelforge",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "fastapi>=0.100.0",
        "uvicorn>=0.20.0",
        "pydantic>=2.0.0",
        "python-dotenv>=0.19.0",
        "openai>=1.0.0",
        "aiohttp>=3.8.0",
    ],
    python_requires=">=3.8",
) 