import google.generativeai as genai
import json
import os
from dotenv import load_dotenv
from app.utils.helpers import parse_json_safe
from app.services.parser import extract_text_from_file
from app.services.rule_based_parser import parse_resume_rule_based
from app.services.ats_scorer import calculate_ats_score_rule_based
from app.services.suggestion_generator import generate_suggestions_rule_based
from app.services.resume_enhancer import apply_suggestions_rule_based

load_dotenv()
genai.configure(api_key=os.getenv('GEMINI_API_KEY'))
model = genai.GenerativeModel('gemini-2.5-flash')

# Configuration flags that can be set true whenever needed but here we are using them as fallbacks when rule-based methods fail or when user explicitly requests API usage. 
# This allows us to maintain a primarily rule-based approach while leveraging LLM capabilities as needed without incurring unnecessary API calls.
USE_LLM_FOR_PARSING = False  
USE_LLM_FOR_SCORING = False  
USE_LLM_FOR_SUGGESTIONS = False  
USE_LLM_FOR_ENHANCEMENT = False  


def extract_resume_data(file_path: str, job_role: str, job_desc: str) -> dict:
    """
    Extract structured data from resume
    PRIMARY: Rule-based parser
    FALLBACK: Gemini AI (if rule-based fails or flag is set)
    """
    
    # Extract text from file
    resume_text = extract_text_from_file(file_path)
    
    # Try rule-based parsing first (unless LLM flag is set)
    if not USE_LLM_FOR_PARSING:
        try:
            print("Using rule-based parser...")
            parsed_data = parse_resume_rule_based(resume_text)
            
            # Validate parsed data
            if _validate_parsed_data(parsed_data):
                print("Rule-based parsing successful")
                return parsed_data
            else:
                print("Rule-based parsing incomplete, falling back to LLM...")
        except Exception as e:
            print(f"Rule-based parsing failed: {str(e)}, falling back to LLM...")
    else:
        print("LLM parsing enabled by flag")
    
    # Fallback to LLM
    return _extract_with_llm(resume_text, job_role, job_desc)


def analyze_and_score(extracted_data: dict, job_role: str, job_desc: str, use_api_for_suggestions: bool = False) -> dict:
    """
    Score resume and provide suggestions
    PRIMARY: Rule-based scoring and suggestions
    FALLBACK: Gemini AI (if rule-based fails or flag is set)
    """
    
    # Check if user requested API or if rule-based should be used
    if use_api_for_suggestions or USE_LLM_FOR_SCORING or USE_LLM_FOR_SUGGESTIONS:
        print("Using API for analysis (user requested or fallback)")
        return _analyze_with_llm(extracted_data, job_role, job_desc)
    
    # Try rule-based approach first
    try:
        print("Using rule-based scoring and suggestions...")
        
        # Calculate score
        ats_score, score_breakdown, explanation = calculate_ats_score_rule_based(
            extracted_data, job_role, job_desc
        )
        
        # Generate suggestions
        suggestions = generate_suggestions_rule_based(
            extracted_data, job_role, job_desc, score_breakdown
        )
        
        print(f"Rule-based analysis complete - Score: {ats_score}")
        
        return {
            'ats_score': ats_score,
            'score_breakdown': score_breakdown,
            'explanation': explanation,
            'suggestions': suggestions,
            'source': 'rule_based',
            'needs_api_check': len(suggestions) < 3  # Flag if few suggestions generated
        }
    except Exception as e:
        print(f"Rule-based analysis failed: {str(e)}, falling back to LLM...")
        return _analyze_with_llm(extracted_data, job_role, job_desc)


def apply_changes(original_data: dict, suggestions: list, job_role: str, job_desc: str, use_api_for_optimization: bool = False) -> dict:
    """
    Apply accepted suggestions to resume data
    PRIMARY: Rule-based enhancement
    FALLBACK: Gemini AI (if rule-based fails or flag is set)
    """
    
    # Check if user requested API or if rule-based should be used
    if use_api_for_optimization or USE_LLM_FOR_ENHANCEMENT:
        print("Using API for resume optimization (user requested or fallback)")
        return _apply_changes_with_llm(original_data, suggestions, job_role, job_desc)
    
    # Try rule-based approach first
    try:
        print("Using rule-based resume enhancement...")
        enhanced_data = apply_suggestions_rule_based(
            original_data, suggestions, job_role, job_desc
        )
        
        # Validate enhanced data
        if _validate_parsed_data(enhanced_data):
            print("Rule-based enhancement successful")
            return enhanced_data
        else:
            print("Rule-based enhancement incomplete, falling back to LLM...")
            return _apply_changes_with_llm(original_data, suggestions, job_role, job_desc)
    except Exception as e:
        print(f"Rule-based enhancement failed: {str(e)}, falling back to LLM...")
        return _apply_changes_with_llm(original_data, suggestions, job_role, job_desc)




