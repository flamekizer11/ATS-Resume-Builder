"""
Helper Utilities
Provides common utility functions used across the application
"""

import os
import json
import re
from typing import Any, Dict


def ensure_directories():
    """
    Create necessary directories if they don't exist
    
    Creates:
        - uploads/: Temporary storage for uploaded files
        - outputs/: Storage for generated resume files
    """
    os.makedirs("uploads", exist_ok=True)
    os.makedirs("outputs", exist_ok=True)
    print("Directories initialized: uploads/, outputs/")


def clean_json_response(text: str) -> str:
    """
    Remove markdown code blocks from AI response
    
    Args:
        text: Raw AI response text
        
    Returns:
        Cleaned JSON string
    """
    text = text.strip()
    
    # Remove ```json ... ``` blocks
    if text.startswith('```json'):
        text = text.split('```json', 1)[1]
        text = text.split('```', 1)[0]
        text = text.strip()
    
    # Remove ``` ... ``` blocks
    elif text.startswith('```'):
        text = text.split('```', 1)[1]
        text = text.split('```', 1)[0]
        text = text.strip()
    
    return text


def parse_json_safe(text: str) -> dict:
    """
    Safely parse JSON from AI response
    
    Args:
        text: JSON string (possibly with markdown)
        
    Returns:
        Parsed dictionary
        
    Raises:
        ValueError: If JSON parsing fails
    """
    cleaned = clean_json_response(text)
    
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as e:
        # Show preview of problematic content
        preview = cleaned[:500] if len(cleaned) > 500 else cleaned
        raise ValueError(
            f"Failed to parse JSON: {str(e)}\n"
            f"Content preview: {preview}..."
        )


def validate_file_type(filename: str, allowed_extensions: list = None) -> bool:
    """
    Validate file extension
    
    Args:
        filename: Name of the file
        allowed_extensions: List of allowed extensions (default: ['pdf', 'docx', 'doc'])
        
    Returns:
        True if valid, False otherwise
    """
    if allowed_extensions is None:
        allowed_extensions = ['pdf', 'docx', 'doc']
    
    ext = filename.lower().split('.')[-1]
    return ext in allowed_extensions


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename for safe filesystem operations
    
    Args:
        filename: Original filename
        
    Returns:
        Sanitized filename
    """
    # Remove or replace unsafe characters
    filename = re.sub(r'[<>:"/\\|?*]', '_', filename)
    
    # Replace spaces with underscores
    filename = filename.replace(' ', '_')
    
    # Remove multiple consecutive underscores
    filename = re.sub(r'_+', '_', filename)
    
    # Limit length
    name, ext = os.path.splitext(filename)
    if len(name) > 100:
        name = name[:100]
    
    return name + ext


def format_file_size(size_bytes: int) -> str:
    """
    Format file size in human-readable format
    
    Args:
        size_bytes: Size in bytes
        
    Returns:
        Formatted string (e.g., "1.5 MB")
    """
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def merge_dicts(dict1: dict, dict2: dict) -> dict:
    """
    Deep merge two dictionaries
    
    Args:
        dict1: First dictionary (base)
        dict2: Second dictionary (updates)
        
    Returns:
        Merged dictionary
    """
    result = dict1.copy()
    
    for key, value in dict2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_dicts(result[key], value)
        else:
            result[key] = value
    
    return result


def extract_keywords_simple(text: str, min_length: int = 4) -> list:
    """
    Extract keywords from text using simple tokenization
    
    Args:
        text: Input text
        min_length: Minimum word length to consider
        
    Returns:
        List of keywords
    """
    # Common stop words to filter out 
    stop_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
        'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
        'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'should',
        'could', 'may', 'might', 'must', 'can', 'this', 'that', 'these', 'those'
    }
    
    # Extract words
    words = re.findall(r'\b[a-z]+\b', text.lower())
    
    # Filter
    keywords = [
        word for word in words
        if len(word) >= min_length and word not in stop_words
    ]
    
    # Remove duplicates while preserving order 
    seen = set()
    unique_keywords = []
    for keyword in keywords:
        if keyword not in seen:
            seen.add(keyword)
            unique_keywords.append(keyword)
    
    return unique_keywords


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate text to maximum length
    
    Args:
        text: Input text
        max_length: Maximum length
        suffix: Suffix to add when truncated
        
    Returns:
        Truncated text
    """
    if len(text) <= max_length:
        return text
    
    return text[:max_length - len(suffix)] + suffix


def normalize_whitespace(text: str) -> str:
    """
    Normalize whitespace in text
    
    Args:
        text: Input text
        
    Returns:
        Normalized text
    """
    # Replace multiple spaces with single space
    text = re.sub(r'\s+', ' ', text)
    
    # Remove leading/trailing whitespace
    text = text.strip()
    
    return text


