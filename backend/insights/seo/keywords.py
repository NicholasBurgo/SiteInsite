"""
SEO Keyword Coverage & Scoring module.
Deterministic keyword-level SEO metrics without AI/LLM dependencies.
"""
import os
import json
import re
from typing import List, Dict, Any, Optional, Set
from collections import Counter
from urllib.parse import urlparse
from backend.core.types import KeywordMetrics, SiteKeywordSummary, KeywordComparisonEntry, KeywordComparisonSummary, KeywordCoverageSummary
from backend.storage.runs import RunStore


# [SEO_KEYWORDS_PATCH] Updated stopword list
STOPWORDS = {
    "you", "your", "and", "the", "a", "an", "of", "to", "for", "with", "in", "on", "at", "by",
    "we", "our", "us", "they", "them", "it", "is", "are", "be", "this", "that", "these", "those",
    "has", "he", "its", "was", "will", "have", "had", "what", "said", "each", "which", "their",
    "time", "if", "up", "out", "many", "then", "so", "some", "her", "would", "make", "like",
    "into", "him", "two", "more", "very", "after", "words", "long", "than", "first", "been",
    "call", "who", "oil", "sit", "now", "find", "down", "day", "did", "get", "come", "made", "may", "part"
}

# [SEO_KEYWORDS_PATCH] Generic business words that should not be selected alone
GENERIC = {
    "company", "support", "service", "services", "solutions", "products", "product",
    "team", "group", "systems", "business"
}


def normalize_text(text: str) -> str:
    """Normalize text: lowercase, strip punctuation, remove extra whitespace."""
    if not text:
        return ""
    # Lowercase
    text = text.lower()
    # Remove punctuation (keep alphanumeric and spaces)
    text = re.sub(r'[^\w\s]', ' ', text)
    # Normalize whitespace
    text = re.sub(r'\s+', ' ', text)
    return text.strip()


def simple_stem(word: str) -> str:
    """Simple stemming: remove common suffixes."""
    if len(word) <= 3:
        return word
    
    # Remove common suffixes
    suffixes = ['ing', 'ed', 's', 'es', 'ly', 'er', 'est']
    for suffix in suffixes:
        if word.endswith(suffix) and len(word) > len(suffix) + 2:
            return word[:-len(suffix)]
    
    return word


def tokenize(text: str) -> List[str]:
    """Tokenize text into words, normalized and stemmed."""
    normalized = normalize_text(text)
    if not normalized:
        return []
    
    tokens = normalized.split()
    # [SEO_KEYWORDS_PATCH] Filter stopwords and short tokens (keep original tokens for phrase extraction)
    tokens = [simple_stem(t) for t in tokens if t not in STOPWORDS and len(t) > 2]
    return tokens


def extract_ngrams(text: str, min_n: int = 2, max_n: int = 3) -> List[str]:
    """
    [SEO_KEYWORDS_PATCH] Extract n-grams (phrases) from normalized text.
    Returns 2-3 word phrases, normalized and filtered.
    """
    normalized = normalize_text(text)
    if not normalized:
        return []
    
    words = normalized.split()
    if len(words) < min_n:
        return []
    
    phrases = []
    # Extract n-grams of size min_n to max_n
    for n in range(min_n, min(max_n + 1, len(words) + 1)):
        for i in range(len(words) - n + 1):
            phrase_words = words[i:i + n]
            # Filter out stopwords from phrase
            filtered_phrase = [w for w in phrase_words if w.lower() not in STOPWORDS]
            # Only keep phrase if it has at least min_n meaningful words
            if len(filtered_phrase) >= min_n:
                phrase = ' '.join(filtered_phrase)
                # Filter out numeric-only and very short phrases
                if len(phrase) >= 4 and not phrase.replace(' ', '').isdigit():
                    phrases.append(phrase)
    
    return phrases


def extract_slug_from_url(url: str) -> str:
    """Extract slug from URL path."""
    try:
        parsed = urlparse(url)
        path = parsed.path.strip('/')
        if not path:
            return ""
        # Get last segment
        segments = [s for s in path.split('/') if s]
        if segments:
            slug = segments[-1]
            # Remove file extension
            slug = re.sub(r'\.[^.]+$', '', slug)
            return normalize_text(slug)
        return ""
    except Exception:
        return ""


