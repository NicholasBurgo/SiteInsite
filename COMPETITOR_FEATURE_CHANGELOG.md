# Competitor Suggestion + Confirmation Flow - Changelog

## Overview
This document details all changes made to implement the hybrid competitor selection flow with suggestion and confirmation UI.

---

## Backend Changes

### 1. New File: `backend/routers/competitors.py`
**Created:** New router for competitor-related endpoints

**Contents:**
- `GET /api/competitors/suggest` endpoint
- Uses `tldextract` to extract root domain from URL
- Returns placeholder competitor suggestions based on domain variations:
  - `{domain}online.com`
  - `{domain}services.com`
  - `{domain}pro.com`
  - `{domain}-official.com`
  - `{domain}-usa.com`
- Includes TODO comments for future enhancements:
  - Replace with real SERP scraping
  - Extract keywords from homepage content
  - Support industry-specific presets
  - Use stored competitor history

**Key Features:**
- Query parameter validation
- Error handling with HTTPException
- Deduplication (filters out primary URL from suggestions)
- Returns maximum 5 suggestions

---

### 2. Modified: `backend/app.py`
**Changes:**
- Added `competitors` to router imports:
  ```python
  from backend.routers import runs, pages, review, confirm, insights, competitors
  ```
- Registered competitors router:
  ```python
  app.include_router(competitors.router, tags=["competitors"])
  ```

---

### 3. Modified: `backend/requirements.txt`
**Changes:**
- Added `tldextract` dependency for domain extraction

**Before:**
```
pdfkit

# System Dependencies:
```

**After:**
```
pdfkit
tldextract

# System Dependencies:
```

---

## Frontend Changes

### 4. Modified: `frontend/src/pages/Generator.tsx`
**Major Changes:**

#### New State Variables:
- `suggested: string[]` - List of suggested competitor URLs
- `selected: string[]` - List of selected competitor URLs
- `customCompetitor: string` - Input value for custom competitor URL
- `fetchingSuggestions: boolean` - Loading state for suggestion fetch
- `comparisonMode: boolean` - Toggle for comparison vs single audit mode

#### New Functions:
- `fetchSuggestions()` - Fetches competitor suggestions from API
  - Auto-selects top 3 suggestions
  - Handles errors gracefully
- `handleAddCustomCompetitor()` - Adds custom competitor URL to selection
  - Validates URL format (must start with 'http')
  - Prevents duplicates
- `handleRunComparison()` - Triggers comparison audit
  - Calls `/api/compare` endpoint
  - Shows loading state and error handling

#### Modified Functions:
- `handleSubmit()` - Updated to handle comparison mode
  - Checks if comparison mode is enabled
  - Routes to comparison flow if competitors are selected
  - Otherwise runs normal single-site audit

#### New UI Components:

1. **Comparison Mode Toggle**
   - Checkbox to enable/disable comparison mode
   - Auto-fetches suggestions when enabled (if URL exists)

2. **Competitor Selection Section** (shown when comparison mode is active)
   - **Header:** "Who do you want to beat?" with motivational copy
   - **Suggest Button:** "Suggest Competitors" (indigo button)
   - **Suggested List:** Checkbox list of suggested competitors
     - Auto-selects top 3
     - Scrollable container (max-height: 48)
     - Hover effects on items
   - **Custom Input:** Text field + "Add" button
     - Enter key support
     - URL validation
     - Disabled state when invalid
   - **Selected Summary:** Blue badge display
     - Shows count of selected competitors
     - Individual remove buttons (×) on each badge

3. **Dynamic Submit Button**
   - **Comparison Mode:** Green "Run Comparison Audit" button
   - **Normal Mode:** Blue "Start Audit" button
   - Disabled states based on URL and selection requirements

**Styling:**
- Uses Tailwind CSS classes consistent with existing design
- Gray background section for competitor selection
- Blue badges for selected competitors
- Indigo button for suggestions
- Green button for comparison action

---

### 5. Modified: `frontend/src/lib/api.ts`
**New Functions Added:**

