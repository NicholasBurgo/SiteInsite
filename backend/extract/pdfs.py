import io
import hashlib
from pypdf import PdfReader
from backend.crawl.fetch import FetchResponse

async def extract_pdf(resp: FetchResponse) -> dict:
    """
    Extract text and metadata from PDF response.
    """
    try:
        pdf_file = io.BytesIO(resp.content)
        reader = PdfReader(pdf_file)
        
        # Extract text
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        # Extract metadata
        meta = {}
        if reader.metadata:
            meta = {
                "title": reader.metadata.get("/Title", ""),
                "author": reader.metadata.get("/Author", ""),
                "subject": reader.metadata.get("/Subject", ""),
                "creator": reader.metadata.get("/Creator", ""),
                "producer": reader.metadata.get("/Producer", ""),
                "creation_date": str(reader.metadata.get("/CreationDate", "")),
                "modification_date": str(reader.metadata.get("/ModDate", ""))
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
                "type": "PDF",
                "load_time_ms": resp.load_time_ms,
                "content_length_bytes": resp.content_length_bytes
            },
            "meta": meta,
            "text": text,
            "htmlExcerpt": None,
            "headings": [],
            "images": [],
            "links": [],
            "tables": [],
            "structuredData": [],
            "stats": {
                "word_count": word_count,
                "page_count": len(reader.pages),
                "image_count": 0,
                "link_count": 0
            }
        }
    except Exception as e:
        print(f"PDF extraction error: {e}")
        return _create_error_response(resp, "PDF")

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