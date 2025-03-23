FROM python:3.12-slim

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

# Accept build argument for OpenAI API key
ARG OPENAI_API_KEY
ARG SUPABASE_DB_URL
ENV OPENAI_API_KEY=$OPENAI_API_KEY
ENV SUPABASE_DB_URL=$SUPABASE_DB_URL

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "modelforge.main:app", "--host", "0.0.0.0", "--port", "8000"]