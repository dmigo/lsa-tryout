import asyncio
import aiohttp
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from typing import List, Dict, Set, Optional, Any
import time
import re
from dataclasses import dataclass
from llm_seo_agent.utils.data_models import WebsiteAnalysis


@dataclass
class CrawlResult:
    url: str
    title: str
    content: str
    links: List[str]
    meta_data: Dict[str, str]
    status_code: int
    load_time: float
    error: Optional[str] = None


class WebCrawler:
    """Advanced web crawler for SEO analysis."""

    def __init__(self, max_concurrent: int = 5, delay: float = 1.0):
        self.max_concurrent = max_concurrent
        self.delay = delay
        self.session: Optional[aiohttp.ClientSession] = None
        self.visited_urls: Set[str] = set()

    async def __aenter__(self):
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self.session = aiohttp.ClientSession(
            timeout=timeout,
            headers={
                'User-Agent': 'SEO-Analyzer/1.0 (Educational Research)'
            }
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def crawl_website(self, start_url: str, max_pages: int = 10) -> List[CrawlResult]:
        """Crawl a website starting from the given URL."""
        if not self.session:
            raise RuntimeError("Crawler must be used as async context manager")

        results = []
        urls_to_crawl = [start_url]
        crawled_count = 0

        # Create semaphore for concurrent control
        semaphore = asyncio.Semaphore(self.max_concurrent)

        while urls_to_crawl and crawled_count < max_pages:
            # Get batch of URLs to crawl
            batch_size = min(self.max_concurrent, len(urls_to_crawl), max_pages - crawled_count)
            current_batch = urls_to_crawl[:batch_size]
            urls_to_crawl = urls_to_crawl[batch_size:]

            # Crawl batch concurrently
            tasks = [
                self._crawl_single_page(url, semaphore)
                for url in current_batch
                if url not in self.visited_urls
            ]

            if not tasks:
                break

            batch_results = await asyncio.gather(*tasks, return_exceptions=True)

            for result in batch_results:
                if isinstance(result, CrawlResult) and result.error is None:
                    results.append(result)
                    crawled_count += 1

                    # Extract internal links for further crawling
                    domain = urlparse(start_url).netloc
                    internal_links = [
                        link for link in result.links
                        if urlparse(link).netloc == domain and link not in self.visited_urls
                    ]
                    urls_to_crawl.extend(internal_links[:5])  # Limit new links per page

            # Rate limiting delay
            if urls_to_crawl:
                await asyncio.sleep(self.delay)

        return results

    async def _crawl_single_page(self, url: str, semaphore: asyncio.Semaphore) -> CrawlResult:
        """Crawl a single page and extract data."""
        async with semaphore:
            start_time = time.time()

            try:
                self.visited_urls.add(url)

                async with self.session.get(url) as response:
                    load_time = time.time() - start_time
                    content = await response.text()

                    soup = BeautifulSoup(content, 'html.parser')

                    # Extract page data
                    title = self._extract_title(soup)
                    text_content = self._extract_text_content(soup)
                    links = self._extract_links(soup, url)
                    meta_data = self._extract_meta_data(soup)

                    return CrawlResult(
                        url=url,
                        title=title,
                        content=text_content,
                        links=links,
                        meta_data=meta_data,
                        status_code=response.status,
                        load_time=load_time
                    )

            except Exception as e:
                return CrawlResult(
                    url=url,
                    title="",
                    content="",
                    links=[],
                    meta_data={},
                    status_code=0,
                    load_time=time.time() - start_time,
                    error=str(e)
                )

    def _extract_title(self, soup: BeautifulSoup) -> str:
        """Extract page title."""
        title_tag = soup.find('title')
        return title_tag.get_text().strip() if title_tag else ""

    def _extract_text_content(self, soup: BeautifulSoup) -> str:
        """Extract main text content."""
        # Remove script and style elements
        for script in soup(["script", "style"]):
            script.decompose()

        # Get text content
        text = soup.get_text()

        # Clean up whitespace
        lines = (line.strip() for line in text.splitlines())
        chunks = (phrase.strip() for line in lines for phrase in line.split("  "))
        text = '\n'.join(chunk for chunk in chunks if chunk)

        return text

    def _extract_links(self, soup: BeautifulSoup, base_url: str) -> List[str]:
        """Extract all links from the page."""
        links = []

        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)

            # Filter out non-HTTP links
            if absolute_url.startswith(('http://', 'https://')):
                links.append(absolute_url)

        return list(set(links))  # Remove duplicates

    def _extract_meta_data(self, soup: BeautifulSoup) -> Dict[str, str]:
        """Extract meta data from the page."""
        meta_data = {}

        # Extract meta tags
        for meta in soup.find_all('meta'):
            if meta.get('name'):
                meta_data[meta['name']] = meta.get('content', '')
            elif meta.get('property'):
                meta_data[meta['property']] = meta.get('content', '')

        # Extract structured data
        schema_scripts = soup.find_all('script', type='application/ld+json')
        if schema_scripts:
            meta_data['structured_data_count'] = str(len(schema_scripts))

        # Extract heading structure
        for i in range(1, 7):
            headings = soup.find_all(f'h{i}')
            if headings:
                meta_data[f'h{i}_count'] = str(len(headings))
                meta_data[f'h{i}_first'] = headings[0].get_text().strip()

        return meta_data


