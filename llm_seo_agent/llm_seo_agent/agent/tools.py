import asyncio
import aiohttp
import time
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, urljoin
from bs4 import BeautifulSoup
import re
from llm_seo_agent.utils.data_models import ToolResponse, WebsiteAnalysis, CompetitorAnalysis


class SEOTools:
    def __init__(self):
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=30),
            headers={'User-Agent': 'SEO-Agent/1.0 (Educational purposes)'}
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def analyze_website(self, url: str) -> ToolResponse:
        """Comprehensive website analysis for SEO."""
        start_time = time.time()

        try:
            if not url.startswith(('http://', 'https://')):
                url = f"https://{url}"

            async with self.session.get(url) as response:
                if response.status != 200:
                    return ToolResponse(
                        tool_name="analyze_website",
                        success=False,
                        error_message=f"HTTP {response.status}: Could not fetch {url}"
                    )

                html = await response.text()
                soup = BeautifulSoup(html, 'html.parser')

                analysis_data = await self._perform_website_analysis(soup, url)

                execution_time = time.time() - start_time
                return ToolResponse(
                    tool_name="analyze_website",
                    success=True,
                    data=analysis_data,
                    execution_time=execution_time
                )

        except Exception as e:
            return ToolResponse(
                tool_name="analyze_website",
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def _perform_website_analysis(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Perform detailed website analysis."""

        # Basic SEO elements
        title = soup.find('title')
        title_text = title.get_text().strip() if title else None

        meta_desc = soup.find('meta', attrs={'name': 'description'})
        meta_desc_text = meta_desc.get('content', '').strip() if meta_desc else None

        # Heading structure
        h1_tags = [h1.get_text().strip() for h1 in soup.find_all('h1')]
        h2_tags = [h2.get_text().strip() for h2 in soup.find_all('h2')]

        # Content analysis
        content_text = soup.get_text()
        word_count = len(content_text.split())

        # Schema markup detection
        schema_scripts = soup.find_all('script', type='application/ld+json')
        has_schema = len(schema_scripts) > 0

        # Technical SEO checks
        technical_issues = []
        content_suggestions = []

        # Check for common issues
        if not title_text:
            technical_issues.append("Missing title tag")
        elif len(title_text) > 60:
            technical_issues.append("Title tag too long (>60 characters)")

        if not meta_desc_text:
            technical_issues.append("Missing meta description")
        elif len(meta_desc_text) > 160:
            technical_issues.append("Meta description too long (>160 characters)")

        if len(h1_tags) == 0:
            technical_issues.append("No H1 tag found")
        elif len(h1_tags) > 1:
            technical_issues.append("Multiple H1 tags found")

        if word_count < 300:
            content_suggestions.append("Content appears thin (<300 words)")

        # AI readiness assessment
        ai_readiness_factors = {
            'has_clear_headings': len(h1_tags) == 1 and len(h2_tags) > 0,
            'has_meta_description': bool(meta_desc_text),
            'has_schema_markup': has_schema,
            'sufficient_content': word_count >= 300,
            'structured_content': len(h2_tags) >= 2
        }

        ai_readiness_score = sum(ai_readiness_factors.values()) / len(ai_readiness_factors) * 100

        # Content structure analysis for AI
        question_patterns = re.findall(r'\b(?:what|how|why|when|where|who)\b.*?\?', content_text, re.IGNORECASE)
        has_faq_structure = len(question_patterns) > 0

        if not has_faq_structure:
            content_suggestions.append("Consider adding FAQ section for better AI citation potential")

        if not has_schema:
            content_suggestions.append("Add structured data (Schema.org) for better AI understanding")

        return {
            'url': url,
            'title': title_text,
            'meta_description': meta_desc_text,
            'h1_tags': h1_tags,
            'h2_tags': h2_tags,
            'word_count': word_count,
            'has_schema_markup': has_schema,
            'schema_types': [script.get_text() for script in schema_scripts],
            'ai_readiness_score': round(ai_readiness_score, 1),
            'ai_readiness_factors': ai_readiness_factors,
            'technical_issues': technical_issues,
            'content_suggestions': content_suggestions,
            'question_patterns_found': len(question_patterns),
            'has_faq_structure': has_faq_structure
        }

    async def check_ai_citations(self, domain: str, keywords: List[str]) -> ToolResponse:
        """Simulate checking AI citation frequency (placeholder implementation)."""
        start_time = time.time()

        try:
            # This would integrate with real AI search APIs in production
            # For now, we'll simulate the response
            await asyncio.sleep(0.5)  # Simulate API call

            mock_data = {
                'domain': domain,
                'total_citations': 42,
                'keywords_analyzed': keywords,
                'citation_sources': ['ChatGPT', 'Claude', 'Perplexity'],
                'trending_topics': ['AI optimization', 'content strategy'],
                'competitor_comparison': {
                    'your_citations': 42,
                    'average_competitor': 68,
                    'top_competitor': 95
                },
                'recommendations': [
                    'Increase question-answer content format',
                    'Add more authoritative sources and citations',
                    'Improve content depth on trending topics'
                ]
            }

            return ToolResponse(
                tool_name="check_ai_citations",
                success=True,
                data=mock_data,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResponse(
                tool_name="check_ai_citations",
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    async def compare_competitors(self, your_site: str, competitor_sites: List[str]) -> ToolResponse:
        """Compare your site against competitors."""
        start_time = time.time()

        try:
            results = {}

            # Analyze your site
            your_analysis = await self.analyze_website(your_site)
            if not your_analysis.success:
                return your_analysis

            results['your_site'] = your_analysis.data

            # Analyze competitors
            results['competitors'] = {}
            for competitor in competitor_sites[:3]:  # Limit to 3 competitors
                comp_analysis = await self.analyze_website(competitor)
                if comp_analysis.success:
                    results['competitors'][competitor] = comp_analysis.data

            # Generate comparison insights
            insights = self._generate_competitive_insights(results)

            return ToolResponse(
                tool_name="compare_competitors",
                success=True,
                data={
                    'analysis_results': results,
                    'competitive_insights': insights
                },
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResponse(
                tool_name="compare_competitors",
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )

    def _generate_competitive_insights(self, results: Dict) -> Dict[str, Any]:
        """Generate insights from competitive analysis."""
        your_data = results['your_site']
        competitors = results['competitors']

        insights = {
            'content_gaps': [],
            'technical_advantages': [],
            'improvement_opportunities': []
        }

        your_word_count = your_data.get('word_count', 0)
        your_ai_score = your_data.get('ai_readiness_score', 0)

        competitor_scores = []
        competitor_word_counts = []

        for comp_url, comp_data in competitors.items():
            comp_score = comp_data.get('ai_readiness_score', 0)
            comp_word_count = comp_data.get('word_count', 0)

            competitor_scores.append(comp_score)
            competitor_word_counts.append(comp_word_count)

            # Check for schema markup advantages
            if comp_data.get('has_schema_markup') and not your_data.get('has_schema_markup'):
                insights['improvement_opportunities'].append(
                    f"Competitor {comp_url} uses schema markup - consider implementing"
                )

            # Check content length
            if comp_word_count > your_word_count * 1.5:
                insights['content_gaps'].append(
                    f"Competitor has significantly more content ({comp_word_count} vs {your_word_count} words)"
                )

        # Overall performance comparison
        if competitor_scores:
            avg_competitor_score = sum(competitor_scores) / len(competitor_scores)
            if your_ai_score < avg_competitor_score:
                insights['improvement_opportunities'].append(
                    f"Your AI readiness score ({your_ai_score}%) is below competitor average ({avg_competitor_score:.1f}%)"
                )
            else:
                insights['technical_advantages'].append(
                    f"Your AI readiness score ({your_ai_score}%) exceeds competitor average"
                )

        return insights

    async def track_performance(self, domain: str, timeframe: str = "30d") -> ToolResponse:
        """Track SEO performance over time (placeholder implementation)."""
        start_time = time.time()

        try:
            # Simulate performance tracking data
            await asyncio.sleep(0.3)

            mock_performance = {
                'domain': domain,
                'timeframe': timeframe,
                'metrics': {
                    'ai_citations': {
                        'current': 42,
                        'previous': 38,
                        'change_percent': 10.5
                    },
                    'organic_traffic': {
                        'current': 5420,
                        'previous': 4980,
                        'change_percent': 8.8
                    },
                    'avg_position': {
                        'current': 12.3,
                        'previous': 14.1,
                        'change_percent': -12.8
                    }
                },
                'trending_keywords': [
                    'AI search optimization',
                    'content strategy',
                    'schema markup'
                ],
                'performance_summary': 'Showing positive growth in AI citations and organic traffic'
            }

            return ToolResponse(
                tool_name="track_performance",
                success=True,
                data=mock_performance,
                execution_time=time.time() - start_time
            )

        except Exception as e:
            return ToolResponse(
                tool_name="track_performance",
                success=False,
                error_message=str(e),
                execution_time=time.time() - start_time
            )