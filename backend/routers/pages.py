"""
API routes for page listing and detail retrieval.
"""
from fastapi import APIRouter, HTTPException, Query
from backend.storage.runs import RunStore
from backend.core.types import PageSummary, PageDetail

router = APIRouter()


@router.get("/{run_id}", response_model=list[PageSummary])
async def list_pages(
    run_id: str,
    page: int = 1,
    size: int = 50,
    q: str | None = None,
    type: str | None = None,
    minText: int = 0
):
    """
    List pages for a given run with optional filtering and pagination.
    
    Args:
        run_id: Unique identifier for the audit run
        page: Page number for pagination (1-indexed)
        size: Number of items per page
        q: Search query string to filter pages
        type: Content type filter (html, pdf, docx, etc.)
        minText: Minimum word count filter
    
    Returns:
        list[PageSummary]: List of page summaries matching the filters
    """
    store = RunStore(run_id)
    return store.list_pages(page=page, size=size, q=q, type_filter=type, min_words=minText)


@router.get("/{run_id}/{page_id}", response_model=PageDetail)
async def get_page(run_id: str, page_id: str):
    """
    Get detailed information for a specific page.
    
    Args:
        run_id: Unique identifier for the audit run
        page_id: Unique identifier for the page
    
    Returns:
        PageDetail: Detailed page information including content, metadata, and statistics
    
    Raises:
        HTTPException: 404 if page not found
    """
    store = RunStore(run_id)
    item = store.get_page(page_id)
    if not item:
        raise HTTPException(status_code=404, detail="Page not found")
    return item

