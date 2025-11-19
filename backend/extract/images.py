import io
import hashlib
from PIL import Image
from backend.crawl.fetch import FetchResponse

async def extract_images(resp: FetchResponse) -> dict:
    """
    Extract metadata from image response.
    """
    try:
        image_file = io.BytesIO(resp.content)
        image = Image.open(image_file)
        
        # Extract metadata
        meta = {
            "format": image.format,
            "mode": image.mode,
            "size": image.size,
            "width": image.width,
            "height": image.height
        }
        
        # Extract EXIF data if available
        exif_data = {}
        if hasattr(image, '_getexif') and image._getexif():
            exif_data = image._getexif()
        
        # Count words (0 for images)
        word_count = 0
        
        # Generate unique pageId from URL
        page_id = hashlib.md5(resp.url.encode()).hexdigest()[:12]
        
        return {
            "summary": {
                "pageId": page_id,
                "url": resp.url,
                "contentType": resp.content_type,
                "title": f"Image ({image.format})",
                "words": word_count,
                "images": 1,
                "links": 0,
                "status": resp.status,
                "path": resp.path,
                "type": "IMG"
            },
            "meta": meta,
            "text": None,
            "htmlExcerpt": None,
            "headings": [],
            "images": [{
                "src": resp.url,
                "alt": "",
                "title": f"Image ({image.format})",
                "width": image.width,
                "height": image.height,
                "format": image.format
            }],
            "links": [],
            "tables": [],
            "structuredData": [],
            "stats": {
                "word_count": word_count,
                "image_count": 1,
                "width": image.width,
                "height": image.height,
                "format": image.format
            }
        }
    except Exception as e:
        print(f"Image extraction error: {e}")
        return _create_error_response(resp, "IMG")

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
            "path": resp.path,
            "type": content_type
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