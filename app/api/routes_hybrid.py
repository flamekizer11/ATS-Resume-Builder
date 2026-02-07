# API endpoints with hybrid logic

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse
import shutil
import os
import json
import re
from app.services.gemini_hybrid import extract_resume_data, analyze_and_score, apply_changes
from app.services.generator import generate_ats_resume
from app.utils.helpers import ensure_directories

router = APIRouter()

ensure_directories()


@router.post("/analyze")
async def analyze_resume(
    resume: UploadFile = File(..., description="Upload PDF or DOCX resume"),
    job_role: str = Form(..., description="Target job role (e.g.'Front End Developer' 'Software Engineer')"),
    job_desc: str = Form(None, description="Job description"),
    use_api_for_suggestions: bool = Form(False, description="Use API for suggestions (default: rule-based with API fallback)")
):
    """
    Analyze uploaded resume and provide ATS score with suggestions

    Returns:
    - ats_score: Overall ATS score (0-100)
    - score_breakdown: Detailed scoring by category
    - explanation: Summary of strengths and gaps
    - suggestions: List of actionable improvements
    - extracted_data: Parsed resume data
    """
    try:
        # Validate file type
        if not resume.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

        # Save uploaded file
        file_path = f"uploads/{resume.filename}"
        with open(file_path, "wb") as f:
            shutil.copyfileobj(resume.file, f)

        # Extract data using hybrid processing
        extracted = extract_resume_data(file_path, job_role, job_desc or "")

        # Score and suggest using hybrid processing
        analysis = analyze_and_score(extracted, job_role, job_desc or "", use_api_for_suggestions)

        # Cleanup uploaded file
        os.remove(file_path)

        return {
            "ats_score": analysis.get("ats_score", 0),
            "score_breakdown": analysis.get("score_breakdown", {}),
            "explanation": analysis.get("explanation", ""),
            "suggestions": analysis.get("suggestions", []),
            "extracted_data": extracted
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.post("/optimize")
async def optimize_resume(
    resume: UploadFile = File(..., description="Upload PDF or DOCX resume"),
    job_role: str = Form(..., description="Target job role"),
    job_desc: str = Form(None, description="Job description (optional)"),
    suggestions: str = Form(None, description="JSON string of suggestions to apply"),
    use_api_for_optimization: bool = Form(False, description="Use API for resume optimization (default: hybrid offline with API fallback)")
):
    """
    Apply optimizations to resume and generate new DOCX

    Returns:
    - download_url: URL to download optimized resume
    - applied_changes: List of changes made
    """
    # Debug: Print received values
    print(f"DEBUG: job_role='{job_role}', job_desc='{job_desc}', suggestions='{suggestions}', use_api_for_optimization={use_api_for_optimization}")
    
    try:
        # Validate file type and saving uploaded file
        if not resume.filename.lower().endswith(('.pdf', '.docx', '.doc')):
            raise HTTPException(status_code=400, detail="Only PDF and DOCX files are supported")

        file_path = f"uploads/{resume.filename}"
        with open(file_path, "wb") as f:
            shutil.copyfileobj(resume.file, f)

        # Parse suggestions and Extract and optimize data
        suggestions_list = json.loads(suggestions) if suggestions else []
        extracted = extract_resume_data(file_path, job_role, job_desc or "")
        optimized_data = apply_changes(extracted, suggestions_list, job_role, job_desc or "", use_api_for_optimization)

        # Generate optimized resume with proper filename
        base_name = resume.filename
        while '.' in base_name:
            base_name = base_name.rsplit('.', 1)[0]
        base_name = re.sub(r'[^\w\-_\.]', '_', base_name)
        output_filename = f"optimized_{base_name}.docx"
        output_path = f"outputs/{output_filename}"
        generate_ats_resume(optimized_data, output_path)

        # Clean the uploaded file
        os.remove(file_path)

        return {
            "download_url": f"/download/{output_filename}",
            "applied_changes": suggestions_list,
            "optimized_data": optimized_data
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Optimization failed: {str(e)}")


@router.get("/download/{filename}")
async def download_resume(filename: str):
    """
    Download optimized resume file
    """
    file_path = f"outputs/{filename}"
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    )

# Additional endpoint to check API status and configuration if needed for debugging or client information
@router.get("/config")
async def get_config():
    """
    Get API configuration and status
    """
    return {
        "version": "2.0.0",
        "processing_mode": "hybrid",
        "primary_method": "rule-based",
        "fallback_method": "google-gemini",
        "supported_formats": ["pdf", "docx", "doc"],
        "max_file_size": "10MB",
        "rate_limit": "100 requests/hour"
    }