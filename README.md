# Philter Web App

Web interface for the Philter PHI (Protected Health Information) filtering tool for clinical notes.

## Features

- **Web Interface**: Simple HTMX-powered form for uploading text files or pasting clinical notes
- **API Endpoint**: Direct curl-accessible API for programmatic access
- **Multiple Output Formats**: Download filtered results as TXT, XML, or JSON
- **Frequency Table**: Optional generation of PHI frequency statistics
- **No Storage**: All processing done in-memory, results not persisted
- **Important Disclaimer**: Outputs PHI-reduced notes, not PHI-free notes

## Quick Start with Docker (Recommended)

The easiest way to run Philter Web App is using Docker:

### Prerequisites
- Docker
- Docker Compose

### Running the Application

1. **Build and start the container:**
```bash
docker-compose up -d
```

2. **Access the application:**
   - Web interface: http://localhost:8000
   - API endpoint: http://localhost:8000/api/philter

3. **View logs:**
```bash
docker-compose logs -f philter-web
```

4. **Stop the application:**
```bash
docker-compose down
```

### Rebuilding After Changes

If you modify the code, rebuild the container:
```bash
docker-compose up -d --build
```

## Manual Installation (Alternative)

If you prefer not to use Docker:

### Prerequisites
- Python 3.9-3.11
- uv or pip

### Installation

1. Install dependencies using uv:
```bash
uv pip install -e .
```

Or with standard pip:
```bash
pip install -e .
```

2. Activate the virtual environment:
```bash
source .venv39/Scripts/activate  # Windows
source .venv39/bin/activate      # Linux/Mac
```

3. Start the server:
```bash
python main.py
```

The application will be available at: http://localhost:8000

## Usage

### Web Interface

1. Navigate to http://localhost:8000
2. Either:
   - Paste clinical text into the textarea, OR
   - Upload a text file (max 10MB)
3. Optionally check "Generate frequency table"
4. Click "Process Text"
5. View filtered results and download in your preferred format

### API Usage (curl)

Process text directly:

```bash
curl -X POST http://localhost:8000/api/philter \
  -F "text=Patient John Doe was seen on 01/01/2023" \
  -F "freq_table=false"
```

Process a file:

```bash
curl -X POST http://localhost:8000/api/philter \
  -F "file=@clinical_note.txt" \
  -F "freq_table=true"
```

Response format:
```json
{
  "success": true,
  "filtered_text": "Patient **** *** was seen on **********",
  "xml_output": "<xml>...</xml>",
  "freq_table": {...}
}
```

## Configuration

The application uses the `philter_delta.json` configuration from the philter-ucsf project. This is pre-configured and hidden from users.

Settings:
- **Max file size**: 10MB
- **Output format**: Production mode (i2b2 XML with PHI tags)
- **Config file**: `philter_config/philter_delta.json`

## Deployment

### Docker Deployment

The application includes a multi-stage Dockerfile optimized for production:

- Based on Python 3.9 slim image
- Includes all required dependencies
- Pre-downloads NLTK data
- Health checks configured
- Runs on port 8000

### Environment Variables

None required by default. All configuration is pre-set.

## Project Structure

```
philter-web-app/
├── Dockerfile              # Docker container definition
├── docker-compose.yml      # Docker Compose configuration
├── main.py                 # FastAPI application
├── templates/
│   ├── index.html         # Main page
│   └── results.html       # Results partial
├── static/
│   └── style.css          # Styling
├── philter_config/
│   └── philter_delta.json # Philter configuration
└── pyproject.toml         # Dependencies
```

## Citation

If you use this software for any publication, please cite:

Norgeot, B., Muenzen, K., Peterson, T.A. et al. Protected Health Information filter (Philter): accurately and securely de-identifying free-text clinical notes. npj Digit. Med. 3, 57 (2020). https://doi.org/10.1038/s41746-020-0258-y

## License

See the philter-ucsf project for licensing information.
