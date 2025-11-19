"""
Review API routes for audit review workflow.
"""

import os
import json
from fastapi import APIRouter, HTTPException, Response
from backend.core.types import DraftModel, ConfirmRequest
from backend.extract.aggregate import build_draft_model
from backend.storage.runs import RunStore

router = APIRouter()

@router.get("/{run_id}/draft", response_model=DraftModel)
async def get_draft(run_id: str):
    """
    Get the aggregated draft model for a run.
    
    This endpoint analyzes all extracted pages and builds a structured
    business model with services, locations, team, etc.
    
    **Example Response:**
    ```json
    {
      "runId": "1761075695",
      "business": {
        "name": "Example Business",
        "tagline": "Your trusted partner",
        "phones": ["+1-555-123-4567"],
        "emails": ["info@example.com"],
        "socials": {"facebook": "https://facebook.com/example"},
        "logo": "https://example.com/logo.png",
        "brand_colors": ["#3b82f6", "#1f2937"],
        "sources": ["abc123", "def456"]
      },
      "services": [
        {
          "id": "svc1",
          "title": "Web Development",
          "description": "Custom web solutions",
          "confidence": 0.85,
          "sources": ["abc123"]
        }
      ],
      "locations": [
        {
          "id": "loc1",
          "name": "Main Office",
          "address": "123 Main St, City, State",
          "phone": "+1-555-123-4567",
          "confidence": 0.9,
          "sources": ["abc123"]
        }
      ],
      "sitemap": {
        "primary": [
          {"label": "Home", "href": "/"},
          {"label": "Services", "href": "/services"}
        ],
        "secondary": [],
        "footer": []
      }
    }
    ```
    """
    try:
        # Check if run exists
        store = RunStore(run_id)
        if not os.path.exists(store.run_dir):
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Build draft model
        draft = await build_draft_model(run_id)
        return draft
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error building draft: {str(e)}")

