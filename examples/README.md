# ModelForge AI Examples

This folder contains example scripts demonstrating the usage of ModelForge AI components.

## Available Examples

### workflow_example.py
A complete workflow demonstration that:
1. Takes a natural language description of an ML task
2. Parses it into a structured ML specification
3. Uses the specification to search for relevant datasets
4. Fetches actual data for analysis

## Running the Examples

1. Make sure you have set up your environment as described in the main README:
   ```bash
   # From the project root
   cp .env.example .env
   # Edit .env and add your OPENAI_API_KEY
   pip install -r requirements.txt
   ```

2. Run the workflow example:
   ```bash
   # From the project root
   python examples/workflow_example.py
   ```

## Expected Output

The workflow example will:
1. Parse the input: "Predict Spain's inflation rate for the next 3 months using economic indicators"
2. Show the structured ML specification
3. Search for relevant datasets in the INE API
4. Display dataset metadata and schema
5. Fetch and show actual data points

Example output:
```
Starting ModelForge AI Workflow Example...
----------------------------------------
1. Starting Intent Parsing...

Input description: Predict Spain's inflation rate for the next 3 months using economic indicators

Parsed ML Specification:
Task Type: time_series_regression
Target: inflation_rate
Features: ['economic_indicators']
Metric: rmse
Horizon: 3M

2. Starting Data Discovery...
[...] 