class SitemapCrawler:
    """Specialized crawler for XML sitemaps."""

    def __init__(self):
        self.session: Optional[aiohttp.ClientSession] = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'SEO-Analyzer/1.0 (Sitemap Parser)'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def discover_sitemaps(self, domain: str) -> List[str]:
        """Discover sitemap URLs for a domain."""
        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"

        sitemap_urls = []

        # Common sitemap locations
        common_paths = [
            '/sitemap.xml',
            '/sitemap_index.xml',
            '/sitemap.txt',
            '/sitemaps.xml'
        ]

        for path in common_paths:
            url = urljoin(domain, path)
            if await self._check_sitemap_exists(url):
                sitemap_urls.append(url)

        # Check robots.txt for sitemap declarations
        robots_sitemaps = await self._get_sitemaps_from_robots(domain)
        sitemap_urls.extend(robots_sitemaps)

        return list(set(sitemap_urls))

    async def _check_sitemap_exists(self, url: str) -> bool:
        """Check if a sitemap exists at the given URL."""
        try:
            async with self.session.head(url) as response:
                return response.status == 200
        except:
            return False

    async def _get_sitemaps_from_robots(self, domain: str) -> List[str]:
        """Extract sitemap URLs from robots.txt."""
        robots_url = urljoin(domain, '/robots.txt')
        sitemaps = []

        try:
            async with self.session.get(robots_url) as response:
                if response.status == 200:
                    content = await response.text()

                    # Find sitemap declarations
                    for line in content.split('\n'):
                        line = line.strip()
                        if line.lower().startswith('sitemap:'):
                            sitemap_url = line.split(':', 1)[1].strip()
                            sitemaps.append(sitemap_url)

        except:
            pass

        return sitemaps

    async def parse_sitemap(self, sitemap_url: str) -> List[Dict[str, Any]]:
        """Parse an XML sitemap and extract URLs."""
        try:
            async with self.session.get(sitemap_url) as response:
                if response.status != 200:
                    return []

                content = await response.text()
                soup = BeautifulSoup(content, 'xml')

                urls = []

                # Handle sitemap index files
                sitemap_tags = soup.find_all('sitemap')
                if sitemap_tags:
                    for sitemap in sitemap_tags:
                        loc = sitemap.find('loc')
                        if loc:
                            # Recursively parse sub-sitemaps
                            sub_urls = await self.parse_sitemap(loc.get_text())
                            urls.extend(sub_urls)

                # Handle regular sitemap files
                url_tags = soup.find_all('url')
                for url_tag in url_tags:
                    loc = url_tag.find('loc')
                    if loc:
                        url_data = {
                            'url': loc.get_text(),
                            'lastmod': None,
                            'changefreq': None,
                            'priority': None
                        }

                        # Extract additional data if available
                        lastmod = url_tag.find('lastmod')
                        if lastmod:
                            url_data['lastmod'] = lastmod.get_text()

                        changefreq = url_tag.find('changefreq')
                        if changefreq:
                            url_data['changefreq'] = changefreq.get_text()

                        priority = url_tag.find('priority')
                        if priority:
                            url_data['priority'] = priority.get_text()

                        urls.append(url_data)

                return urls

        except Exception as e:
            print(f"Error parsing sitemap {sitemap_url}: {e}")
            return []


class ContentAnalyzer:
    """Analyze content structure and quality."""

    @staticmethod
    def analyze_content_structure(content: str) -> Dict[str, Any]:
        """Analyze content structure for SEO."""
        words = content.split()
        word_count = len(words)

        # Readability metrics
        sentences = re.split(r'[.!?]+', content)
        sentence_count = len([s for s in sentences if s.strip()])
        avg_words_per_sentence = word_count / sentence_count if sentence_count > 0 else 0

        # Question detection for AI optimization
        question_patterns = re.findall(r'\b(?:what|how|why|when|where|who)\b.*?\?', content, re.IGNORECASE)

        # Header structure simulation (would need parsed HTML)
        headers_found = len(re.findall(r'\n[A-Z][^.]*\n', content))

        return {
            'word_count': word_count,
            'sentence_count': sentence_count,
            'avg_words_per_sentence': round(avg_words_per_sentence, 1),
            'question_count': len(question_patterns),
            'has_questions': len(question_patterns) > 0,
            'estimated_headers': headers_found,
            'content_score': ContentAnalyzer._calculate_content_score(
                word_count, len(question_patterns), headers_found
            )
        }

    @staticmethod
    def _calculate_content_score(word_count: int, question_count: int, header_count: int) -> float:
        """Calculate overall content quality score."""
        score = 0

        # Word count score (300-2000 words optimal)
        if 300 <= word_count <= 2000:
            score += 30
        elif word_count > 2000:
            score += 25
        elif word_count > 100:
            score += 15

        # Question score (good for AI)
        if question_count > 0:
            score += min(question_count * 10, 30)

        # Header structure score
        if header_count > 0:
            score += min(header_count * 5, 25)

        # Content depth bonus
        if word_count > 1000 and question_count > 2:
            score += 15

        return min(score, 100)