@router.post("/{run_id}/confirm")
async def confirm_draft(run_id: str, request: ConfirmRequest):
    """
    Confirm and save the edited draft model.
    
    This endpoint validates the draft model and saves it as confirmed.json
    in the run directory for later packaging/seeding.
    
    **Request Body:**
    ```json
    {
      "draft": {
        "runId": "1761075695",
        "business": {
          "name": "Example Business",
          "tagline": "Your trusted partner",
          "phones": ["+1-555-123-4567"],
          "emails": ["info@example.com"],
          "socials": {"facebook": "https://facebook.com/example"},
          "logo": "https://example.com/logo.png",
          "brand_colors": ["#3b82f6", "#1f2937"],
          "sources": ["abc123", "def456"]
        },
        "services": [
          {
            "id": "svc1",
            "title": "Web Development",
            "description": "Custom web solutions",
            "confidence": 0.85,
            "sources": ["abc123"]
          }
        ],
        "locations": [
          {
            "id": "loc1",
            "name": "Main Office",
            "address": "123 Main St, City, State",
            "phone": "+1-555-123-4567",
            "confidence": 0.9,
            "sources": ["abc123"]
          }
        ],
        "sitemap": {
          "primary": [
            {"label": "Home", "href": "/"},
            {"label": "Services", "href": "/services"}
          ],
          "secondary": [],
          "footer": []
        }
      }
    }
    ```
    
    **Response:**
    ```json
    {
      "success": true,
      "message": "Draft confirmed and saved",
      "runId": "1761075695",
      "confirmedAt": "2025-01-21T12:00:00Z"
    }
    ```
    """
    try:
        # Check if run exists
        store = RunStore(run_id)
        if not os.path.exists(store.run_dir):
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Validate draft model
        draft = request.draft
        
        # Basic validation
        if not draft.business.name:
            raise HTTPException(status_code=400, detail="Business name is required")
        
        if draft.runId != run_id:
            raise HTTPException(status_code=400, detail="Run ID mismatch")
        
        # Save confirmed draft
        confirmed_file = os.path.join(store.run_dir, "confirmed.json")
        
        with open(confirmed_file, 'w') as f:
            json.dump(draft.dict(), f, indent=2)
        
        return {
            "success": True,
            "message": "Draft confirmed and saved",
            "runId": run_id,
            "confirmedAt": json.dumps({"timestamp": "now"})  # Would use actual timestamp
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error confirming draft: {str(e)}")

@router.get("/{run_id}/confirmed")
async def get_confirmed(run_id: str):
    """
    Get the confirmed draft model if it exists.
    """
    try:
        store = RunStore(run_id)
        confirmed_file = os.path.join(store.run_dir, "confirmed.json")
        
        if not os.path.exists(confirmed_file):
            raise HTTPException(status_code=404, detail="No confirmed draft found")
        
        with open(confirmed_file, 'r') as f:
            confirmed_data = json.load(f)
        
        return confirmed_data
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error loading confirmed draft: {str(e)}")

@router.get("/{run_id}/summary")
async def get_run_summary(run_id: str):
    """
    Get aggregated run statistics and summary information.
    
    **Example Response:**
    ```json
    {
      "runId": "1761075695",
      "status": "completed",
      "startedAt": "2025-01-21T12:00:00Z",
      "completedAt": "2025-01-21T12:05:00Z",
      "runtime": "5m 0s",
      "pages": {
        "total": 15,
        "successful": 14,
        "failed": 1,
        "types": {
          "html": 12,
          "pdf": 2,
          "docx": 1
        }
      },
      "extraction": {
        "totalFields": 45,
        "highConfidence": 32,
        "mediumConfidence": 10,
        "lowConfidence": 3,
        "services": 8,
        "products": 12,
        "locations": 2,
        "teamMembers": 5,
        "images": 23,
        "words": 15420
      },
      "errors": [
        {
          "url": "https://example.com/broken-page",
          "error_type": "fetch_failed",
          "timestamp": "2025-01-21T12:03:00Z"
        }
      ],
      "confidence": {
        "average": 0.78,
        "distribution": {
          "high": 32,
          "medium": 10,
          "low": 3
        }
      }
    }
    ```
    """
    try:
        # Check if run exists
        store = RunStore(run_id)
        if not os.path.exists(store.run_dir):
            raise HTTPException(status_code=404, detail="Run not found")
        
        # Load run metadata
        meta_file = os.path.join(store.run_dir, "meta.json")
        meta_data = {}
        if os.path.exists(meta_file):
            with open(meta_file, 'r') as f:
                meta_data = json.load(f)
        
        # Build draft model to get extraction stats
        draft = await build_draft_model(run_id)
        
        # Calculate statistics
        total_fields = len(draft.services) + len(draft.products) + len(draft.locations) + len(draft.team)
        high_confidence = sum(1 for item in draft.services + draft.products + draft.locations + draft.team if item.confidence > 0.8)
        medium_confidence = sum(1 for item in draft.services + draft.products + draft.locations + draft.team if 0.5 < item.confidence <= 0.8)
        low_confidence = sum(1 for item in draft.services + draft.products + draft.locations + draft.team if item.confidence <= 0.5)
        
        # Calculate average confidence
        all_confidences = [item.confidence for item in draft.services + draft.products + draft.locations + draft.team]
        avg_confidence = sum(all_confidences) / len(all_confidences) if all_confidences else 0
        
        # Calculate total words (mock calculation)
        total_words = sum(len(item.description or '') for item in draft.services + draft.products + draft.team)
        
        # Calculate runtime
        started_at = meta_data.get('started_at', 0)
        completed_at = meta_data.get('completed_at', started_at)
        runtime_seconds = completed_at - started_at
        runtime_str = f"{int(runtime_seconds // 60)}m {int(runtime_seconds % 60)}s"

        performance_summary = meta_data.get("pageLoad", {}).get("summary", {})
        
        return {
            "runId": run_id,
            "status": meta_data.get('status', 'unknown'),
            "startedAt": meta_data.get('started_at'),
            "completedAt": meta_data.get('completed_at'),
            "runtime": runtime_str,
            "performance": performance_summary,
            "pages": {
                "total": len(meta_data.get('pages', [])),
                "successful": len(meta_data.get('pages', [])),
                "failed": len(meta_data.get('errors', [])),
                "types": {
                    "html": len(meta_data.get('pages', [])),
                    "pdf": 0,
                    "docx": 0
                }
            },
            "extraction": {
                "totalFields": total_fields,
                "highConfidence": high_confidence,
                "mediumConfidence": medium_confidence,
                "lowConfidence": low_confidence,
                "services": len(draft.services),
                "products": len(draft.products),
                "locations": len(draft.locations),
                "teamMembers": len(draft.team),
                "images": len(draft.media),
                "words": total_words
            },
            "errors": meta_data.get('errors', []),
            "confidence": {
                "average": round(avg_confidence, 2),
                "distribution": {
                    "high": high_confidence,
                    "medium": medium_confidence,
                    "low": low_confidence
                }
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating summary: {str(e)}")                        