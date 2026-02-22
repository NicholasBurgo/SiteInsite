"""
Competitor suggestion API routes.
"""
import tldextract
from fastapi import APIRouter, HTTPException, Query

router = APIRouter()

@router.get("/api/competitors/suggest")
async def suggest_competitors(url: str = Query(..., description="Primary website URL to suggest competitors for")):
    """
    Returns a list of suggested competitor URLs based on a domain.
    
    For now, uses placeholder logic based on simple domain variations.
    Later will be replaced with:
    - Google SERP results for brand keywords
    - Keyword-based competitor mining
    - Category classifiers
    - SimilarWeb/Ahrefs APIs
    
    **Example Request:**
    ```
    GET /api/competitors/suggest?url=https://example.com
    ```
    
    **Example Response:**
    ```json
    {
      "suggested": [
        "https://exampleonline.com",
        "https://exampleservices.com",
        "https://examplepro.com",
        "https://example-official.com",
        "https://example-usa.com"
      ]
    }
    ```
    """
    try:
        # Extract root domain
        ext = tldextract.extract(url)
        root = ext.domain
        
        if not root:
            raise HTTPException(
                status_code=400,
                detail="Invalid URL: could not extract domain"
            )
        
        # Naive competitor guessing using simple domain variations.
        suggestions = [
            f"https://{root}online.com",
            f"https://{root}services.com",
            f"https://{root}pro.com",
            f"https://{root}-official.com",
            f"https://{root}-usa.com",
        ]
        
        # Deduplicate + strip primary
        filtered = [s for s in suggestions if url not in s]
        
        return {"suggested": filtered[:5]}
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating competitor suggestions: {str(e)}"
        )

