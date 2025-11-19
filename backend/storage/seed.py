"""
Seed generation utilities.
Builds export-ready seed.json from edited site data and page content.
"""
import os
import json
from typing import Dict, Any, List
from backend.storage.confirmation import ConfirmationStore


class SeedBuilder:
    """
    Builds seed.json for site generation.
    Combines edited site.json with selected page files.
    """
    
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.store = ConfirmationStore(run_id)
        self.seed_dir = os.path.join("runs", run_id, "seed")
        
        # Ensure seed directory exists
        os.makedirs(self.seed_dir, exist_ok=True)
    
    def build_seed(self) -> str:
        """
        Build seed.json combining edited site.json + page files.
        Returns path to generated seed.json.
        """
        try:
            # Get site data
            site_data = self.store.get_site_data()
            
            # Get pages index
            pages_index = self.store.get_pages_index()
            
            # Build pages with components
            pages = []
            for page_info in pages_index:
                page_id = page_info.get("pageId")
                page_content = self.store.get_page_content(page_id)
                
                if page_content:
                    page_components = self._build_page_components(page_content)
                    pages.append({
                        "path": page_info.get("path", "/"),
                        "components": page_components
                    })
            
            # Build seed structure
            seed_data = {
                "baseUrl": site_data.get("baseUrl", ""),
                "nav": site_data.get("nav", []),
                "footer": site_data.get("footer", {}),
                "pages": pages
            }
            
            # Save seed.json
            seed_path = os.path.join(self.seed_dir, "seed.json")
            with open(seed_path, 'w') as f:
                json.dump(seed_data, f, indent=2)
            
            return seed_path
            
        except Exception as e:
            raise Exception(f"Error building seed: {str(e)}")
    
    def _build_page_components(self, page_content: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Build page components from structured content.
        Maps content to export-ready components.
        """
        components = []
        
        # Extract content sections
        media = page_content.get("media", {})
        words = page_content.get("words", {})
        files = page_content.get("files", [])
        
        # Determine if this should be a hero section
        images = media.get("images", [])
        headings = words.get("headings", [])
        
        # First component: Hero if we have large media + heading
        if images and headings:
            first_image = images[0]
            first_heading = next((h for h in headings if h.get("tag") == "h1"), headings[0] if headings else None)
            
            if first_image and first_heading:
                hero_component = {
                    "type": "hero",
                    "props": {
                        "heading": first_heading.get("text", ""),
                        "text": words.get("paragraphs", [])[:2],  # First 2 paragraphs
                        "images": [first_image]
                    }
                }
                components.append(hero_component)
        
        # Additional components: sections
        remaining_paragraphs = words.get("paragraphs", [])
        if len(remaining_paragraphs) > 2:
            remaining_paragraphs = remaining_paragraphs[2:]  # Skip paragraphs used in hero
        
        # Group remaining content into sections
        if remaining_paragraphs:
            section_component = {
                "type": "section",
                "props": {
                    "html": "<p>" + "</p><p>".join(remaining_paragraphs) + "</p>"
                }
            }
            components.append(section_component)
        
        # Add media gallery if multiple images
        if len(images) > 1:
            gallery_component = {
                "type": "gallery",
                "props": {
                    "images": images[1:]  # Skip first image used in hero
                }
            }
            components.append(gallery_component)
        
        # Add files section if any files
        if files:
            files_component = {
                "type": "files",
                "props": {
                    "files": files
                }
            }
            components.append(files_component)
        
        # If no components were created, create a basic section
        if not components:
            components.append({
                "type": "section",
                "props": {
                    "html": "<p>Content not available</p>"
                }
            })
        
        return components
    
    def _extract_hero_content(self, page_content: Dict[str, Any]) -> Dict[str, Any]:
        """Extract content suitable for hero component."""
        media = page_content.get("media", {})
        words = page_content.get("words", {})
        
        # Find largest image
        images = media.get("images", [])
        largest_image = None
        if images:
            largest_image = max(images, key=lambda img: (img.get("width", 0) * img.get("height", 0)))
        
        # Find main heading
        headings = words.get("headings", [])
        main_heading = next((h for h in headings if h.get("tag") == "h1"), headings[0] if headings else None)
        
        # Get first few paragraphs
        paragraphs = words.get("paragraphs", [])[:2]
        
        return {
            "heading": main_heading.get("text", "") if main_heading else "",
            "text": paragraphs,
            "images": [largest_image] if largest_image else []
        }
    
    def _create_section_component(self, content: str) -> Dict[str, Any]:
        """Create a section component from HTML content."""
        return {
            "type": "section",
            "props": {
                "html": content
            }
        }
