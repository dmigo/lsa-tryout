import asyncio
import aiohttp
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import time
from datetime import datetime, timedelta
from .crawler import WebCrawler
from .content_analyzer import ContentAnalyzer
from ..utils.data_models import CompetitorAnalysis


class CompetitorTracker:
    """Track and analyze competitors for SEO insights."""

    def __init__(self, max_concurrent: int = 3):
        self.max_concurrent = max_concurrent
        self.content_analyzer = ContentAnalyzer()

    async def analyze_competitors(self, your_domain: str, competitor_domains: List[str],
                                analysis_depth: str = "standard") -> Dict[str, Any]:
        """Comprehensive competitor analysis."""

        # Analyze your own site first
        your_analysis = await self._analyze_single_site(your_domain, is_primary=True)

        # Analyze competitors
        competitor_analyses = {}
        semaphore = asyncio.Semaphore(self.max_concurrent)

        async def analyze_competitor(domain):
            async with semaphore:
                return await self._analyze_single_site(domain, is_primary=False)

        tasks = [analyze_competitor(domain) for domain in competitor_domains[:5]]  # Limit to 5 competitors
        competitor_results = await asyncio.gather(*tasks, return_exceptions=True)

        for domain, result in zip(competitor_domains, competitor_results):
            if not isinstance(result, Exception):
                competitor_analyses[domain] = result

        # Generate competitive insights
        insights = self._generate_competitive_insights(your_analysis, competitor_analyses)

        # Generate recommendations
        recommendations = self._generate_competitive_recommendations(your_analysis, competitor_analyses, insights)

        return {
            'your_site': {
                'domain': your_domain,
                'analysis': your_analysis
            },
            'competitors': competitor_analyses,
            'insights': insights,
            'recommendations': recommendations,
            'analysis_date': datetime.now().isoformat()
        }

    async def _analyze_single_site(self, domain: str, is_primary: bool = False) -> Dict[str, Any]:
        """Analyze a single website for competitive intelligence."""

        if not domain.startswith(('http://', 'https://')):
            domain = f"https://{domain}"

        async with WebCrawler(max_concurrent=2) as crawler:
            # Crawl key pages (homepage + a few important pages)
            crawl_results = await crawler.crawl_website(domain, max_pages=5)

        if not crawl_results:
            return {'error': f'Could not analyze {domain}'}

        # Analyze the homepage (first result)
        homepage = crawl_results[0]
        content_analysis = self.content_analyzer.analyze_content(homepage.content, homepage.url)

        # Technical SEO analysis
        technical_analysis = self._analyze_technical_seo(crawl_results)

        # Content strategy analysis
        content_strategy = self._analyze_content_strategy(crawl_results)

        # AI readiness assessment
        ai_assessment = self._assess_ai_readiness(content_analysis)

        # Authority signals (simulated)
        authority_signals = await self._analyze_authority_signals(domain)

        return {
            'domain': domain,
            'homepage_analysis': content_analysis,
            'technical_seo': technical_analysis,
            'content_strategy': content_strategy,
            'ai_readiness': ai_assessment,
            'authority_signals': authority_signals,
            'overall_score': self._calculate_site_score(content_analysis, technical_analysis, ai_assessment)
        }

    def _analyze_technical_seo(self, crawl_results: List) -> Dict[str, Any]:
        """Analyze technical SEO factors."""
        if not crawl_results:
            return {}

        homepage = crawl_results[0]

        # Page speed (using load time as proxy)
        avg_load_time = sum(result.load_time for result in crawl_results) / len(crawl_results)

        # Title and meta analysis
        has_title = bool(homepage.meta_data.get('title', ''))
        has_meta_desc = 'description' in homepage.meta_data

        # Schema markup detection
        schema_count = int(homepage.meta_data.get('structured_data_count', 0))

        # Heading structure
        heading_counts = {}
        for i in range(1, 7):
            heading_counts[f'h{i}'] = int(homepage.meta_data.get(f'h{i}_count', 0))

        # Mobile-friendliness indicators (simulated)
        mobile_friendly = True  # Would use actual mobile testing in production

        return {
            'avg_load_time': round(avg_load_time, 2),
            'has_title_tag': has_title,
            'has_meta_description': has_meta_desc,
            'schema_markup_count': schema_count,
            'heading_structure': heading_counts,
            'mobile_friendly': mobile_friendly,
            'pages_crawled': len(crawl_results),
            'technical_score': self._calculate_technical_score(
                avg_load_time, has_title, has_meta_desc, schema_count, heading_counts
            )
        }

    def _analyze_content_strategy(self, crawl_results: List) -> Dict[str, Any]:
        """Analyze content strategy and depth."""
        if not crawl_results:
            return {}

        total_words = 0
        total_questions = 0
        total_headings = 0
        content_topics = []

        for result in crawl_results:
            # Word count analysis
            word_count = len(result.content.split())
            total_words += word_count

            # Question detection
            import re
            questions = re.findall(r'\b(?:what|how|why|when|where|who)\b[^.!?]*\?', result.content, re.IGNORECASE)
            total_questions += len(questions)

            # Heading count
            for i in range(1, 7):
                total_headings += int(result.meta_data.get(f'h{i}_count', 0))

            # Extract potential topics from first heading of each page
            first_h1 = result.meta_data.get('h1_first', '')
            if first_h1:
                content_topics.append(first_h1)

        avg_words_per_page = total_words / len(crawl_results) if crawl_results else 0

        return {
            'total_pages_analyzed': len(crawl_results),
            'avg_words_per_page': round(avg_words_per_page),
            'total_questions': total_questions,
            'total_headings': total_headings,
            'content_topics': content_topics,
            'content_depth_score': self._calculate_content_depth_score(
                avg_words_per_page, total_questions, total_headings, len(crawl_results)
            )
        }

    def _assess_ai_readiness(self, content_analysis: Dict) -> Dict[str, Any]:
        """Assess AI search readiness from content analysis."""
        ai_data = content_analysis.get('ai_readiness', {})

        return {
            'ai_optimization_score': ai_data.get('ai_optimization_score', 0),
            'question_count': ai_data.get('question_count', 0),
            'has_faq_structure': ai_data.get('has_faq_structure', False),
            'structured_data_schemas': ai_data.get('structured_data', {}).get('total_schemas', 0),
            'answer_patterns': ai_data.get('answer_patterns', 0),
            'list_patterns': ai_data.get('list_patterns', 0)
        }

    async def _analyze_authority_signals(self, domain: str) -> Dict[str, Any]:
        """Analyze authority signals (simulated data for demo)."""
        # In production, this would integrate with tools like:
        # - Ahrefs API for backlink data
        # - SEMrush API for domain authority
        # - Moz API for domain metrics

        await asyncio.sleep(0.1)  # Simulate API call

        # Mock authority data based on domain
        domain_age_score = hash(domain) % 100
        backlink_score = (hash(domain) * 7) % 100
        content_freshness = (hash(domain) * 13) % 100

        return {
            'domain_authority': round(40 + (domain_age_score * 0.6)),
            'estimated_backlinks': (hash(domain) % 10000) + 100,
            'estimated_referring_domains': (hash(domain) % 1000) + 50,
            'content_freshness_score': content_freshness,
            'social_signals': (hash(domain) % 500) + 10,
            'brand_mentions': (hash(domain) % 200) + 5
        }

    def _generate_competitive_insights(self, your_analysis: Dict, competitor_analyses: Dict) -> Dict[str, Any]:
        """Generate insights from competitive analysis."""
        insights = {
            'content_gaps': [],
            'technical_advantages': [],
            'technical_disadvantages': [],
            'ai_readiness_comparison': {},
            'content_strategy_insights': [],
            'opportunity_areas': []
        }

        if not competitor_analyses:
            return insights

        your_scores = self._extract_scores(your_analysis)

        # Compare scores with competitors
        competitor_scores = {}
        for domain, analysis in competitor_analyses.items():
            competitor_scores[domain] = self._extract_scores(analysis)

        # AI readiness comparison
        your_ai_score = your_scores.get('ai_score', 0)
        competitor_ai_scores = [scores.get('ai_score', 0) for scores in competitor_scores.values()]

        if competitor_ai_scores:
            avg_competitor_ai = sum(competitor_ai_scores) / len(competitor_ai_scores)
            best_competitor_ai = max(competitor_ai_scores)

            insights['ai_readiness_comparison'] = {
                'your_score': your_ai_score,
                'competitor_average': round(avg_competitor_ai, 1),
                'best_competitor': round(best_competitor_ai, 1),
                'performance': 'above average' if your_ai_score > avg_competitor_ai else 'below average'
            }

        # Content strategy insights
        your_content_score = your_scores.get('content_score', 0)
        competitor_content_scores = [scores.get('content_score', 0) for scores in competitor_scores.values()]

        if competitor_content_scores:
            avg_competitor_content = sum(competitor_content_scores) / len(competitor_content_scores)

            if your_content_score < avg_competitor_content:
                insights['content_gaps'].append(
                    f"Content depth below competitor average ({your_content_score} vs {avg_competitor_content:.1f})"
                )

        # Technical advantages/disadvantages
        your_tech_score = your_scores.get('technical_score', 0)
        competitor_tech_scores = [scores.get('technical_score', 0) for scores in competitor_scores.values()]

        if competitor_tech_scores:
            avg_competitor_tech = sum(competitor_tech_scores) / len(competitor_tech_scores)

            if your_tech_score > avg_competitor_tech:
                insights['technical_advantages'].append(
                    f"Technical SEO above average ({your_tech_score} vs {avg_competitor_tech:.1f})"
                )
            else:
                insights['technical_disadvantages'].append(
                    f"Technical SEO below average ({your_tech_score} vs {avg_competitor_tech:.1f})"
                )

        # Opportunity areas
        for domain, scores in competitor_scores.items():
            if scores.get('ai_score', 0) > your_ai_score + 20:
                insights['opportunity_areas'].append(
                    f"AI optimization: {domain} scores significantly higher ({scores['ai_score']} vs {your_ai_score})"
                )

            if scores.get('content_score', 0) > your_content_score + 15:
                insights['opportunity_areas'].append(
                    f"Content strategy: Learn from {domain}'s content approach"
                )

        return insights

    def _generate_competitive_recommendations(self, your_analysis: Dict, competitor_analyses: Dict,
                                           insights: Dict) -> List[Dict[str, Any]]:
        """Generate actionable recommendations based on competitive analysis."""
        recommendations = []

        # AI readiness recommendations
        ai_comparison = insights.get('ai_readiness_comparison', {})
        if ai_comparison.get('performance') == 'below average':
            recommendations.append({
                'category': 'AI Optimization',
                'priority': 'High',
                'title': 'Improve AI Search Readiness',
                'description': f"Your AI score ({ai_comparison.get('your_score', 0)}) is below the competitor average. Focus on FAQ content and structured data.",
                'impact': 'High'
            })

        # Content gap recommendations
        if insights.get('content_gaps'):
            recommendations.append({
                'category': 'Content Strategy',
                'priority': 'Medium',
                'title': 'Address Content Depth Gaps',
                'description': 'Competitors have more comprehensive content. Consider expanding topic coverage and article length.',
                'impact': 'Medium'
            })

        # Technical SEO recommendations
        if insights.get('technical_disadvantages'):
            recommendations.append({
                'category': 'Technical SEO',
                'priority': 'High',
                'title': 'Improve Technical Foundation',
                'description': 'Your technical SEO is lagging behind competitors. Focus on page speed, schema markup, and on-page optimization.',
                'impact': 'High'
            })

        # Specific opportunity recommendations
        for opportunity in insights.get('opportunity_areas', [])[:3]:  # Top 3 opportunities
            recommendations.append({
                'category': 'Competitive Opportunity',
                'priority': 'Medium',
                'title': 'Competitive Gap Analysis',
                'description': opportunity,
                'impact': 'Medium'
            })

        return recommendations

    def _extract_scores(self, analysis: Dict) -> Dict[str, float]:
        """Extract key scores from analysis."""
        return {
            'overall_score': analysis.get('overall_score', 0),
            'ai_score': analysis.get('ai_readiness', {}).get('ai_optimization_score', 0),
            'technical_score': analysis.get('technical_seo', {}).get('technical_score', 0),
            'content_score': analysis.get('content_strategy', {}).get('content_depth_score', 0)
        }

    def _calculate_technical_score(self, load_time: float, has_title: bool, has_meta: bool,
                                 schema_count: int, headings: Dict) -> float:
        """Calculate technical SEO score."""
        score = 0

        # Page speed score (0-25 points)
        if load_time < 2:
            score += 25
        elif load_time < 4:
            score += 15
        else:
            score += 5

        # Basic SEO elements (0-30 points)
        if has_title:
            score += 15
        if has_meta:
            score += 15

        # Schema markup (0-20 points)
        score += min(schema_count * 5, 20)

        # Heading structure (0-25 points)
        h1_count = headings.get('h1', 0)
        if h1_count == 1:
            score += 15
        elif h1_count > 1:
            score += 5

        total_headings = sum(headings.values())
        if total_headings >= 3:
            score += 10

        return round(min(score, 100), 1)

    def _calculate_content_depth_score(self, avg_words: float, questions: int,
                                     headings: int, pages: int) -> float:
        """Calculate content depth score."""
        score = 0

        # Word count score (0-40 points)
        if avg_words >= 1500:
            score += 40
        elif avg_words >= 800:
            score += 30
        elif avg_words >= 300:
            score += 20
        else:
            score += 10

        # Question content (0-30 points)
        score += min(questions * 3, 30)

        # Structure (0-20 points)
        score += min(headings * 2, 20)

        # Content volume (0-10 points)
        score += min(pages * 2, 10)

        return round(min(score, 100), 1)

    def _calculate_site_score(self, content_analysis: Dict, technical_analysis: Dict,
                            ai_assessment: Dict) -> float:
        """Calculate overall site score."""
        content_score = content_analysis.get('overall_score', 0)
        technical_score = technical_analysis.get('technical_score', 0)
        ai_score = ai_assessment.get('ai_optimization_score', 0)

        # Weighted average
        overall_score = (content_score * 0.4 + technical_score * 0.35 + ai_score * 0.25)

        return round(overall_score, 1)