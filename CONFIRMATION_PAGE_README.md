# Confirmation Page - SiteInsite

## Overview

The Confirmation Page provides a comprehensive multi-tab interface for reviewing and confirming extracted website data before packaging and seeding. This page transforms the post-extraction workflow into an organized, user-friendly confirmation process.

## Features

### 🏗️ Multi-Tab Interface

- **Summary Tab**: Run overview with statistics, confidence distribution, and quick actions
- **Business Info Tab**: Sub-tabs for Identity, Services, Contact, and Legal information
- **Assets Tab**: Image and media file previews with categorization
- **Paragraphs Tab**: Page-organized text segments with word counts
- **Navbar Tab**: Full navigation tree with nested menu items
- **Truth Table Tab**: Unified overview of all confirmed values and confidence scores

### ✅ Confirmation System

- Individual field confirmation toggles (✅ / ❌)
- Bulk confirmation actions for high-confidence items
- Real-time confirmation counter in header
- Smart finalize button that warns when no fields are confirmed

### 📊 Persistent Sidebar Summary

- Total extracted fields count
- Confidence distribution (High/Medium/Low)
- Extracted images count
- Last updated timestamp
- Real-time confirmation progress

### 🎨 UI Features

- "Extraction Complete" success banner
- Smooth tab transitions with Tailwind styling
- Responsive grid layouts
- Icon-based navigation with Lucide React
- Color-coded confidence indicators
- Loading states and error handling

## Backend Integration

### New Endpoints

- `GET /api/review/{run_id}/summary` - Aggregated run statistics
- Enhanced draft model with comprehensive extraction data
- Real-time confidence scoring and distribution

### Data Structure

The confirmation page works with the existing `DraftModel` structure:

```typescript
interface DraftModel {
  runId: string;
  business: BusinessProfile;
  services: ItemBase[];
  products: ItemBase[];
  locations: Location[];
  team: ItemBase[];
  media: any[];
  sitemap: NavigationStructure;
  // ... additional fields
}
```

## Usage

1. **Navigate to Confirmation**: After extraction completes, users are directed to `/confirm/{runId}`
2. **Review Data**: Browse through tabs to review extracted information
3. **Confirm Fields**: Use confirmation toggles to mark verified data
4. **Bulk Actions**: Use quick actions to confirm high-confidence items
5. **Finalize**: Click "Finalize & Pack" to save confirmed data for seeding

## File Structure

```
frontend/src/pages/
├── ConfirmPage.tsx          # Main confirmation page
└── tabs/
    ├── SummaryTab.tsx       # Run overview and statistics
    ├── BusinessTab.tsx      # Business information with sub-tabs
    ├── AssetsTab.tsx        # Media and image management
    ├── ParagraphsTab.tsx    # Text content organization
    ├── NavbarTab.tsx        # Navigation structure
    └── TruthTableTab.tsx    # Unified data table
```

## Technical Implementation

- **React Hooks**: useState, useEffect for state management
- **TypeScript**: Full type safety with existing type definitions
- **Tailwind CSS**: Responsive design with consistent styling
- **Lucide React**: Icon library for consistent UI elements
- **FastAPI Integration**: RESTful API calls for data fetching

## Future Enhancements

- Export functionality for confirmed data
- Advanced filtering and search capabilities
- Batch editing for multiple fields
- Integration with seeding pipeline
- Real-time collaboration features
- Advanced confidence scoring algorithms

