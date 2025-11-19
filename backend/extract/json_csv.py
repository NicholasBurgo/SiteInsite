import json
import csv
import io
import hashlib
from backend.crawl.fetch import FetchResponse

async def extract_json_csv(resp: FetchResponse) -> dict:
    """
    Extract data from JSON or CSV response.
    """
    try:
        content = resp.content.decode('utf-8', errors='ignore')
        
        if resp.content_type == "application/json":
            return _extract_json(content, resp)
        elif resp.content_type == "text/csv":
            return _extract_csv(content, resp)
        else:
            return _create_error_response(resp, "UNKNOWN")
            
    except Exception as e:
        print(f"JSON/CSV extraction error: {e}")
        return _create_error_response(resp, "JSON/CSV")

def _extract_json(content: str, resp: FetchResponse) -> dict:
    """Extract JSON data."""
    try:
        data = json.loads(content)
        
        # Extract sample data
        sample_data = _get_sample_data(data)
        
        # Count words in string representation
        word_count = len(str(data).split())
        
        # Generate unique pageId from URL
        page_id = hashlib.md5(resp.url.encode()).hexdigest()[:12]
        
        return {
            "summary": {
                "pageId": page_id,
                "url": resp.url,
                "contentType": resp.content_type,
                "title": "JSON Data",
                "words": word_count,
                "images": 0,
                "links": 0,
                "status": resp.status,
                "status_code": resp.status,
                "path": resp.path,
                "type": "JSON",
                "load_time_ms": resp.load_time_ms,
                "content_length_bytes": resp.content_length_bytes
            },
            "meta": {
                "data_type": type(data).__name__,
                "size": len(content)
            },
            "text": str(data)[:5000],  # Truncate for display
            "htmlExcerpt": None,
            "headings": [],
            "images": [],
            "links": [],
            "tables": [],
            "structuredData": [{"type": "json", "data": sample_data}],
            "stats": {
                "word_count": word_count,
                "data_size": len(content),
                "structure_type": type(data).__name__
            }
        }
    except json.JSONDecodeError:
        return _create_error_response(resp, "JSON")

def _extract_csv(content: str, resp: FetchResponse) -> dict:
    """Extract CSV data."""
    try:
        csv_file = io.StringIO(content)
        reader = csv.reader(csv_file)
        rows = list(reader)
        
        if not rows:
            return _create_error_response(resp, "CSV")
        
        # Extract headers
        headers = rows[0] if rows else []
        
        # Extract sample data
        sample_data = rows[:10]  # First 10 rows
        
        # Count words
        word_count = len(content.split())
        
        # Generate unique pageId from URL
        page_id = hashlib.md5(resp.url.encode()).hexdigest()[:12]
        
        return {
            "summary": {
                "pageId": page_id,
                "url": resp.url,
                "contentType": resp.content_type,
                "title": "CSV Data",
                "words": word_count,
                "images": 0,
                "links": 0,
                "status": resp.status,
                "status_code": resp.status,
                "path": resp.path,
                "type": "CSV",
                "load_time_ms": resp.load_time_ms,
                "content_length_bytes": resp.content_length_bytes
            },
            "meta": {
                "row_count": len(rows),
                "column_count": len(headers),
                "headers": headers
            },
            "text": content[:5000],  # Truncate for display
            "htmlExcerpt": None,
            "headings": [],
            "images": [],
            "links": [],
            "tables": [{"headers": headers, "rows": sample_data}],
            "structuredData": [],
            "stats": {
                "word_count": word_count,
                "row_count": len(rows),
                "column_count": len(headers)
            }
        }
    except Exception:
        return _create_error_response(resp, "CSV")

def _get_sample_data(data, max_depth=2, current_depth=0):
    """Get sample data from JSON structure."""
    if current_depth >= max_depth:
        return "..."
    
    if isinstance(data, dict):
        sample = {}
        for key, value in list(data.items())[:5]:  # First 5 keys
            sample[key] = _get_sample_data(value, max_depth, current_depth + 1)
        return sample
    elif isinstance(data, list):
        return [_get_sample_data(item, max_depth, current_depth + 1) for item in data[:5]]
    else:
        return str(data)[:100]  # Truncate long strings

def _create_error_response(resp: FetchResponse, content_type: str) -> dict:
    """Create error response."""
    page_id = hashlib.md5(resp.url.encode()).hexdigest()[:12]
    return {
        "summary": {
            "pageId": page_id,
            "url": resp.url,
            "contentType": resp.content_type,
            "title": None,
            "words": 0,
            "images": 0,
            "links": 0,
            "status": resp.status,
            "status_code": resp.status,
            "path": resp.path,
            "type": content_type,
            "load_time_ms": resp.load_time_ms,
            "content_length_bytes": resp.content_length_bytes
        },
        "meta": {},
        "text": None,
        "htmlExcerpt": None,
        "headings": [],
        "images": [],
        "links": [],
        "tables": [],
        "structuredData": [],
        "stats": {}
    }