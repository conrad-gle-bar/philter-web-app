import os
import tempfile
import json
import uuid
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, Request, Form, UploadFile, File, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from philter import Philter

app = FastAPI(title="Philter Web App", description="Web interface for PHI filtering")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Setup templates
templates = Jinja2Templates(directory="templates")

# Configuration
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
CONFIG_PATH = "philter_config/philter_delta.json"

# In-memory storage for processed results (session_id -> results)
results_store = {}


def process_with_philter(text: str, freq_table: bool = False) -> dict:
    """
    Process text with Philter and return results.

    Returns:
        dict with keys: filtered_text, xml_output, freq_table_data (if requested)
    """
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Create input and output directories
        input_dir = temp_path / "input"
        output_dir = temp_path / "output"
        input_dir.mkdir()
        output_dir.mkdir()

        # Write input text to file
        input_file = input_dir / "input.txt"
        input_file.write_text(text, encoding='utf-8')

        # Configure Philter
        philter_config = {
            "verbose": False,
            "run_eval": False,
            "freq_table": freq_table,
            "finpath": str(input_dir),
            "foutpath": str(output_dir),
            "outformat": "i2b2",  # XML format for production
            "filters": CONFIG_PATH,
            "prod": True,
            "cachepos": None
        }

        # Run Philter
        filterer = Philter(philter_config)
        filterer.map_coordinates()
        filterer.transform()

        # Read results - philter outputs as .xml in i2b2 format
        output_file = output_dir / "input.xml"

        if not output_file.exists():
            # Try .txt as fallback
            output_file = output_dir / "input.txt"
            if not output_file.exists():
                raise Exception("Philter processing failed - no output file generated")

        # For i2b2 format, the output is XML
        xml_output = output_file.read_text(encoding='utf-8')

        # Extract filtered text from XML and replace PHI with asterisks
        import re
        import xml.etree.ElementTree as ET

        try:
            root = ET.fromstring(xml_output)
            text_elem = root.find('.//TEXT')
            if text_elem is not None and text_elem.text:
                original_text = text_elem.text
            else:
                raise Exception("TEXT element not found or empty in XML")

            tags = root.findall('.//TAGS/*')

            # Create list of (start, end) tuples for PHI locations
            phi_locations = [(int(tag.get('start')), int(tag.get('end'))) for tag in tags]
            phi_locations.sort()

            # Build filtered text by replacing PHI spans with asterisks
            filtered_text = ""
            last_end = 0
            for start, end in phi_locations:
                filtered_text += original_text[last_end:start]
                filtered_text += '*' * (end - start)
                last_end = end
            filtered_text += original_text[last_end:]

        except Exception as e:
            # Fallback to simple extraction if XML parsing fails
            filtered_text = re.sub(r'<[^>]+>', '', xml_output)

        results = {
            "filtered_text": filtered_text,
            "xml_output": xml_output,
            "original_text": text
        }

        # Handle frequency table if requested
        if freq_table:
            freq_table_file = output_dir / "freq_table.json"
            if freq_table_file.exists():
                results["freq_table_data"] = json.loads(freq_table_file.read_text())
            else:
                results["freq_table_data"] = None

        return results


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main page."""
    return templates.TemplateResponse("index.html", {"request": request})


@app.post("/process", response_class=HTMLResponse)
async def process_text(
    request: Request,
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    freq_table: bool = Form(False)
):
    """
    Process text via HTMX form submission.
    Returns HTML partial for results display.
    """
    try:
        # Validate input
        if not text and not file:
            return templates.TemplateResponse(
                "results.html",
                {"request": request, "error": "Please provide text or upload a file"}
            )

        # Get text content
        if file:
            # Check file size
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                return templates.TemplateResponse(
                    "results.html",
                    {"request": request, "error": f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit"}
                )
            text = content.decode('utf-8')

        if not text or not text.strip():
            return templates.TemplateResponse(
                "results.html",
                {"request": request, "error": "Text content is empty"}
            )

        # Process with Philter
        results = process_with_philter(text, freq_table)

        # Generate session ID for downloads
        session_id = str(uuid.uuid4())
        results_store[session_id] = results

        return templates.TemplateResponse(
            "results.html",
            {
                "request": request,
                "filtered_text": results["filtered_text"],
                "session_id": session_id,
                "has_freq_table": freq_table and results.get("freq_table_data")
            }
        )

    except Exception as e:
        return templates.TemplateResponse(
            "results.html",
            {"request": request, "error": f"Processing error: {str(e)}"}
        )


@app.post("/api/philter")
async def api_philter(
    text: Optional[str] = Form(None),
    file: Optional[UploadFile] = File(None),
    freq_table: bool = Form(False)
):
    """
    API endpoint for direct curl access.
    Returns JSON response.
    """
    try:
        # Validate input
        if not text and not file:
            raise HTTPException(status_code=400, detail="Please provide text or upload a file")

        # Get text content
        if file:
            content = await file.read()
            if len(content) > MAX_FILE_SIZE:
                raise HTTPException(
                    status_code=400,
                    detail=f"File size exceeds {MAX_FILE_SIZE / 1024 / 1024}MB limit"
                )
            text = content.decode('utf-8')

        if not text or not text.strip():
            raise HTTPException(status_code=400, detail="Text content is empty")

        # Process with Philter
        results = process_with_philter(text, freq_table)

        return JSONResponse({
            "success": True,
            "filtered_text": results["filtered_text"],
            "xml_output": results["xml_output"],
            "freq_table": results.get("freq_table_data")
        })

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Processing error: {str(e)}")


@app.get("/download/{format}/{session_id}")
async def download_result(format: str, session_id: str):
    """
    Download processed results in different formats.
    Formats: txt, xml, json
    """
    if session_id not in results_store:
        raise HTTPException(status_code=404, detail="Session not found or expired")

    results = results_store[session_id]

    if format == "txt":
        content = results["filtered_text"]
        media_type = "text/plain"
        filename = "filtered_output.txt"

    elif format == "xml":
        content = results["xml_output"]
        media_type = "application/xml"
        filename = "filtered_output.xml"

    elif format == "json":
        content = json.dumps({
            "filtered_text": results["filtered_text"],
            "xml_output": results["xml_output"],
            "freq_table": results.get("freq_table_data")
        }, indent=2)
        media_type = "application/json"
        filename = "filtered_output.json"

    else:
        raise HTTPException(status_code=400, detail="Invalid format. Use: txt, xml, or json")

    return Response(
        content=content,
        media_type=media_type,
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
