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
COPY philter.py ./
COPY coordinate_map.py ./
COPY templates/ ./templates/
COPY static/ ./static/
COPY philter_config/ ./philter_config/
COPY filters/ ./filters/

# Download required NLTK data
RUN . /opt/venv/bin/activate && python -c "import nltk; \
    nltk.download('punkt', quiet=True); \
    nltk.download('averaged_perceptron_tagger', quiet=True); \
    nltk.download('averaged_perceptron_tagger_eng', quiet=True); \
    nltk.download('maxent_ne_chunker', quiet=True); \
    nltk.download('words', quiet=True); \
    nltk.download('wordnet', quiet=True); \
    nltk.download('omw-1.4', quiet=True)"

# Expose port
EXPOSE 8000

# Run the application
CMD ["uv", "run","uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
