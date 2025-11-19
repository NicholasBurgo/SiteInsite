"""
Rollup generation for cross-page analysis
"""
from typing import Dict, List, Any, Set
from datetime import datetime
from collections import Counter, defaultdict
import re

from backend.core.types import PageResult, RunRollup, ContactInfo, ServiceInfo, NavItem
from backend.core.utils import extract_emails, extract_phones, clean_text


class RollupGenerator:
    """Generate rollup data from page results"""
    
    def __init__(self):
        pass
    
    async def generate_all_rollups(self, run_id: str, pages: List[PageResult]) -> Dict[str, RunRollup]:
        """Generate all rollup types"""
        rollups = {}
        
        # Generate each rollup type
        rollups['contacts'] = await self._generate_contacts_rollup(pages)
        rollups['services'] = await self._generate_services_rollup(pages)
        rollups['navigation'] = await self._generate_navigation_rollup(pages)
        rollups['images'] = await self._generate_images_rollup(pages)
        rollups['top_paths'] = await self._generate_top_paths_rollup(pages)
        rollups['wordcount_buckets'] = await self._generate_wordcount_rollup(pages)
        rollups['content_types'] = await self._generate_content_types_rollup(pages)
        rollups['errors'] = await self._generate_errors_rollup(pages)
        
        return rollups
    
    async def _generate_contacts_rollup(self, pages: List[PageResult]) -> RunRollup:
        """Generate contact information rollup"""
        all_emails = set()
        all_phones = set()
        all_addresses = set()
        
        for page in pages:
            if page.stats:
                emails = page.stats.get('emails', [])
                phones = page.stats.get('phones', [])
                
                all_emails.update(emails)
                all_phones.update(phones)
                
                # Extract addresses from text (basic pattern)
                addresses = self._extract_addresses(page.text)
                all_addresses.update(addresses)
        
        contact_info = ContactInfo(
            emails=list(all_emails),
            phones=list(all_phones),
            addresses=list(all_addresses)
        )
        
        return RunRollup(
            name='contacts',
            data={
                'emails': contact_info.emails,
                'phones': contact_info.phones,
                'addresses': contact_info.addresses,
                'total_emails': len(contact_info.emails),
                'total_phones': len(contact_info.phones),
                'total_addresses': len(contact_info.addresses)
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _generate_services_rollup(self, pages: List[PageResult]) -> RunRollup:
        """Generate services rollup"""
        services = []
        
        # Common service keywords
        service_keywords = [
            'service', 'services', 'solutions', 'consulting', 'support',
            'maintenance', 'repair', 'installation', 'design', 'development',
            'marketing', 'advertising', 'sales', 'training', 'education'
        ]
        
        service_pages = defaultdict(list)
        
        for page in pages:
            if page.content_type.value == 'html' and page.text:
                text_lower = page.text.lower()
                
                for keyword in service_keywords:
                    if keyword in text_lower:
                        # Extract potential service name from headings
                        service_name = self._extract_service_name(page.headings, keyword)
                        if service_name:
                            service_pages[service_name].append(page.url)
        
        # Convert to ServiceInfo objects
        for service_name, urls in service_pages.items():
            services.append(ServiceInfo(
                name=service_name,
                description=f"Service mentioned on {len(urls)} pages",
                pages=urls,
                confidence=min(1.0, len(urls) / 10.0)  # Confidence based on frequency
            ))
        
        return RunRollup(
            name='services',
            data={
                'services': [{'name': s.name, 'description': s.description, 'pages': s.pages, 'confidence': s.confidence} for s in services],
                'total_services': len(services),
                'top_services': sorted(services, key=lambda x: len(x.pages), reverse=True)[:10]
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _generate_navigation_rollup(self, pages: List[PageResult]) -> RunRollup:
        """Generate navigation rollup"""
        nav_items = defaultdict(lambda: {'text': '', 'url': '', 'level': 0, 'frequency': 0})
        
        for page in pages:
            if page.content_type.value == 'html':
                for link in page.links:
                    if link.is_internal and link.text:
                        key = link.url
                        nav_items[key]['text'] = link.text
                        nav_items[key]['url'] = link.url
                        nav_items[key]['level'] = self._estimate_nav_level(link.url)
                        nav_items[key]['frequency'] += 1
        
        # Convert to NavItem objects
        navigation = []
        for url, data in nav_items.items():
            if data['frequency'] > 1:  # Only include items that appear multiple times
                navigation.append(NavItem(
                    text=data['text'],
                    url=url,
                    level=data['level'],
                    frequency=data['frequency']
                ))
        
        # Sort by frequency and level
        navigation.sort(key=lambda x: (-x.frequency, x.level))
        
        return RunRollup(
            name='navigation',
            data={
                'navigation': [{'text': n.text, 'url': n.url, 'level': n.level, 'frequency': n.frequency} for n in navigation],
                'total_nav_items': len(navigation),
                'top_nav_items': navigation[:20]
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _generate_images_rollup(self, pages: List[PageResult]) -> RunRollup:
        """Generate images rollup"""
        all_images = []
        image_domains = Counter()
        image_types = Counter()
        
        for page in pages:
            for image in page.images:
                all_images.append({
                    'url': image.url,
                    'alt_text': image.alt_text,
                    'width': image.width,
                    'height': image.height,
                    'size_bytes': image.size_bytes,
                    'mime_type': image.mime_type,
                    'page_url': page.url
                })
                
                # Track domains and types
                if image.url:
                    domain = image.url.split('/')[2] if '//' in image.url else 'unknown'
                    image_domains[domain] += 1
                
                if image.mime_type:
                    image_types[image.mime_type] += 1
        
        # Remove duplicates based on URL
        unique_images = []
        seen_urls = set()
        for img in all_images:
            if img['url'] not in seen_urls:
                unique_images.append(img)
                seen_urls.add(img['url'])
        
        return RunRollup(
            name='images',
            data={
                'all_images': unique_images,
                'total_images': len(all_images),
                'unique_images': len(unique_images),
                'image_domains': dict(image_domains.most_common(10)),
                'image_types': dict(image_types.most_common(10)),
                'images_without_alt': len([img for img in unique_images if not img['alt_text']]),
                'large_images': len([img for img in unique_images if img['size_bytes'] and img['size_bytes'] > 1024*1024])
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _generate_top_paths_rollup(self, pages: List[PageResult]) -> RunRollup:
        """Generate top paths rollup"""
        path_counts = Counter()
        path_depths = defaultdict(list)
        
        for page in pages:
            url_parts = page.url.split('/')
            path = '/'.join(url_parts[:4])  # Include domain and first few path segments
            path_counts[path] += 1
            
            depth = len([p for p in url_parts if p])
            path_depths[depth].append(page.url)
        
        top_paths = []
        for path, count in path_counts.most_common(20):
            top_paths.append({
                'path': path,
                'count': count,
                'percentage': count / len(pages) * 100
            })
        
        return RunRollup(
            name='top_paths',
            data={
                'top_paths': top_paths,
                'path_depth_distribution': {depth: len(urls) for depth, urls in path_depths.items()},
                'most_common_path': path_counts.most_common(1)[0] if path_counts else None
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _generate_wordcount_rollup(self, pages: List[PageResult]) -> RunRollup:
        """Generate word count distribution rollup"""
        wordcount_buckets = {
            '0-99': 0,
            '100-499': 0,
            '500-999': 0,
            '1000-1999': 0,
            '2000-4999': 0,
            '5000+': 0
        }
        
        word_counts = []
        
        for page in pages:
            word_count = page.stats.get('word_count', 0) if page.stats else 0
            word_counts.append(word_count)
            
            # Bucket the word count
            if word_count < 100:
                wordcount_buckets['0-99'] += 1
            elif word_count < 500:
                wordcount_buckets['100-499'] += 1
            elif word_count < 1000:
                wordcount_buckets['500-999'] += 1
            elif word_count < 2000:
                wordcount_buckets['1000-1999'] += 1
            elif word_count < 5000:
                wordcount_buckets['2000-4999'] += 1
            else:
                wordcount_buckets['5000+'] += 1
        
        return RunRollup(
            name='wordcount_buckets',
            data={
                'buckets': wordcount_buckets,
                'total_pages': len(pages),
                'average_word_count': sum(word_counts) / len(word_counts) if word_counts else 0,
                'median_word_count': sorted(word_counts)[len(word_counts)//2] if word_counts else 0,
                'max_word_count': max(word_counts) if word_counts else 0,
                'min_word_count': min(word_counts) if word_counts else 0
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _generate_content_types_rollup(self, pages: List[PageResult]) -> RunRollup:
        """Generate content type distribution rollup"""
        content_types = Counter()
        
        for page in pages:
            content_types[page.content_type.value] += 1
        
        return RunRollup(
            name='content_types',
            data={
                'distribution': dict(content_types),
                'total_pages': len(pages),
                'most_common_type': content_types.most_common(1)[0] if content_types else None
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    async def _generate_errors_rollup(self, pages: List[PageResult]) -> RunRollup:
        """Generate error summary rollup"""
        error_counts = Counter()
        error_pages = []
        
        for page in pages:
            if page.error:
                error_counts[page.error] += 1
                error_pages.append({
                    'url': page.url,
                    'error': page.error,
                    'status': page.status
                })
        
        return RunRollup(
            name='errors',
            data={
                'error_counts': dict(error_counts),
                'total_errors': len(error_pages),
                'error_pages': error_pages,
                'error_rate': len(error_pages) / len(pages) * 100 if pages else 0,
                'most_common_error': error_counts.most_common(1)[0] if error_counts else None
            },
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    def _extract_addresses(self, text: str) -> List[str]:
        """Extract addresses from text (basic pattern matching)"""
        addresses = []
        
        # Basic address patterns
        address_patterns = [
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Cir|Court|Ct)',
            r'\d+\s+[A-Za-z\s]+(?:Street|St|Avenue|Ave|Road|Rd|Boulevard|Blvd|Drive|Dr|Lane|Ln|Way|Circle|Cir|Court|Ct),\s*[A-Za-z\s]+,\s*[A-Z]{2}\s+\d{5}'
        ]
        
        for pattern in address_patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            addresses.extend(matches)
        
        return list(set(addresses))  # Remove duplicates
    
    def _extract_service_name(self, headings: List[Dict[str, Any]], keyword: str) -> Optional[str]:
        """Extract service name from headings"""
        for heading in headings:
            if keyword in heading['text'].lower():
                return clean_text(heading['text'])
        return None
    
    def _estimate_nav_level(self, url: str) -> int:
        """Estimate navigation level based on URL depth"""
        path_parts = url.split('/')
        return len([p for p in path_parts if p]) - 1  # Subtract 1 for domain