def infer_focus_keywords(run_store: RunStore, max_keywords: int = 20) -> List[str]:
    """
    [SEO_KEYWORDS_PATCH] Infer focus keywords from a run's content.
    
    Strategy:
    1. Extract 2-3 word phrases (n-grams) from titles, H1/H2, nav items
    2. Boost phrases appearing in important locations or multiple pages
    3. Filter out generic words when alone
    4. Prefer phrases over single words
    5. Select top N high-signal keywords
    """
    run_dir = run_store.run_dir
    
    # Load site.json for nav items
    site_file = os.path.join(run_dir, "site.json")
    nav_items = []
    if os.path.exists(site_file):
        try:
            with open(site_file, 'r') as f:
                site_data = json.load(f)
                nav_items = site_data.get("nav", [])
        except Exception:
            pass
    
    # [SEO_KEYWORDS_PATCH] Track phrases and single words separately with scoring
    phrase_scores: Dict[str, Dict[str, Any]] = {}  # phrase -> {score, in_title, in_h1, in_h2, in_nav, page_count}
    single_word_scores: Counter = Counter()
    phrase_page_counts: Dict[str, Set[str]] = {}  # phrase -> set of page URLs
    
    # Load pages_index.json
    pages_index_file = os.path.join(run_dir, "pages_index.json")
    pages_index = []
    if os.path.exists(pages_index_file):
        try:
            with open(pages_index_file, 'r') as f:
                pages_index = json.load(f)
        except Exception:
            pass
    
    # Process pages
    pages_dir = os.path.join(run_dir, "pages")
    if not os.path.exists(pages_dir):
        return []
    
    # [SEO_KEYWORDS_PATCH] Collect phrases and words from all pages
    for filename in os.listdir(pages_dir):
        if not filename.endswith('.json'):
            continue
        
        page_file = os.path.join(pages_dir, filename)
        try:
            with open(page_file, 'r') as f:
                page_data = json.load(f)
            
            url = page_data.get("url", "")
            title = page_data.get("title", "") or ""
            words_data = page_data.get("words", {})
            headings = words_data.get("headings", [])
            
            # Extract H1 and H2
            h1_texts = []
            h2_texts = []
            for h in headings:
                tag = h.get("tag", "").lower() if isinstance(h, dict) else ""
                text = h.get("text", "") if isinstance(h, dict) else str(h)
                if tag == "h1":
                    h1_texts.append(text)
                elif tag == "h2":
                    h2_texts.append(text)
            
            # [SEO_KEYWORDS_PATCH] Extract phrases from titles (highest priority)
            if title:
                title_phrases = extract_ngrams(title)
                for phrase in title_phrases:
                    if phrase not in phrase_scores:
                        phrase_scores[phrase] = {
                            'score': 0,
                            'in_title': False,
                            'in_h1': False,
                            'in_h2': False,
                            'in_nav': False,
                            'page_count': 0
                        }
                    phrase_scores[phrase]['score'] += 10  # High weight for titles
                    phrase_scores[phrase]['in_title'] = True
                    if phrase not in phrase_page_counts:
                        phrase_page_counts[phrase] = set()
                    phrase_page_counts[phrase].add(url)
            
            # [SEO_KEYWORDS_PATCH] Extract phrases from H1
            for h1_text in h1_texts:
                h1_phrases = extract_ngrams(h1_text)
                for phrase in h1_phrases:
                    if phrase not in phrase_scores:
                        phrase_scores[phrase] = {
                            'score': 0,
                            'in_title': False,
                            'in_h1': False,
                            'in_h2': False,
                            'in_nav': False,
                            'page_count': 0
                        }
                    phrase_scores[phrase]['score'] += 8  # High weight for H1
                    phrase_scores[phrase]['in_h1'] = True
                    if phrase not in phrase_page_counts:
                        phrase_page_counts[phrase] = set()
                    phrase_page_counts[phrase].add(url)
            
            # [SEO_KEYWORDS_PATCH] Extract phrases from H2
            for h2_text in h2_texts:
                h2_phrases = extract_ngrams(h2_text)
                for phrase in h2_phrases:
                    if phrase not in phrase_scores:
                        phrase_scores[phrase] = {
                            'score': 0,
                            'in_title': False,
                            'in_h1': False,
                            'in_h2': False,
                            'in_nav': False,
                            'page_count': 0
                        }
                    phrase_scores[phrase]['score'] += 6  # Medium-high weight for H2
                    phrase_scores[phrase]['in_h2'] = True
                    if phrase not in phrase_page_counts:
                        phrase_page_counts[phrase] = set()
                    phrase_page_counts[phrase].add(url)
            
            # [SEO_KEYWORDS_PATCH] Extract phrases from URL slug
            slug = extract_slug_from_url(url)
            if slug:
                slug_phrases = extract_ngrams(slug)
                for phrase in slug_phrases:
                    if phrase not in phrase_scores:
                        phrase_scores[phrase] = {
                            'score': 0,
                            'in_title': False,
                            'in_h1': False,
                            'in_h2': False,
                            'in_nav': False,
                            'page_count': 0
                        }
                    phrase_scores[phrase]['score'] += 5  # Medium weight for slugs
                    if phrase not in phrase_page_counts:
                        phrase_page_counts[phrase] = set()
                    phrase_page_counts[phrase].add(url)
            
            # [SEO_KEYWORDS_PATCH] Also track single words from titles/H1/H2 for fallback
            if title:
                title_tokens = tokenize(title)
                for token in title_tokens:
                    if token.lower() not in GENERIC:  # Skip generic words
                        single_word_scores[token] += 3
            
            for h1_text in h1_texts:
                h1_tokens = tokenize(h1_text)
                for token in h1_tokens:
                    if token.lower() not in GENERIC:
                        single_word_scores[token] += 2
            
            for h2_text in h2_texts:
                h2_tokens = tokenize(h2_text)
                for token in h2_tokens:
                    if token.lower() not in GENERIC:
                        single_word_scores[token] += 1
        
        except Exception:
            continue
    
    # [SEO_KEYWORDS_PATCH] Process nav items for phrases
    def extract_nav_labels(items: List[Any]) -> List[str]:
        """Recursively extract labels from nav items."""
        labels = []
        for item in items:
            if isinstance(item, dict):
                label = item.get("label", "")
                if label:
                    labels.append(label)
                children = item.get("children", [])
                if children:
                    labels.extend(extract_nav_labels(children))
            elif isinstance(item, str):
                labels.append(item)
        return labels
    
    nav_labels = extract_nav_labels(nav_items)
    for label in nav_labels:
        nav_phrases = extract_ngrams(label)
        for phrase in nav_phrases:
            if phrase not in phrase_scores:
                phrase_scores[phrase] = {
                    'score': 0,
                    'in_title': False,
                    'in_h1': False,
                    'in_h2': False,
                    'in_nav': False,
                    'page_count': 0
                }
            phrase_scores[phrase]['score'] += 7  # High weight for nav
            phrase_scores[phrase]['in_nav'] = True
    
    # [SEO_KEYWORDS_PATCH] Update page counts and boost phrases appearing in multiple pages
    for phrase, pages in phrase_page_counts.items():
        if phrase in phrase_scores:
            phrase_scores[phrase]['page_count'] = len(pages)
            # Boost phrases appearing in ≥2 pages
            if len(pages) >= 2:
                phrase_scores[phrase]['score'] += 3
    
    # [SEO_KEYWORDS_PATCH] Boost phrases appearing in titles/headings
    for phrase, data in phrase_scores.items():
        if data['in_title'] or data['in_h1'] or data['in_h2']:
            data['score'] += 2
    
    # [SEO_KEYWORDS_PATCH] Boost longer phrases (up to 3 words)
    for phrase, data in phrase_scores.items():
        word_count = len(phrase.split())
        if word_count == 3:
            data['score'] += 1  # Slight boost for 3-word phrases
    
    # [SEO_KEYWORDS_PATCH] Score and rank candidates
    candidates = []
    
    # Add phrases (prioritized)
    for phrase, data in phrase_scores.items():
        # Filter: remove phrases that are too short or numeric-only
        if len(phrase) < 4 or phrase.replace(' ', '').isdigit():
            continue
        # Filter: remove phrases that are only generic words
        phrase_words = phrase.split()
        if len(phrase_words) == 1 and phrase_words[0].lower() in GENERIC:
            continue
        candidates.append({
            'keyword': phrase,
            'score': data['score'],
            'is_phrase': True,
            'page_count': data['page_count']
        })
    
    # Add single words as fallback (only if no good phrases found)
    if len(candidates) < max_keywords:
        for word, count in single_word_scores.most_common(max_keywords * 2):
            # Filter: skip generic words, short words, numeric-only
            if (word.lower() in GENERIC or 
                len(word) < 3 or 
                word.isdigit() or
                any(c['keyword'] == word for c in candidates)):  # Avoid duplicates
                continue
            candidates.append({
                'keyword': word,
                'score': count,
                'is_phrase': False,
                'page_count': 0
            })
    
    # [SEO_KEYWORDS_PATCH] Sort by: phrase > single word, then by score
    candidates.sort(key=lambda x: (
        not x['is_phrase'],  # Phrases first (False sorts before True)
        -x['score'],  # Higher score first
        -x['page_count']  # More pages first
    ))
    
    # [SEO_KEYWORDS_PATCH] Final filter and cap
    focus_keywords = []
    for candidate in candidates:
        keyword = candidate['keyword']
        # Final checks: length, not numeric-only
        if len(keyword) >= 3 and not keyword.replace(' ', '').isdigit():
            focus_keywords.append(keyword)
        if len(focus_keywords) >= max_keywords:
            break
    
    return focus_keywords


