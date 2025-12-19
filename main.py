"""
FastAPI backend: handle file uploads and coordinate modules
"""
import os
import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, HTTPException, Form
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware

from document_processor import DocumentProcessor
from form_filler import FormFiller

# Create FastAPI app
app = FastAPI(title="Document Automation System")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create upload directory
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# In-memory storage for extracted data and API key
extracted_data = {}
api_key_storage = {"key": None}


@app.get("/", response_class=HTMLResponse)
async def root():
    """Return the frontend page"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return f.read()


@app.post("/set-api-key")
async def set_api_key(api_key: str = Form(...)):
    """Set the API key"""
    api_key_storage["key"] = api_key
    return JSONResponse({"status": "success", "message": "API key has been set"})


@app.get("/check-api-key")
async def check_api_key():
    """Check whether the API key is set"""
    return JSONResponse({"has_key": api_key_storage["key"] is not None})


@app.post("/upload/passport")
async def upload_passport(file: UploadFile = File(...)):
    """Upload a passport file"""
    if not api_key_storage["key"]:
        raise HTTPException(status_code=400, detail="Please set the API key first")
    
    try:
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        file_path = UPLOAD_DIR / f"passport_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Use stored API key
        processor = DocumentProcessor(api_key_storage["key"])
        passport_data = await processor.extract_passport_info(str(file_path))
        extracted_data["passport"] = passport_data
        
        return JSONResponse({
            "status": "success",
            "message": "Passport uploaded successfully",
            "data": passport_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/upload/g28")
async def upload_g28(file: UploadFile = File(...)):
    """Upload a G-28 form"""
    if not api_key_storage["key"]:
        raise HTTPException(status_code=400, detail="Please set the API key first")
    
    try:
        allowed_types = ["image/jpeg", "image/png", "application/pdf"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="Unsupported file type")
        
        file_path = UPLOAD_DIR / f"g28_{file.filename}"
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        processor = DocumentProcessor(api_key_storage["key"])
        g28_data = await processor.extract_g28_info(str(file_path))
        extracted_data["g28"] = g28_data
        
        return JSONResponse({
            "status": "success",
            "message": "G-28 form uploaded successfully",
            "data": g28_data
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/extracted-data")
async def get_extracted_data():
    """Get extracted data"""
    return JSONResponse(extracted_data)


@app.post("/fill-form")
async def fill_form():
    """Fill the form using extracted data"""
    print(extracted_data)
    try:
        if not extracted_data:
            raise HTTPException(status_code=400, detail="Please upload documents first")
        
        # Pass passport and G-28 data separately so form filler can use correct data for each section
        passport_data = extracted_data.get("passport", {})
        g28_data = extracted_data.get("g28", {})
        
        form_filler = FormFiller()
        result = await form_filler.fill_form(passport_data, g28_data)
        
        return JSONResponse({
            "status": "success",
            "message": "Form filling completed",
            "result": result
        })
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/clear")
async def clear_data():
    """Clear uploaded and extracted data"""
    global extracted_data
    extracted_data = {}
    
    for file in UPLOAD_DIR.iterdir():
        if file.is_file() and file.name != ".gitkeep":
            file.unlink()
    
    return JSONResponse({"status": "success", "message": "Data has been cleared"})


if __name__ == "__main__":
    import uvicorn
    print("Starting document automation service...")
    print("Access at: http://localhost:8000")
    uvicorn.run(app, host="0.0.0.0", port=8000)
