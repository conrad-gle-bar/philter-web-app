# Use Python 3.9 slim image
FROM ghcr.io/astral-sh/uv:alpine

# Set working directory
WORKDIR /app

# Copy dependency files
COPY pyproject.toml ./

# Install Python dependencies using uv
RUN uv sync

# Copy application files
COPY main.py ./
COPY download-nltk.py ./
COPY philter.py ./
COPY coordinate_map.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY philter_config/ ./philter_config/
COPY filters/ ./filters/
COPY .env ./

# Download required NLTK data
RUN uv run download-nltk.py

# Expose port
RUN source .env
EXPOSE ${APP_PORT:-8001}

# Run the application
CMD uv run uvicorn main:app --host 0.0.0.0 --port ${APP_PORT:-8001}
