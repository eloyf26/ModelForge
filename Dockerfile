FROM python:3.12-slim AS base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Accept build arguments for API keys and other secrets
ARG OPENAI_API_KEY
ARG SUPABASE_URL
ARG SUPABASE_KEY
ARG INE_API_KEY
ARG AEMET_API_KEY
ARG EUROSTAT_API_KEY

# Set environment variables from build args
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV SUPABASE_URL=$SUPABASE_URL
ENV SUPABASE_KEY=$SUPABASE_KEY
ENV INE_API_KEY=$INE_API_KEY
ENV AEMET_API_KEY=$AEMET_API_KEY
ENV EUROSTAT_API_KEY=$EUROSTAT_API_KEY

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt requirements-dev.txt ./

# Install dependencies (including dev dependencies for testing)
RUN pip install --no-cache-dir -r requirements.txt && \
    pip install --no-cache-dir -r requirements-dev.txt

# Copy project files
COPY . .

# Make run_tests.sh executable
RUN chmod +x run_tests.sh

# Expose port
EXPOSE 8000

# Default command - run the application
CMD ["uvicorn", "modelforge.main:app", "--host", "0.0.0.0", "--port", "8000"]

# Test stage for running tests
FROM base AS test
CMD ["./run_tests.sh"]