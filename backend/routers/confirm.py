"""
Confirmation API router.
Provides endpoints for Prime, Content, and Seed operations.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import List, Dict, Any, Optional
from backend.storage.confirmation import ConfirmationStore
from backend.storage.seed import SeedBuilder
from backend.routers.runs import manager as run_manager

router = APIRouter()


@router.get("/{run_id}/status")
async def get_extraction_status(run_id: str):
    """
    Check if extraction is complete and data is ready for confirmation.
    Returns: { isComplete: bool, hasData: bool, pagesCount: int }
    """
    try:
        # Check if run is still active
        progress = await run_manager.progress(run_id)
        
        # Check if confirmation data exists
        store = ConfirmationStore(run_id)
        pages_index = store.get_pages_index()
        site_data = store.get_site_data()
        
        # Determine if extraction is complete
        # Run is complete when progress is None (run finished and cleaned up) OR when is_complete flag is True
        is_complete = progress is None or progress.get("is_complete", False)
        # Only return hasData=true when extraction is fully complete to avoid showing partial results
        has_data = is_complete and len(pages_index) > 0 and site_data.get("baseUrl")
        
        return {
            "isComplete": is_complete,
            "hasData": has_data,
            "pagesCount": len(pages_index),
            "progress": progress
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error checking extraction status: {str(e)}")


@router.get("/{run_id}/prime")
async def get_prime_data(run_id: str):
    """
    Get prime data (nav, footer, pages index) for confirmation.
    Returns: { nav, footer, pages: [{titleGuess,path,url,status}] }
    """
    try:
        store = ConfirmationStore(run_id)
        
        # Get site data
        site_data = store.get_site_data()
        
        # Get pages index
        pages_index = store.get_pages_index()
        
        return {
            "baseUrl": site_data.get("baseUrl", ""),
            "nav": site_data.get("nav", []),
            "footer": site_data.get("footer", {"columns": [], "socials": [], "contact": {}}),
            "pages": pages_index
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting prime data: {str(e)}")


@router.get("/{run_id}/content")
async def get_page_content(run_id: str, page_path: str = Query(..., description="Page path to get content for")):
    """
    Get structured content for a specific page.
    Returns the single page JSON (media/files/words/links).
    """
    try:
        store = ConfirmationStore(run_id)
        
        # Find page by path
        pages_index = store.get_pages_index()
        page = next((p for p in pages_index if p.get("path") == page_path), None)
        
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        page_id = page.get("pageId")
        content = store.get_page_content(page_id)
        
        if not content:
            raise HTTPException(status_code=404, detail="Page content not found")
        
        return content
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting page content: {str(e)}")


@router.get("/{run_id}/prime/nav")
async def get_navigation(run_id: str):
    """
    Get navigation data specifically.
    Returns: { baseUrl, nav: NavNode[] }
    """
    try:
        store = ConfirmationStore(run_id)
        site_data = store.get_site_data()
        
        return {
            "baseUrl": site_data.get("baseUrl", ""),
            "nav": site_data.get("nav", [])
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting navigation: {str(e)}")


@router.patch("/{run_id}/prime/nav")
async def update_navigation(run_id: str, nav: List[Dict[str, Any]]):
    """
    Update navigation data.
    Input: edited NavNode[] and overwrites site.json.nav
    Validate: each node needs label, href; children optional.
    Preserve order if not provided; regenerate continuous order values.
    """
    try:
        # Validate navigation data
        errors = []
        for i, node in enumerate(nav):
            if not node.get('label'):
                errors.append(f"Node {i}: missing label")
            if not node.get('href'):
                errors.append(f"Node {i}: missing href")
            if not node.get('id'):
                errors.append(f"Node {i}: missing id")
        
        if errors:
            raise HTTPException(status_code=400, detail=f"Validation errors: {'; '.join(errors)}")
        
        # Regenerate order values if not provided
        for i, node in enumerate(nav):
            if 'order' not in node:
                node['order'] = i
            
            # Recursively handle children
            if node.get('children'):
                for j, child in enumerate(node['children']):
                    if 'order' not in child:
                        child['order'] = j
        
        store = ConfirmationStore(run_id)
        store.update_navigation(nav)
        return {"message": "Navigation updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating navigation: {str(e)}")


@router.patch("/{run_id}/prime/footer")
async def update_footer(run_id: str, footer: Dict[str, Any]):
    """
    Update footer data.
    Input: edited footer; persist to site.json
    """
    try:
        store = ConfirmationStore(run_id)
        store.update_footer(footer)
        return {"message": "Footer updated successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating footer: {str(e)}")


@router.patch("/{run_id}/content")
async def update_page_content(run_id: str, page_path: str = Query(..., description="Page path to update"), 
                             content: Dict[str, Any] = None):
    """
    Update page content.
    Allow edits to title, description, media[].alt, remove/add links, etc.
    """
    try:
        store = ConfirmationStore(run_id)
        
        # Find page by path
        pages_index = store.get_pages_index()
        page = next((p for p in pages_index if p.get("path") == page_path), None)
        
        if not page:
            raise HTTPException(status_code=404, detail="Page not found")
        
        page_id = page.get("pageId")
        
        # Update page content
        store.update_page_content(page_id, content)
        
        return {"message": "Page content updated successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating page content: {str(e)}")


@router.post("/{run_id}/seed")
async def generate_seed(run_id: str):
    """
    Generate seed.json using edited site.json + selected/cleaned page files.
    Returns the path to the generated seed.json file.
    """
    try:
        seed_builder = SeedBuilder(run_id)
        seed_path = seed_builder.build_seed()
        
        return {
            "message": "Seed generated successfully",
            "seedPath": seed_path
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating seed: {str(e)}")


@router.patch("/{run_id}/pages/{page_id}/type")
async def update_page_type(run_id: str, page_id: str, page_type_data: Dict[str, Any]):
    """
    Update page_type for a specific page.
    Updates both pages_index.json and the page's JSON file.
    """
    try:
        page_type = page_type_data.get("page_type", "generic")
        
        # Validate page_type
        valid_types = ["article", "landing", "catalog", "product", "media_gallery", "contact", "utility", "generic"]
        if page_type not in valid_types:
            raise HTTPException(status_code=400, detail=f"Invalid page_type. Must be one of: {', '.join(valid_types)}")
        
        store = ConfirmationStore(run_id)
        
        # Update pages_index.json
        pages_index = store.get_pages_index()
        page_found = False
        for page in pages_index:
            if page.get("pageId") == page_id:
                page["page_type"] = page_type
                page_found = True
                break
        
        if not page_found:
            raise HTTPException(status_code=404, detail="Page not found in index")
        
        # Save updated pages_index
        import json
        import os
        pages_index_file = os.path.join(store.run_dir, "pages_index.json")
        with open(pages_index_file, 'w') as f:
            json.dump(pages_index, f, indent=2)
        
        # Also update the page's JSON file if it exists
        page_content = store.get_page_content(page_id)
        if page_content:
            # Update stats.page_type if it exists
            if "stats" not in page_content:
                page_content["stats"] = {}
            page_content["stats"]["page_type"] = page_type
            store.update_page_content(page_id, page_content)
        
        return {"message": "Page type updated successfully", "page_type": page_type}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating page type: {str(e)}")
