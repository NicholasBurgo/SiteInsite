import io
import hashlib
from docx import Document
from backend.crawl.fetch import FetchResponse

async def extract_docx(resp: FetchResponse) -> dict:
    """
    Extract text and metadata from DOCX response.
    """
    try:
        doc_file = io.BytesIO(resp.content)
        doc = Document(doc_file)
        
        # Extract text
        text = ""
        headings = []
        for paragraph in doc.paragraphs:
            text += paragraph.text + "\n"
            
            # Extract headings
            if paragraph.style.name.startswith('Heading'):
                headings.append({
                    "level": int(paragraph.style.name.split()[-1]) if paragraph.style.name.split()[-1].isdigit() else 1,
                    "text": paragraph.text.strip()
                })
        
        # Extract metadata
        meta = {
            "title": doc.core_properties.title or "",
            "author": doc.core_properties.author or "",
            "subject": doc.core_properties.subject or "",
            "keywords": doc.core_properties.keywords or "",
            "created": str(doc.core_properties.created) if doc.core_properties.created else "",
            "modified": str(doc.core_properties.modified) if doc.core_properties.modified else ""
        }
        
        # Count words
        word_count = len(text.split()) if text else 0
        
        # Generate unique pageId from URL
        page_id = hashlib.md5(resp.url.encode()).hexdigest()[:12]
        
        return {
            "summary": {
                "pageId": page_id,
                "url": resp.url,
                "contentType": resp.content_type,
                "title": meta.get("title", ""),
                "words": word_count,
                "images": 0,
                "links": 0,
                "status": resp.status,
                "status_code": resp.status,
                "path": resp.path,
                "type": "DOCX",
                "load_time_ms": resp.load_time_ms,
                "content_length_bytes": resp.content_length_bytes
            },
            "meta": meta,
            "text": text,
            "htmlExcerpt": None,
            "headings": headings,
            "images": [],
            "links": [],
            "tables": [],
            "structuredData": [],
            "stats": {
                "word_count": word_count,
                "heading_count": len(headings),
                "image_count": 0,
                "link_count": 0
            }
        }
    except Exception as e:
        print(f"DOCX extraction error: {e}")
        return _create_error_response(resp, "DOCX")

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