def count_keyword_occurrences(text: str, keyword: str) -> int:
    """Count normalized occurrences of keyword in text."""
    if not text or not keyword:
        return 0
    
    normalized_text = normalize_text(text)
    normalized_keyword = normalize_text(keyword)
    
    # Count occurrences (word boundaries)
    pattern = r'\b' + re.escape(normalized_keyword) + r'\b'
    matches = re.findall(pattern, normalized_text)
    return len(matches)


def compute_keyword_metrics_for_run(
    run_store: RunStore,
    focus_keywords: List[str]
) -> List[KeywordMetrics]:
    """
    Compute per-keyword metrics for a run.
    
    For each focus keyword:
    - Count occurrences across all pages
    - Track title/H1/H2/slug/anchor hits
    - Compute density and scores
    """
    run_dir = run_store.run_dir
    pages_dir = os.path.join(run_dir, "pages")
    
    if not os.path.exists(pages_dir):
        return []
    
    # Load pages_index to get total page count
    pages_index_file = os.path.join(run_dir, "pages_index.json")
    pages_index = []
    if os.path.exists(pages_index_file):
        try:
            with open(pages_index_file, 'r') as f:
                pages_index = json.load(f)
        except Exception:
            pass
    
    total_pages = len(pages_index) if pages_index else 0
    if total_pages == 0:
        # Count pages from directory
        total_pages = len([f for f in os.listdir(pages_dir) if f.endswith('.json')])
    
    if total_pages == 0:
        return []
    
    # Initialize per-keyword accumulators
    keyword_stats: Dict[str, Dict[str, Any]] = {}
    for keyword in focus_keywords:
        keyword_stats[keyword] = {
            'pages_used': 0,
            'total_occurrences': 0,
            'title_hits': 0,
            'h1_hits': 0,
            'h2_hits': 0,
            'slug_hits': 0,
            'anchor_hits': 0,
            'page_densities': [],  # Store density per page
        }
    
    # Process each page
    for filename in os.listdir(pages_dir):
        if not filename.endswith('.json'):
            continue
        
        page_file = os.path.join(pages_dir, filename)
        try:
            with open(page_file, 'r') as f:
                page_data = json.load(f)
            
            url = page_data.get("url", "")
            title = page_data.get("title", "") or ""
            words_data = page_data.get("words", {})
            headings = words_data.get("headings", [])
            text_content = page_data.get("text", "") or ""
            links_data = page_data.get("links", {})
            internal_links = links_data.get("internal", [])
            
            # Extract slug
            slug = extract_slug_from_url(url)
            
            # Extract H1/H2 texts
            h1_texts = []
            h2_texts = []
            for h in headings:
                tag = h.get("tag", "").lower() if isinstance(h, dict) else ""
                text = h.get("text", "") if isinstance(h, dict) else str(h)
                if tag == "h1":
                    h1_texts.append(text)
                elif tag == "h2":
                    h2_texts.append(text)
            
            # Extract anchor texts
            anchor_texts = []
            for link in internal_links:
                if isinstance(link, dict):
                    anchor = link.get("text", "") or link.get("anchor", "")
                    if anchor:
                        anchor_texts.append(anchor)
                elif isinstance(link, str):
                    anchor_texts.append(link)
            
            # Count word count for density calculation
            word_count = len(tokenize(text_content))
            if word_count == 0:
                word_count = 1  # Avoid division by zero
            
            # Process each keyword
            for keyword in focus_keywords:
                stats = keyword_stats[keyword]
                
                # Count occurrences in main text
                occurrences = count_keyword_occurrences(text_content, keyword)
                
                if occurrences > 0:
                    stats['pages_used'] += 1
                    stats['total_occurrences'] += occurrences
                    
                    # Calculate density for this page
                    density = occurrences / word_count
                    stats['page_densities'].append(density)
                
                # Check title
                if title and count_keyword_occurrences(title, keyword) > 0:
                    stats['title_hits'] += 1
                
                # Check H1
                for h1_text in h1_texts:
                    if count_keyword_occurrences(h1_text, keyword) > 0:
                        stats['h1_hits'] += 1
                        break  # Count once per page
                
                # Check H2
                for h2_text in h2_texts:
                    if count_keyword_occurrences(h2_text, keyword) > 0:
                        stats['h2_hits'] += 1
                        break  # Count once per page
                
                # Check slug
                if slug and count_keyword_occurrences(slug, keyword) > 0:
                    stats['slug_hits'] += 1
                
                # Check anchor texts
                for anchor_text in anchor_texts:
                    if count_keyword_occurrences(anchor_text, keyword) > 0:
                        stats['anchor_hits'] += 1
                        break  # Count once per page
        
        except Exception:
            continue
    
    # Compute scores for each keyword
    keyword_metrics = []
    for keyword, stats in keyword_stats.items():
        pages_used = stats['pages_used']
        total_occurrences = stats['total_occurrences']
        title_hits = stats['title_hits']
        h1_hits = stats['h1_hits']
        h2_hits = stats['h2_hits']
        slug_hits = stats['slug_hits']
        anchor_hits = stats['anchor_hits']
        page_densities = stats['page_densities']
        
        # Coverage score: how many pages use this keyword
        coverage_score = clamp_0_100(100.0 * pages_used / total_pages if total_pages > 0 else 0.0)
        
        # On-page score: weighted combination of title/H1/H2/slug/anchor hits
        def normalized(n: int, total: int) -> float:
            """Normalize count to 0-1 range."""
            return min(1.0, n / total) if total > 0 else 0.0
        
        onpage_score_raw = (
            0.3 * normalized(title_hits, total_pages) +
            0.2 * normalized(h1_hits, total_pages) +
            0.2 * normalized(h2_hits, total_pages) +
            0.15 * normalized(slug_hits, total_pages) +
            0.15 * normalized(anchor_hits, total_pages)
        )
        onpage_score = clamp_0_100(onpage_score_raw * 100.0)
        
        # Density score: average density across pages where keyword appears
        avg_density = sum(page_densities) / len(page_densities) if page_densities else 0.0
        density_score = compute_density_score(avg_density)
        
        # Total score: weighted combination
        total_score = round(
            0.3 * coverage_score +
            0.4 * onpage_score +
            0.3 * density_score,
            1
        )
        
        keyword_metrics.append(KeywordMetrics(
            keyword=keyword,
            pages_used=pages_used,
            total_occurrences=total_occurrences,
            title_hits=title_hits,
            h1_hits=h1_hits,
            h2_hits=h2_hits,
            slug_hits=slug_hits,
            anchor_hits=anchor_hits,
            avg_density=round(avg_density, 4),
            coverage_score=round(coverage_score, 1),
            onpage_score=round(onpage_score, 1),
            total_score=total_score
        ))
    
    return keyword_metrics


