/**
 * TypeScript types for confirmation flow.
 * Defines data contracts for Prime, Content, and Seed operations.
 */

export type NavNode = {
  id: string;                 // stable hash of label+href
  label: string;              // exact visual label (trimmed)
  href: string;               // absolute URL (preserve query if present)
  children?: NavNode[];       // nested items
  order?: number;             // original order captured from DOM
  path?: string;              // normalized path (for page matching)
};

export type FooterColumn = {
  heading?: string;
  links: { label: string; href: string }[];
};

export type FooterData = {
  columns: FooterColumn[];
  socials?: { platform: string; url: string; label?: string }[];
  contact?: {
    email?: string;
    phone?: string;
    address?: string;
  };
};

export type PageIndexItem = {
  pageId: string;
  titleGuess?: string;
  path: string;
  url: string;
  status?: number;
  status_code?: number;
  words?: number;
  mediaCount?: number;
  loadTimeMs?: number;
  contentLengthBytes?: number;
};

export type PrimeResponse = {
  baseUrl: string;
  nav: NavNode[];
  footer: FooterData;
  pages: PageIndexItem[];
};

export type MediaItem = {
  url: string;
  alt?: string;
  width?: number;
  height?: number;
};

export type VideoItem = {
  url: string;
  type?: string;
};

export type GifItem = {
  url: string;
};

export type FileItem = {
  url: string;
  type?: string;
  bytes?: number;
  label?: string;
};

export type HeadingItem = {
  tag: string;
  text: string;
};

export type LinkItem = {
  label?: string;
  href: string;
};

export type PageContent = {
  url: string;
  path: string;
  status?: number;
  title?: string;
  description?: string;
  canonical?: string;
  media: {
    images: MediaItem[];
    gifs: GifItem[];
    videos: VideoItem[];
  };
  files: FileItem[];
  words: {
    headings: HeadingItem[];
    paragraphs: string[];
    wordCount: number;
  };
  links: {
    internal: LinkItem[];
    external: LinkItem[];
    broken: { href: string; status?: number }[];
  };
  extractedAt: string;
};

export type UpdateNavigationRequest = NavNode[];

export type UpdateFooterRequest = FooterData;

export type UpdatePageContentRequest = Partial<PageContent>;

export type SeedResponse = {
  message: string;
  seedPath: string;
};

// UI State Types
export type ConfirmationTab = 'prime' | 'content' | 'insights' | 'competitors';

export type PrimeSubTab = 'nav' | 'footer' | 'pages';

export type ContentSubTab = 'media' | 'files' | 'words' | 'links';

export type MediaType = 'images' | 'gifs' | 'videos';

export type LinkType = 'internal' | 'external' | 'broken';

// Form State Types
export type NavEditState = {
  editing: boolean;
  node: NavNode | null;
  parentPath: number[];
};

export type PageEditState = {
  selectedPage: string | null;
  editing: boolean;
  unsavedChanges: boolean;
};

export type MediaEditState = {
  editingAlt: string | null;
  includeExclude: Record<string, boolean>;
};

// API Error Types
export type ApiError = {
  message: string;
  status: number;
  details?: any;
};