1. **`suggestCompetitors(url: string)`**
   ```typescript
   export async function suggestCompetitors(url: string) {
     const res = await fetch(`/api/competitors/suggest?url=${encodeURIComponent(url)}`);
     if (!res.ok) {
       throw new Error("Failed to fetch competitor suggestions");
     }
     return res.json();
   }
   ```
   - Encodes URL parameter
   - Returns `{ suggested: string[] }`

2. **`runComparison(primaryUrl: string, competitors: string[])`**
   ```typescript
   export async function runComparison(primaryUrl: string, competitors: string[]) {
     const res = await fetch("/api/compare", {
       method: "POST",
       headers: { "Content-Type": "application/json" },
       body: JSON.stringify({
         primaryUrl,
         competitors
       })
     });
     if (!res.ok) {
       throw new Error("Failed to run comparison");
     }
     return res.json();
   }
   ```
   - POSTs to existing `/api/compare` endpoint
   - Sends `ComparePayload` format

---

## API Endpoints

### New Endpoint: `GET /api/competitors/suggest`
**Query Parameters:**
- `url` (required): Primary website URL

**Response:**
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

**Error Responses:**
- `400`: Invalid URL (could not extract domain)
- `500`: Server error during suggestion generation

### Existing Endpoint Used: `POST /api/compare`
**Request Body:**
```json
{
  "primaryUrl": "https://example.com",
  "competitors": [
    "https://competitor1.com",
    "https://competitor2.com"
  ]
}
```

**Response:**
- Returns `ComparisonReport` (already implemented)

---

## User Flow

1. User enters primary website URL
2. User optionally enables "Compare with competitors" checkbox
3. If enabled:
   - Suggestions are auto-fetched (or user clicks "Suggest Competitors")
   - Top 3 suggestions are auto-selected
   - User can check/uncheck suggested competitors
   - User can add custom competitor URLs
   - Selected competitors are displayed as badges
4. User clicks "Run Comparison Audit" (green button)
5. Comparison pipeline runs for primary + selected competitors
6. Results are returned (currently shows alert; can be enhanced to navigate to results page)

---

## Future Enhancement TODOs

All TODO comments are included in the code for future development:

1. **Backend (`backend/routers/competitors.py`):**
   - Replace placeholder competitor suggestions with real SERP scraping
   - Extract keywords from homepage content and search for competitors
   - Support industry-specific competitor presets
   - Use stored competitor history to track trends over time

2. **Frontend (`frontend/src/pages/Generator.tsx`):**
   - Navigate to comparison results page when available
   - Enhanced error handling and user feedback
   - Save competitor selections for future use

---

## Files Summary

### Created:
- `backend/routers/competitors.py` (74 lines)

### Modified:
- `backend/app.py` (2 changes: import + router registration)
- `backend/requirements.txt` (1 line added: `tldextract`)
- `frontend/src/pages/Generator.tsx` (major UI additions, ~200 lines added)
- `frontend/src/lib/api.ts` (2 new functions, ~25 lines added)

### Total Lines Changed:
- **Backend:** ~80 lines added
- **Frontend:** ~225 lines added
- **Total:** ~305 lines of new/modified code

---

## Testing Checklist

- [ ] Backend endpoint returns suggestions for valid URLs
- [ ] Backend endpoint handles invalid URLs gracefully
- [ ] Frontend fetches and displays suggestions
- [ ] Checkbox selection works correctly
- [ ] Custom competitor input validates URLs
- [ ] Selected competitors display as badges
- [ ] Comparison button is disabled when no competitors selected
- [ ] Comparison API call succeeds with selected competitors
- [ ] Error handling works for failed API calls
- [ ] UI is responsive and matches existing design

---

## Dependencies

### New Backend Dependency:
- `tldextract` - Python library for extracting domain components from URLs

### Installation:
```bash
pip install tldextract
```

Or install all requirements:
```bash
pip install -r backend/requirements.txt
```

---

## Notes

- The competitor suggestion logic is intentionally simple (placeholder) to allow easy replacement with real SERP data later
- The comparison endpoint (`/api/compare`) already existed and was not modified
- The frontend comparison flow currently shows an alert; this can be enhanced to navigate to a dedicated comparison results page
- All styling uses Tailwind CSS classes consistent with the existing design system
- The implementation follows the existing code patterns and structure