def compute_density_score(avg_density: float) -> float:
    """
    Compute density score (0-100) based on average keyword density.
    
    Rewards reasonable density (0.5% - 2.5%) and penalizes 0 or obvious stuffing (>5%).
    """
    if avg_density <= 0:
        return 0.0
    
    # Convert to percentage
    density_pct = avg_density * 100
    
    # Optimal range: 0.5% - 2.5%
    if 0.5 <= density_pct <= 2.5:
        # Peak at 1.5%
        if density_pct <= 1.5:
            # Linear from 0.5% (score 50) to 1.5% (score 100)
            return clamp_0_100(50 + (density_pct - 0.5) / 1.0 * 50)
        else:
            # Linear from 1.5% (score 100) to 2.5% (score 80)
            return clamp_0_100(100 - (density_pct - 1.5) / 1.0 * 20)
    
    # Below 0.5%: penalize
    if density_pct < 0.5:
        return clamp_0_100(density_pct / 0.5 * 50)
    
    # Above 2.5%: penalize (keyword stuffing)
    if density_pct > 2.5:
        # Penalize heavily above 5%
        if density_pct >= 5.0:
            return 0.0
        # Linear penalty from 2.5% (score 80) to 5% (score 0)
        return clamp_0_100(80 - (density_pct - 2.5) / 2.5 * 80)
    
    return 50.0  # Fallback