def is_valid_email(email: str) -> bool:
    """
    Validate email format
    
    Args:
        email: Email address
        
    Returns:
        True if valid format, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def is_valid_phone(phone: str) -> bool:
    """
    Validate phone number format
    
    Args:
        phone: Phone number
        
    Returns:
        True if valid format, False otherwise
    """
    # Remove common formatting characters
    cleaned = re.sub(r'[\s\-\(\)\.]', '', phone)
    
    # Check if it's digits and reasonable length
    return cleaned.isdigit() and 10 <= len(cleaned) <= 15


def chunk_list(lst: list, chunk_size: int) -> list:
    """
    Split list into chunks
    
    Args:
        lst: Input list
        chunk_size: Size of each chunk
        
    Returns:
        List of chunks
    """
    return [lst[i:i + chunk_size] for i in range(0, len(lst), chunk_size)]


def safe_get(data: dict, *keys, default=None):
    """
    Safely get nested dictionary value
    
    Args:
        data: Dictionary
        *keys: Nested keys to traverse
        default: Default value if key not found
        
    Returns:
        Value or default
        
    Example:
        safe_get(data, 'personal', 'email', default='')
    """
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key)
            if current is None:
                return default
        else:
            return default
    return current if current is not None else default


def calculate_percentage(part: float, total: float) -> float:
    """
    Calculate percentage safely
    
    Args:
        part: Part value
        total: Total value
        
    Returns:
        Percentage (0-100)
    """
    if total == 0:
        return 0.0
    return round((part / total) * 100, 2)


def clean_html_tags(text: str) -> str:
    """
    Remove HTML tags from text
    
    Args:
        text: Text with HTML tags
        
    Returns:
        Clean text
    """
    clean = re.sub(r'<[^>]+>', '', text)
    return normalize_whitespace(clean)


def get_file_extension(filename: str) -> str:
    """
    Get file extension from filename
    
    Args:
        filename: Filename
        
    Returns:
        Extension (lowercase, without dot)
    """
    return filename.lower().split('.')[-1] if '.' in filename else ''


def create_slug(text: str, max_length: int = 50) -> str:
    """
    Create URL-friendly slug from text
    
    Args:
        text: Input text
        max_length: Maximum slug length
        
    Returns:
        Slug string
    """
    # Convert to lowercase
    slug = text.lower()
    
    # Replace spaces and special chars with hyphens
    slug = re.sub(r'[^a-z0-9]+', '-', slug)
    
    # Remove leading/trailing hyphens
    slug = slug.strip('-')
    
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    
    # Truncate
    if len(slug) > max_length:
        slug = slug[:max_length].rstrip('-')
    
    return slug


def dict_to_pretty_json(data: dict, indent: int = 2) -> str:
    """
    Convert dictionary to pretty-printed JSON string
    
    Args:
        data: Dictionary
        indent: Indentation spaces
        
    Returns:
        Pretty JSON string
    """
    return json.dumps(data, indent=indent, ensure_ascii=False)


def load_json_file(filepath: str) -> dict:
    """
    Load JSON from file
    
    Args:
        filepath: Path to JSON file
        
    Returns:
        Parsed dictionary
        
    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If JSON is invalid
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File not found: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filepath}: {str(e)}")


def save_json_file(data: dict, filepath: str, pretty: bool = True):
    """
    Save dictionary to JSON file
    
    Args:
        data: Dictionary to save
        filepath: Output file path
        pretty: Whether to pretty-print
    """
    with open(filepath, 'w', encoding='utf-8') as f:
        if pretty:
            json.dump(data, f, indent=2, ensure_ascii=False)
        else:
            json.dump(data, f, ensure_ascii=False)


def count_words(text: str) -> int:
    """
    Count words in text
    
    Args:
        text: Input text
        
    Returns:
        Word count
    """
    words = re.findall(r'\b\w+\b', text)
    return len(words)


def get_timestamp() -> str:
    """
    Get current timestamp string
    
    Returns:
        ISO format timestamp
    """
    from datetime import datetime
    return datetime.now().isoformat()


# Logging helpers
def log_info(message: str):
    """Print info message"""
    print(f"Info: {message}")


def log_success(message: str):
    """Print success message"""
    print(f"Success! {message}")


def log_warning(message: str):
    """Print warning message"""
    print(f"Warning!! {message}")


def log_error(message: str):
    """Print error message"""
    print(f"Watch Out {message}")


def log_debug(message: str):
    """Print debug message"""
    print(f"Debug {message}")