/**
 * API client for confirmation operations.
 * Handles Prime, Content, and Seed API calls.
 */

import {
  PrimeResponse,
  PageContent,
  UpdateNavigationRequest,
  UpdateFooterRequest,
  UpdatePageContentRequest,
  SeedResponse,
  ApiError
} from './types.confirm';

const API_BASE = '/api/confirm';

class ConfirmationApiError extends Error {
  constructor(public status: number, message: string, public details?: any) {
    super(message);
    this.name = 'ConfirmationApiError';
  }
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ConfirmationApiError(
      response.status,
      errorData.detail || errorData.message || 'API request failed',
      errorData
    );
  }
  return response.json();
}

export const confirmationApi = {
  /**
   * Check extraction status
   */
  async getExtractionStatus(runId: string): Promise<{ isComplete: boolean; hasData: boolean; pagesCount: number; progress?: any }> {
    const response = await fetch(`${API_BASE}/${runId}/status`);
    return handleResponse(response);
  },

  /**
   * Get prime data (nav, footer, pages index)
   */
  async getPrime(runId: string): Promise<PrimeResponse> {
    const response = await fetch(`${API_BASE}/${runId}/prime`);
    return handleResponse<PrimeResponse>(response);
  },

  /**
   * Get navigation data specifically
   */
  async getNavigation(runId: string): Promise<{ baseUrl: string; nav: any[] }> {
    const response = await fetch(`${API_BASE}/${runId}/prime/nav`);
    return handleResponse<{ baseUrl: string; nav: any[] }>(response);
  },

  /**
   * Get structured content for a specific page
   */
  async getPageContent(runId: string, pagePath: string): Promise<PageContent> {
    const response = await fetch(`${API_BASE}/${runId}/content?page_path=${encodeURIComponent(pagePath)}`);
    return handleResponse<PageContent>(response);
  },

  /**
   * Update navigation data
   */
  async updateNavigation(runId: string, nav: UpdateNavigationRequest): Promise<void> {
    const response = await fetch(`${API_BASE}/${runId}/prime/nav`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(nav)
    });
    await handleResponse(response);
  },

  /**
   * Update footer data
   */
  async updateFooter(runId: string, footer: UpdateFooterRequest): Promise<void> {
    const response = await fetch(`${API_BASE}/${runId}/prime/footer`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(footer)
    });
    await handleResponse(response);
  },

  /**
   * Update page content
   */
  async updatePageContent(
    runId: string, 
    pagePath: string, 
    content: UpdatePageContentRequest
  ): Promise<void> {
    const response = await fetch(`${API_BASE}/${runId}/content?page_path=${encodeURIComponent(pagePath)}`, {
      method: 'PATCH',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(content)
    });
    await handleResponse(response);
  },

  /**
   * Generate seed.json
   */
  async generateSeed(runId: string): Promise<SeedResponse> {
    const response = await fetch(`${API_BASE}/${runId}/seed`, {
      method: 'POST'
    });
    return handleResponse<SeedResponse>(response);
  }
};

// Utility functions for common operations
export const confirmationUtils = {
  /**
   * Find page by path in pages index
   */
  findPageByPath(pages: any[], path: string) {
    return pages.find(page => page.path === path);
  },

  /**
   * Get media count for a page
   */
  getMediaCount(content: PageContent): number {
    return content.media.images.length + content.media.gifs.length + content.media.videos.length;
  },

  /**
   * Check if page has unsaved changes
   */
  hasUnsavedChanges(original: PageContent, current: Partial<PageContent>): boolean {
    // Simple comparison - in a real app you'd want more sophisticated change detection
    return JSON.stringify(original) !== JSON.stringify({ ...original, ...current });
  },

  /**
   * Format file size
   */
  formatFileSize(bytes?: number): string {
    if (!bytes) return 'Unknown size';
    
    const units = ['B', 'KB', 'MB', 'GB'];
    let size = bytes;
    let unitIndex = 0;
    
    while (size >= 1024 && unitIndex < units.length - 1) {
      size /= 1024;
      unitIndex++;
    }
    
    return `${size.toFixed(1)} ${units[unitIndex]}`;
  },

  /**
   * Validate navigation structure
   */
  validateNavigation(nav: any[]): string[] {
    const errors: string[] = [];
    
    const validateNode = (node: any, path: string = ''): void => {
      if (!node.label || node.label.trim() === '') {
        errors.push(`Navigation item at ${path} has empty label`);
      }
      if (!node.href || node.href.trim() === '') {
        errors.push(`Navigation item "${node.label}" has empty href`);
      }
      if (node.children) {
        node.children.forEach((child: any, index: number) => {
          validateNode(child, `${path} > ${node.label}[${index}]`);
        });
      }
    };
    
    nav.forEach((node, index) => {
      validateNode(node, `[${index}]`);
    });
    
    return errors;
  },

  /**
   * Flatten navigation for display
   */
  flattenNavigation(nav: any[], level: number = 0): Array<{ node: any; level: number; path: number[] }> {
    const result: Array<{ node: any; level: number; path: number[] }> = [];
    
    nav.forEach((node, index) => {
      result.push({ node, level, path: [index] });
      if (node.children) {
        const childResults = this.flattenNavigation(node.children, level + 1);
        childResults.forEach(child => {
          child.path = [index, ...child.path];
        });
        result.push(...childResults);
      }
    });
    
    return result;
  },

  /**
   * Apply sorting to navigation nodes (view-only, doesn't mutate original)
   */
  applySort(nodes: any[], mode: 'original' | 'az'): any[] {
    const sortFn = mode === 'original'
      ? (a: any, b: any) => (a.order ?? 0) - (b.order ?? 0)
      : (a: any, b: any) => a.label.localeCompare(b.label, undefined, { sensitivity: 'base' });

    return nodes
      .slice()
      .sort(sortFn)
      .map(n => ({ 
        ...n, 
        children: n.children ? this.applySort(n.children, mode) : undefined 
      }));
  },

  /**
   * Generate a stable ID for a navigation node
   */
  generateNodeId(label: string, href: string): string {
    // Simple hash function - in production you might want something more robust
    const str = label + href;
    let hash = 0;
    for (let i = 0; i < str.length; i++) {
      const char = str.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32-bit integer
    }
    return Math.abs(hash).toString(36);
  }
};

export { ConfirmationApiError };