def clamp_0_100(value: float) -> float:
    """Clamp a value to the range [0, 100]."""
    return max(0.0, min(100.0, value))


def compute_keyword_coverage_summary(run_id: str, run_store: RunStore) -> KeywordCoverageSummary:
    """
    [SEO_UNIFIED_SECTION] Compute keyword coverage summary for unified SEO section.
    Returns simplified structure without run_id/domain.
    """
    try:
        # Infer focus keywords
        focus_keywords = infer_focus_keywords(run_store, max_keywords=20)
        
        if not focus_keywords:
            return KeywordCoverageSummary(
                overall_score=0.0,
                focus_keywords=[],
                keyword_metrics=[]
            )
        
        # Compute per-keyword metrics
        keyword_metrics = compute_keyword_metrics_for_run(run_store, focus_keywords)
        
        if not keyword_metrics:
            return KeywordCoverageSummary(
                overall_score=0.0,
                focus_keywords=focus_keywords,
                keyword_metrics=[]
            )
        
        # Compute overall keyword score (weighted average of per-keyword scores)
        total_score_sum = sum(km.total_score for km in keyword_metrics)
        overall_score = round(total_score_sum / len(keyword_metrics), 1) if keyword_metrics else 0.0
        
        return KeywordCoverageSummary(
            overall_score=overall_score,
            focus_keywords=focus_keywords,
            keyword_metrics=keyword_metrics
        )
    
    except Exception as e:
        print(f"Error computing keyword coverage summary for {run_id}: {e}")
        return KeywordCoverageSummary(
            overall_score=0.0,
            focus_keywords=[],
            keyword_metrics=[]
        )


