# ModelForge Logging System

ModelForge provides a simple, centralized logging system that can be used throughout the application.

## Basic Usage

```python
from modelforge.logger import get_logger

# Create a logger for your module
logger = get_logger(__name__)

# Use the logger
logger.debug("Debug message")
logger.info("Info message")
logger.warning("Warning message")
logger.error("Error message")
logger.critical("Critical message")
```

## Configuration

By default, logs are written to both the console and a file at `logs/modelforge.log` with a log level of `DEBUG`.

You can adjust the log level by setting the environment variable `MODELFORGE_LOG_LEVEL` to one of:
- `DEBUG` (default)
- `INFO` 
- `WARNING`
- `ERROR`
- `CRITICAL`

Example:
```bash
# Set log level to INFO
export MODELFORGE_LOG_LEVEL=INFO

# Run your application
python -m modelforge.main
```

## Using the Default App Logger

For simple scripts or quick usage, you can use the pre-configured application logger:

```python
from modelforge import app_logger

app_logger.info("Using the app-wide logger")
```

## Custom Configuration

You can create a logger with custom configuration:

```python
from modelforge.logger import get_logger

# Custom logger with different log file
my_logger = get_logger(
    name="custom_module",
    level="INFO",
    log_file="logs/custom.log"
)

# Or disable file logging entirely
console_only_logger = get_logger(
    name="console_only",
    log_file=None
)
```

## Installing ModelForge in Development Mode

To install ModelForge in development mode:

```bash
# Clone the repository
git clone https://github.com/your-org/modelforge.git
cd modelforge

# Install in development mode
pip install -e .

# Install with development dependencies
pip install -e ".[dev]"
``` 