# LLM FALLBACK FUNCTIONS

def _extract_with_llm(resume_text: str, job_role: str, job_desc: str) -> dict:
    """Extract data using Gemini (FALLBACK)"""
    
    prompt = f"""You are an expert resume parser and ATS analyzer.

INPUT:
- Resume Content: {resume_text}
- Target Job Role: {job_role}
- Job Description: {job_desc if job_desc else "Not provided"}

TASK:
Extract ALL information from the resume in this EXACT JSON structure:

{{
  "personal": {{
    "name": "",
    "email": "",
    "phone": "",
    "linkedin": "",
    "location": ""
  }},
  "summary": "",
  "skills": ["skill1", "skill2"],
  "experience": [
    {{
      "title": "",
      "company": "",
      "duration": "",
      "points": ["point1", "point2"]
    }}
  ],
  "education": [
    {{
      "degree": "",
      "institution": "",
      "year": "",
      "gpa": ""
    }}
  ],
  "projects": [
    {{
      "name": "",
      "description": "",
      "tech": ["tech1"],
      "points": ["point1"]
    }}
  ],
  "certifications": ["cert1"],
  "achievements": ["achievement1"]
}}

RULES:
- Extract exactly as written, don't modify
- If section missing, use empty array/string
- Return ONLY valid JSON, no markdown, no explanation"""
    
    response = model.generate_content(prompt)
    return parse_json_safe(response.text)


def _analyze_with_llm(extracted_data: dict, job_role: str, job_desc: str) -> dict:
    """Score and suggest using Gemini (FALLBACK)"""
    
    prompt = f"""ATS Analysis for {job_role}:

Resume: {json.dumps(extracted_data)}
Job Desc: {job_desc[:500] if job_desc else "Not provided"}

Calculate ATS score (0-100) and provide 3-5 concise suggestions.

JSON output only:
{{
  "ats_score": 75,
  "score_breakdown": {{"keyword_match": 22, "skills_relevance": 20, "format_quality": 18, "experience_alignment": 10, "completeness": 5}},
  "explanation": "Brief summary",
  "suggestions": [
    {{"id": 0, "section": "skills", "change": "Add Python", "reason": "Required", "impact": "+5 points", "priority": "high"}}
  ],
  "source": "api"
}}"""
    
    response = model.generate_content(prompt)
    return parse_json_safe(response.text)

# we can further break down enhancement into multiple steps if needed, but for simplicity we will do it in one step here. 
# The prompt can be made more detailed to ensure better results.
def _apply_changes_with_llm(original_data: dict, suggestions: list, job_role: str, job_desc: str) -> dict:
    """Apply changes using Gemini (FALLBACK)"""
    
    prompt = f"""You are a professional resume writer specializing in ATS optimization.

INPUT:
- Original Resume Data: {json.dumps(original_data, indent=2)}
- Accepted Suggestions: {json.dumps(suggestions, indent=2)}
- Job Role: {job_role}
- Job Description: {job_desc if job_desc else "Not provided"}

TASK:
Apply all accepted suggestions to the original data and return enhanced resume data.

ENHANCEMENT RULES:
1. Apply each accepted change to the correct section
2. Ensure ATS-friendly formatting:
   - No tables, columns, text boxes
   - Simple bullet points
   - Standard section headers
   - No special characters
3. Optimize for keywords from JD
4. Keep professional tone
5. Quantify achievements where possible

OUTPUT FORMAT (JSON only):
{{
  "personal": {{}},
  "summary": "enhanced summary",
  "skills": ["enhanced", "skills"],
  "experience": [{{}}],
  "education": [{{}}],
  "projects": [{{}}],
  "certifications": [],
  "achievements": []
}}

Return ONLY valid JSON with enhanced data, maintaining all original structure. No markdown, no explanation."""
    
    response = model.generate_content(prompt)
    return parse_json_safe(response.text)


# VALIDATION HELPERS

def _validate_parsed_data(data: dict) -> bool:
    """Validate that parsed data has minimum required fields"""
    
    # Check required structure
    if not isinstance(data, dict):
        return False
    
    # Check required top-level keys
    required_keys = ['personal', 'skills', 'experience', 'education']
    if not all(key in data for key in required_keys):
        return False
    
    # Check personal info has at least name or email
    personal = data.get('personal', {})
    if not (personal.get('name') or personal.get('email')):
        return False
    
    # Should have at least some content
    has_content = (
        len(data.get('skills', [])) > 0 or
        len(data.get('experience', [])) > 0 or
        len(data.get('education', [])) > 0 or
        data.get('summary', '').strip() != ''
    )
    
    if not has_content:
        return False
    
    return True