def compute_site_keyword_summary(run_id: str, run_store: RunStore) -> SiteKeywordSummary:
    """
    Compute SEO keyword summary for a single run.
    """
    try:
        # Infer focus keywords
        focus_keywords = infer_focus_keywords(run_store, max_keywords=20)
        
        if not focus_keywords:
            # Return empty summary if no keywords found
            return SiteKeywordSummary(
                run_id=run_id,
                domain=None,
                overall_keyword_score=0.0,
                total_focus_keywords=0,
                keyword_metrics=[]
            )
        
        # Compute per-keyword metrics
        keyword_metrics = compute_keyword_metrics_for_run(run_store, focus_keywords)
        
        if not keyword_metrics:
            return SiteKeywordSummary(
                run_id=run_id,
                domain=None,
                overall_keyword_score=0.0,
                total_focus_keywords=len(focus_keywords),
                keyword_metrics=[]
            )
        
        # Compute overall keyword score (weighted average of per-keyword scores)
        # For v1, weight all keywords equally
        total_score_sum = sum(km.total_score for km in keyword_metrics)
        overall_keyword_score = round(total_score_sum / len(keyword_metrics), 1) if keyword_metrics else 0.0
        
        # Get domain from site.json or baseUrl
        domain = None
        site_file = os.path.join(run_store.run_dir, "site.json")
        if os.path.exists(site_file):
            try:
                with open(site_file, 'r') as f:
                    site_data = json.load(f)
                    base_url = site_data.get("baseUrl")
                    if base_url:
                        parsed = urlparse(base_url)
                        domain = parsed.netloc
            except Exception:
                pass
        
        return SiteKeywordSummary(
            run_id=run_id,
            domain=domain,
            overall_keyword_score=overall_keyword_score,
            total_focus_keywords=len(focus_keywords),
            keyword_metrics=keyword_metrics
        )
    
    except Exception as e:
        # Return empty summary on error
        print(f"Error computing SEO keyword summary for {run_id}: {e}")
        return SiteKeywordSummary(
            run_id=run_id,
            domain=None,
            overall_keyword_score=0.0,
            total_focus_keywords=0,
            keyword_metrics=[]
        )


