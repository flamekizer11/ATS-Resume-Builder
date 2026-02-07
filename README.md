# ATS Resume Optimizer API

<div align="center">
  <h3>AI-Powered Resume Optimization with ATS Scoring</h3>
  <p><strong>Hybrid Processing: Rule-based Primary + LLM Fallback</strong></p>

  ![FastAPI](https://img.shields.io/badge/FastAPI-009688?style=for-the-badge&logo=fastapi&logoColor=white)
  ![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)
  ![Google Gemini](https://img.shields.io/badge/Google%20Gemini-4285F4?style=for-the-badge&logo=google&logoColor=white)
  ![License](https://img.shields.io/badge/License-MIT-green.svg?style=for-the-badge)

  <p><em>Transform your resume into an ATS-friendly document with intelligent scoring and optimization suggestions</em></p>

  <p><a href="demo/Demo Video.mp4">View Demo Video</a></p>
</div>

---

## Table of Contents

- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [API Documentation](#api-documentation)
- [Configuration](#configuration)
- [Usage Examples](#usage-examples)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

---

## Features

### Core Functionality
- **Resume Parsing**: Extract structured data from PDF and DOCX resumes
- **ATS Scoring**: Calculate comprehensive ATS compatibility scores (0-100)
- **Smart Suggestions**: Get actionable improvement recommendations
- **Resume Optimization**: Generate ATS-optimized DOCX resumes
- **Hybrid Processing**: Cost-effective rule-based primary with AI fallback

### AI-Powered Analysis
- **Google Gemini Integration**: Advanced AI analysis when needed
- **Cost Optimization**: 97% cost reduction vs pure LLM approach
- **Intelligent Fallback**: Seamless switching between processing methods

### Comprehensive Scoring
- **Overall ATS Score**: Complete resume evaluation
- **Category Breakdown**: Detailed scoring by sections
- **Keyword Analysis**: Job-specific optimization suggestions
- **Format Validation**: ATS-friendly formatting checks

### File Support
- **PDF Processing**: Advanced text extraction with pdfplumber
- **DOCX Support**: Native Word document processing
- **Batch Processing**: Handle multiple resumes efficiently

---

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   FastAPI       │────│  Hybrid Service  │────│  Gemini API     │
│   Application   │    │  (Rule-based +   │    │  (Fallback)     │
│                 │    │   AI Fallback)   │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   PDF/DOCX      │    │   Text Parsing   │    │   AI Analysis   │
│   Upload        │────│   & Extraction  │────│   & Scoring     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Processing Flow:
1. **Upload**: Resume file (PDF/DOCX) + Job details
2. **Primary**: Rule-based parsing and scoring (fast, free)
3. **Fallback**: Google Gemini AI analysis (when needed)
4. **Optimization**: Generate improved DOCX resume
5. **Download**: ATS-optimized resume file

---

## Tech Stack

### Backend Framework
- **FastAPI**: Modern, fast web framework for building APIs
- **Uvicorn**: ASGI server for high-performance async applications

### Document Processing
- **pdfplumber**: Advanced PDF text extraction
- **python-docx**: DOCX document manipulation
- **spaCy**: Industrial-strength NLP processing

### AI & Machine Learning
- **Google Generative AI (Gemini)**: Advanced AI analysis
- **spaCy en_core_web_sm**: Pre-trained NLP model

### Utilities
- **python-multipart**: File upload handling
- **python-dotenv**: Environment variable management

---

## Installation

### Prerequisites
- Python 3.8+
- pip package manager
- Git (for cloning the repository)

### Step-by-Step Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/flamekizer11/ATS-Resume-Builder.git
   cd resume_creator
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install spaCy model:**
   ```bash
   python -m spacy download en_core_web_sm
   ```

5. **Set up environment variables:**
   ```bash
   cp .env.example .env  # If you have an example file
   # Edit .env with your API keys
   ```

### Environment Configuration

Create a `.env` file in the root directory:

```env
# Google Gemini API Configuration
GOOGLE_API_KEY=your_google_gemini_api_key_here

# Optional: Application Settings
DEBUG=True
MAX_FILE_SIZE=10485760  # 10MB in bytes
```

---

## Quick Start

### Start the Server

```bash
# Using Python directly (recommended)
python main.py

# Or using uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

### Access the Application

- **API Documentation**: http://localhost:8000
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Health Check**: http://localhost:8000/health

### Basic Usage Example

```python
import requests

# Analyze a resume
files = {'resume': open('resume.pdf', 'rb')}
data = {
    'job_role': 'Software Engineer',
    'job_desc': 'Python development role',
    'use_api_for_suggestions': False
}

response = requests.post('http://localhost:8000/analyze', files=files, data=data)
result = response.json()

print(f"ATS Score: {result['ats_score']}")
print(f"Suggestions: {result['suggestions']}")
```

---

## API Documentation

### Endpoints Overview

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/analyze` | Analyze resume and get ATS score |
| `POST` | `/optimize` | Generate optimized resume |
| `GET` | `/download/{filename}` | Download optimized resume |
| `GET` | `/config` | Get API configuration |
| `GET` | `/health` | Health check |

### Analyze Resume

**Endpoint:** `POST /analyze`

**Request:**
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `resume` (file): PDF or DOCX resume file
  - `job_role` (string): Target job position
  - `job_desc` (string, optional): Job description
  - `use_api_for_suggestions` (boolean): Use AI for suggestions

**Response:**
```json
{
  "ats_score": 87,
  "score_breakdown": {
    "keywords": 85,
    "format": 90,
    "experience": 82,
    "education": 95
  },
  "explanation": "Strong resume with good keyword matching...",
  "suggestions": [
    "Add more quantifiable achievements",
    "Include relevant certifications"
  ],
  "extracted_data": {
    "personal": {...},
    "experience": [...],
    "skills": [...],
    "education": [...]
  }
}
```

### Optimize Resume

**Endpoint:** `POST /optimize`

**Request:**
- **Content-Type:** `multipart/form-data`
- **Parameters:**
  - `resume` (file): PDF or DOCX resume file
  - `job_role` (string): Target job position
  - `job_desc` (string, optional): Job description
  - `suggestions` (string): JSON array of suggestions to apply
  - `use_api_for_optimization` (boolean): Use AI for optimization

**Response:**
```json
{
  "download_url": "/download/optimized_resume.docx",
  "applied_changes": ["Added keywords", "Improved formatting"],
  "optimized_data": {...}
}
```

### Download Resume

**Endpoint:** `GET /download/{filename}`

**Response:** Optimized DOCX file download

---

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GOOGLE_API_KEY` | Google Gemini API key | Required |
| `DEBUG` | Enable debug mode | `False` |
| `MAX_FILE_SIZE` | Maximum upload size (bytes) | `10485760` |

### Application Settings

The application automatically creates necessary directories:
- `uploads/` - Temporary uploaded files
- `outputs/` - Generated optimized resumes

### Performance Tuning

- **Hybrid Processing**: Adjust fallback thresholds in service files
- **File Size Limits**: Configure in routes or middleware
- **Rate Limiting**: Add middleware for production deployment

---

## Usage Examples

### Python Client Example

```python
import requests

class ResumeOptimizerClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url

    def analyze_resume(self, file_path, job_role, job_desc=None):
        with open(file_path, 'rb') as f:
            files = {'resume': f}
            data = {'job_role': job_role}
            if job_desc:
                data['job_desc'] = job_desc

            response = requests.post(f"{self.base_url}/analyze", files=files, data=data)
            return response.json()

    def optimize_resume(self, file_path, job_role, suggestions):
        with open(file_path, 'rb') as f:
            files = {'resume': f}
            data = {
                'job_role': job_role,
                'suggestions': json.dumps(suggestions)
            }

            response = requests.post(f"{self.base_url}/optimize", files=files, data=data)
            return response.json()

# Usage
client = ResumeOptimizerClient()
result = client.analyze_resume("my_resume.pdf", "Data Scientist")
print(f"Score: {result['ats_score']}")
```

### cURL Examples

```bash
# Analyze resume
curl -X POST "http://localhost:8000/analyze" \
  -F "resume=@resume.pdf" \
  -F "job_role=Software Engineer" \
  -F "job_desc=Python development position"

# Optimize resume
curl -X POST "http://localhost:8000/optimize" \
  -F "resume=@resume.pdf" \
  -F "job_role=Software Engineer" \
  -F "suggestions=[\"Add Python skills\", \"Improve formatting\"]"
```

---

## Testing

### Run Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python test_resume_recreation.py

# Run with coverage
python -m pytest --cov=app --cov-report=html
```

### Test Files Included
- `test_docx.py` - DOCX processing tests
- `test_extraction.py` - Text extraction tests
- `test_parse_and_generate.py` - Parsing and generation tests
- `test_resume_recreation.py` - End-to-end tests

### Manual Testing

1. Start the server: `python main.py`
2. Visit http://localhost:8000/docs
3. Use the interactive Swagger UI to test endpoints
4. Upload sample resumes and verify results

---

## Contributing

### Development Setup

1. Fork the repository
2. Create a feature branch: `git checkout -b feature-name`
3. Install development dependencies
4. Make your changes
5. Run tests: `python -m pytest`
6. Commit changes: `git commit -am 'Add feature'`
7. Push to branch: `git push origin feature-name`
8. Create a Pull Request

### Code Style

- Follow PEP 8 Python style guidelines
- Use type hints for function parameters
- Add docstrings to all functions and classes
- Write comprehensive tests for new features

### Commit Guidelines

- Use clear, descriptive commit messages
- Start with a verb (Add, Fix, Update, Remove)
- Reference issue numbers when applicable

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### MIT License Summary

- Commercial use
- Modification
- Distribution
- Private use
- Liability
- Warranty

---

## Acknowledgments

- **FastAPI** - The modern web framework that makes this possible
- **Google Gemini** - For providing powerful AI capabilities
- **spaCy** - Industrial-strength NLP processing
- **Open source community** - For the amazing libraries and tools

---

## Support

- **Issues**: [GitHub Issues](https://github.com/flamekizer11/ATS-Resume-Builder/issues)
- **Discussions**: [GitHub Discussions](https://github.com/flamekizer11/ATS-Resume-Builder/discussions)
- **Email**: pratiksinghyo02776@gmail.com

---

<div align="center">
  <p><strong>Would love to know improvement tweaks. Do reach out!</strong></p>
  <p>Transform your resume into an ATS-winning document</p>
</div></content>
<parameter name="filePath">c:\Users\pc\Desktop\resume_creator\README.md