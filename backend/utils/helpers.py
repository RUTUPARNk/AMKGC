import json
import logging
import re
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
import hashlib

logger = logging.getLogger(__name__)

def generate_uuid() -> str:
    """Generate a UUID string"""
    return str(uuid.uuid4())

def sanitize_input(text: str) -> str:
    """Sanitize user input to prevent XSS and SQL injection"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    text = re.sub(r'javascript:', '', text, flags=re.IGNORECASE)
    text = re.sub(r'on\w+\s*=', '', text, flags=re.IGNORECASE)
    
    return text.strip()

def validate_email(email: str) -> bool:
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))

def hash_password(password: str) -> str:
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def format_timestamp(timestamp: datetime) -> str:
    """Format timestamp for display"""
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")

def parse_json_safely(data: str) -> Optional[Dict[str, Any]]:
    """Safely parse JSON string"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None

def truncate_text(text: str, max_length: int = 100) -> str:
    """Truncate text to specified length"""
    if len(text) <= max_length:
        return text
    return text[:max_length-3] + "..."

def extract_node_references(text: str) -> List[str]:
    """Extract node references from text (#Node_1, #Node_2, etc.)"""
    pattern = r'#Node_\d+'
    return re.findall(pattern, text)

def validate_node_name(name: str) -> bool:
    """Validate node name format"""
    if not name or len(name) > 100:
        return False
    return bool(re.match(r'^[a-zA-Z0-9_\s-]+$', name))

def calculate_token_count(text: str) -> int:
    """Calculate approximate token count"""
    return len(text.split()) + len([c for c in text if c in '.,;:!?'])

def chunk_text(text: str, chunk_size: int) -> List[str]:
    """Split text into chunks of specified size"""
    words = text.split()
    chunks = []
    current_chunk = []
    current_size = 0
    
    for word in words:
        if current_size + len(word) + 1 <= chunk_size:
            current_chunk.append(word)
            current_size += len(word) + 1
        else:
            if current_chunk:
                chunks.append(' '.join(current_chunk))
            current_chunk = [word]
            current_size = len(word)
    
    if current_chunk:
        chunks.append(' '.join(current_chunk))
    
    return chunks

def merge_json_objects(obj1: Dict[str, Any], obj2: Dict[str, Any]) -> Dict[str, Any]:
    """Merge two JSON objects, with obj2 taking precedence"""
    result = obj1.copy()
    for key, value in obj2.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge_json_objects(result[key], value)
        else:
            result[key] = value
    return result

def flatten_dict(d: Dict[str, Any], parent_key: str = '', sep: str = '_') -> Dict[str, Any]:
    """Flatten nested dictionary"""
    items = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep=sep).items())
        else:
            items.append((new_key, v))
    return dict(items)

def get_nested_value(data: Dict[str, Any], path: str, default: Any = None) -> Any:
    """Get nested value from dictionary using dot notation"""
    keys = path.split('.')
    current = data
    
    for key in keys:
        if isinstance(current, dict) and key in current:
            current = current[key]
        else:
            return default
    
    return current

def set_nested_value(data: Dict[str, Any], path: str, value: Any) -> bool:
    """Set nested value in dictionary using dot notation"""
    keys = path.split('.')
    current = data
    
    for key in keys[:-1]:
        if key not in current:
            current[key] = {}
        current = current[key]
    
    current[keys[-1]] = value
    return True

def deep_copy(obj: Any) -> Any:
    """Create a deep copy of an object"""
    if isinstance(obj, dict):
        return {k: deep_copy(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [deep_copy(item) for item in obj]
    else:
        return obj

def format_bytes(bytes_value: int) -> str:
    """Format bytes to human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if bytes_value < 1024.0:
            return f"{bytes_value:.1f} {unit}"
        bytes_value /= 1024.0
    return f"{bytes_value:.1f} TB"

def retry_on_exception(func, max_retries: int = 3, delay: float = 1.0):
    """Decorator to retry function on exception"""
    def wrapper(*args, **kwargs):
        for attempt in range(max_retries):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_retries - 1:
                    raise e
                logger.warning(f"Attempt {attempt + 1} failed: {e}. Retrying...")
                import time
                time.sleep(delay)
    return wrapper

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> List[str]:
    """Validate required fields in data dictionary"""
    missing_fields = []
    for field in required_fields:
        if field not in data or data[field] is None or data[field] == "":
            missing_fields.append(field)
    return missing_fields

def create_error_response(message: str, error_code: str = None, details: Any = None) -> Dict[str, Any]:
    """Create standardized error response"""
    response = {
        "error": True,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if error_code:
        response["error_code"] = error_code
    
    if details:
        response["details"] = details
    
    return response

def create_success_response(data: Any = None, message: str = "Success") -> Dict[str, Any]:
    """Create standardized success response"""
    response = {
        "success": True,
        "message": message,
        "timestamp": datetime.now().isoformat()
    }
    
    if data is not None:
        response["data"] = data
    
    return response 