def compute_keyword_comparison(
    primary_run_id: str,
    competitor_run_ids: List[str],
    run_store_factory: callable
) -> KeywordComparisonSummary:
    """
    Compute keyword comparison between primary run and competitors.
    
    Uses primary run's focus keywords as the universe.
    """
    try:
        # Get primary run's keyword summary
        primary_store = run_store_factory(primary_run_id)
        primary_summary = compute_site_keyword_summary(primary_run_id, primary_store)
        
        focus_keywords = [km.keyword for km in primary_summary.keyword_metrics]
        
        if not focus_keywords:
            return KeywordComparisonSummary(
                focus_keywords=[],
                sites=[],
                overall_scores={},
                per_keyword=[]
            )
        
        # Compute keyword summaries for competitors (only for focus keywords)
        site_summaries = {primary_run_id: primary_summary}
        sites = [primary_run_id]
        
        for comp_run_id in competitor_run_ids:
            try:
                comp_store = run_store_factory(comp_run_id)
                # Compute metrics only for focus keywords
                comp_keyword_metrics = compute_keyword_metrics_for_run(comp_store, focus_keywords)
                
                # Compute overall score for competitor
                if comp_keyword_metrics:
                    comp_total_score = sum(km.total_score for km in comp_keyword_metrics)
                    comp_overall_score = round(comp_total_score / len(comp_keyword_metrics), 1)
                else:
                    comp_overall_score = 0.0
                
                # Create competitor summary
                comp_summary = SiteKeywordSummary(
                    run_id=comp_run_id,
                    domain=None,
                    overall_keyword_score=comp_overall_score,
                    total_focus_keywords=len(focus_keywords),
                    keyword_metrics=comp_keyword_metrics
                )
                
                site_summaries[comp_run_id] = comp_summary
                sites.append(comp_run_id)
            except Exception as e:
                print(f"Error computing keyword summary for competitor {comp_run_id}: {e}")
                continue
        
        # Build overall scores dict
        overall_scores = {
            site_id: site_summaries[site_id].overall_keyword_score
            for site_id in sites
        }
        
        # Build per-keyword comparison
        per_keyword = []
        for keyword in focus_keywords:
            site_scores = {}
            for site_id in sites:
                summary = site_summaries[site_id]
                # Find keyword metric for this keyword
                keyword_metric = next(
                    (km for km in summary.keyword_metrics if km.keyword == keyword),
                    None
                )
                if keyword_metric:
                    site_scores[site_id] = keyword_metric.total_score
                else:
                    site_scores[site_id] = 0.0
            
            per_keyword.append(KeywordComparisonEntry(
                keyword=keyword,
                site_scores=site_scores
            ))
        
        return KeywordComparisonSummary(
            focus_keywords=focus_keywords,
            sites=sites,
            overall_scores=overall_scores,
            per_keyword=per_keyword
        )
    
    except Exception as e:
        print(f"Error computing keyword comparison: {e}")
        return KeywordComparisonSummary(
            focus_keywords=[],
            sites=[],
            overall_scores={},
            per_keyword=[]
        )

