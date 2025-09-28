import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import sqlite3
from dataclasses import dataclass, asdict
import aiofiles


@dataclass
class PerformanceMetric:
    domain: str
    date: datetime
    metric_type: str
    value: float
    metadata: Dict[str, Any] = None


class PerformanceMonitor:
    """Monitor and track SEO performance metrics over time."""

    def __init__(self, storage_path: str = "data/performance"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.db_path = self.storage_path / "performance.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database for performance tracking."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute('''
                CREATE TABLE IF NOT EXISTS performance_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    domain TEXT NOT NULL,
                    date TEXT NOT NULL,
                    metric_type TEXT NOT NULL,
                    value REAL NOT NULL,
                    metadata TEXT,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP
                )
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_domain_date
                ON performance_metrics(domain, date)
            ''')

            conn.execute('''
                CREATE INDEX IF NOT EXISTS idx_metric_type
                ON performance_metrics(metric_type)
            ''')

    async def track_performance(self, domain: str, timeframe: str = "30d") -> Dict[str, Any]:
        """Track and analyze performance over specified timeframe."""

        # Get historical data
        historical_data = self._get_historical_data(domain, timeframe)

        # Simulate current metrics (in production, integrate with real APIs)
        current_metrics = await self._get_current_metrics(domain)

        # Store current metrics
        await self._store_metrics(domain, current_metrics)

        # Analyze trends
        trends = self._analyze_trends(historical_data, current_metrics)

        # Generate insights
        insights = self._generate_performance_insights(trends, current_metrics)

        # Create performance report
        return {
            'domain': domain,
            'timeframe': timeframe,
            'current_metrics': current_metrics,
            'historical_data': historical_data,
            'trends': trends,
            'insights': insights,
            'report_date': datetime.now().isoformat()
        }

    async def _get_current_metrics(self, domain: str) -> Dict[str, Any]:
        """Get current performance metrics (simulated for demo)."""

        # Simulate API calls to various services
        await asyncio.sleep(0.5)

        # Generate realistic but simulated metrics
        base_hash = hash(domain)
        date_factor = datetime.now().day

        return {
            'ai_citations': {
                'count': (base_hash % 100) + date_factor,
                'growth_rate': ((base_hash % 20) - 10) / 100,
                'top_citing_queries': self._generate_sample_queries(domain),
                'ai_platforms': {
                    'chatgpt': (base_hash % 30) + 10,
                    'claude': (base_hash % 25) + 8,
                    'perplexity': (base_hash % 20) + 5,
                    'gemini': (base_hash % 15) + 3
                }
            },
            'organic_traffic': {
                'sessions': (base_hash % 10000) + 1000,
                'pageviews': (base_hash % 50000) + 5000,
                'avg_session_duration': (base_hash % 300) + 60,
                'bounce_rate': ((base_hash % 40) + 30) / 100,
                'conversion_rate': ((base_hash % 5) + 1) / 100
            },
            'search_rankings': {
                'avg_position': round(((base_hash % 50) + 5) / 5, 1),
                'keywords_ranking': (base_hash % 500) + 50,
                'top_10_keywords': (base_hash % 50) + 5,
                'featured_snippets': (base_hash % 20) + 1
            },
            'technical_metrics': {
                'page_speed_score': (base_hash % 30) + 70,
                'core_web_vitals_score': (base_hash % 20) + 80,
                'mobile_usability_score': (base_hash % 15) + 85,
                'crawl_errors': base_hash % 10
            },
            'content_metrics': {
                'pages_indexed': (base_hash % 1000) + 100,
                'content_freshness_score': (base_hash % 30) + 70,
                'duplicate_content_issues': base_hash % 5,
                'schema_markup_coverage': ((base_hash % 80) + 20) / 100
            }
        }

    def _generate_sample_queries(self, domain: str) -> List[str]:
        """Generate sample queries that cite the domain."""
        base_queries = [
            f"best practices for {domain.split('.')[0]}",
            f"how to use {domain.split('.')[0]}",
            f"{domain.split('.')[0]} tutorial",
            f"{domain.split('.')[0]} vs alternatives",
            f"{domain.split('.')[0]} pricing"
        ]

        # Use domain hash to select and modify queries
        domain_hash = hash(domain)
        selected_queries = []

        for i, query in enumerate(base_queries):
            if (domain_hash + i) % 3 == 0:
                selected_queries.append(query)

        return selected_queries[:3]

    async def _store_metrics(self, domain: str, metrics: Dict[str, Any]):
        """Store current metrics in database."""
        current_date = datetime.now().isoformat()

        with sqlite3.connect(self.db_path) as conn:
            # Store AI citations
            ai_data = metrics.get('ai_citations', {})
            conn.execute(
                'INSERT INTO performance_metrics (domain, date, metric_type, value, metadata) VALUES (?, ?, ?, ?, ?)',
                (domain, current_date, 'ai_citations', ai_data.get('count', 0), json.dumps(ai_data))
            )

            # Store organic traffic
            traffic_data = metrics.get('organic_traffic', {})
            conn.execute(
                'INSERT INTO performance_metrics (domain, date, metric_type, value, metadata) VALUES (?, ?, ?, ?, ?)',
                (domain, current_date, 'organic_sessions', traffic_data.get('sessions', 0), json.dumps(traffic_data))
            )

            # Store search rankings
            ranking_data = metrics.get('search_rankings', {})
            conn.execute(
                'INSERT INTO performance_metrics (domain, date, metric_type, value, metadata) VALUES (?, ?, ?, ?, ?)',
                (domain, current_date, 'avg_position', ranking_data.get('avg_position', 0), json.dumps(ranking_data))
            )

            # Store technical metrics
            tech_data = metrics.get('technical_metrics', {})
            conn.execute(
                'INSERT INTO performance_metrics (domain, date, metric_type, value, metadata) VALUES (?, ?, ?, ?, ?)',
                (domain, current_date, 'page_speed', tech_data.get('page_speed_score', 0), json.dumps(tech_data))
            )

    def _get_historical_data(self, domain: str, timeframe: str) -> Dict[str, List]:
        """Get historical performance data from database."""

        # Parse timeframe
        days = int(timeframe.rstrip('d'))
        start_date = (datetime.now() - timedelta(days=days)).isoformat()

        historical_data = {
            'ai_citations': [],
            'organic_sessions': [],
            'avg_position': [],
            'page_speed': []
        }

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            for metric_type in historical_data.keys():
                cursor.execute(
                    'SELECT date, value FROM performance_metrics WHERE domain = ? AND metric_type = ? AND date >= ? ORDER BY date',
                    (domain, metric_type, start_date)
                )

                rows = cursor.fetchall()
                historical_data[metric_type] = [{'date': row[0], 'value': row[1]} for row in rows]

        return historical_data

    def _analyze_trends(self, historical_data: Dict, current_metrics: Dict) -> Dict[str, Any]:
        """Analyze trends from historical data."""
        trends = {}

        # AI citations trend
        ai_history = historical_data.get('ai_citations', [])
        if len(ai_history) >= 2:
            recent_values = [point['value'] for point in ai_history[-7:]]  # Last week
            if len(recent_values) >= 2:
                trend_direction = "up" if recent_values[-1] > recent_values[0] else "down"
                trend_strength = abs(recent_values[-1] - recent_values[0]) / recent_values[0] * 100
            else:
                trend_direction = "stable"
                trend_strength = 0
        else:
            trend_direction = "insufficient_data"
            trend_strength = 0

        trends['ai_citations'] = {
            'direction': trend_direction,
            'strength': round(trend_strength, 1),
            'current_value': current_metrics.get('ai_citations', {}).get('count', 0)
        }

        # Organic traffic trend
        traffic_history = historical_data.get('organic_sessions', [])
        if len(traffic_history) >= 2:
            recent_values = [point['value'] for point in traffic_history[-7:]]
            if len(recent_values) >= 2:
                trend_direction = "up" if recent_values[-1] > recent_values[0] else "down"
                trend_strength = abs(recent_values[-1] - recent_values[0]) / recent_values[0] * 100
            else:
                trend_direction = "stable"
                trend_strength = 0
        else:
            trend_direction = "insufficient_data"
            trend_strength = 0

        trends['organic_traffic'] = {
            'direction': trend_direction,
            'strength': round(trend_strength, 1),
            'current_value': current_metrics.get('organic_traffic', {}).get('sessions', 0)
        }

        # Rankings trend (inverse - lower is better)
        ranking_history = historical_data.get('avg_position', [])
        if len(ranking_history) >= 2:
            recent_values = [point['value'] for point in ranking_history[-7:]]
            if len(recent_values) >= 2:
                trend_direction = "up" if recent_values[-1] < recent_values[0] else "down"  # Inverse
                trend_strength = abs(recent_values[-1] - recent_values[0]) / recent_values[0] * 100
            else:
                trend_direction = "stable"
                trend_strength = 0
        else:
            trend_direction = "insufficient_data"
            trend_strength = 0

        trends['search_rankings'] = {
            'direction': trend_direction,
            'strength': round(trend_strength, 1),
            'current_value': current_metrics.get('search_rankings', {}).get('avg_position', 0)
        }

        return trends

    def _generate_performance_insights(self, trends: Dict, current_metrics: Dict) -> List[Dict[str, Any]]:
        """Generate actionable insights from performance data."""
        insights = []

        # AI citations insights
        ai_trend = trends.get('ai_citations', {})
        if ai_trend.get('direction') == 'up' and ai_trend.get('strength', 0) > 10:
            insights.append({
                'type': 'positive',
                'category': 'AI Citations',
                'title': 'AI Citations Growing',
                'description': f"Your AI citations are trending up by {ai_trend.get('strength', 0):.1f}%. Keep optimizing for question-answer content.",
                'action': 'Continue current AI optimization strategy'
            })
        elif ai_trend.get('direction') == 'down':
            insights.append({
                'type': 'warning',
                'category': 'AI Citations',
                'title': 'AI Citations Declining',
                'description': f"AI citations dropped by {ai_trend.get('strength', 0):.1f}%. Review content structure and FAQ sections.",
                'action': 'Audit and improve AI-friendly content format'
            })

        # Traffic insights
        traffic_trend = trends.get('organic_traffic', {})
        if traffic_trend.get('direction') == 'up':
            insights.append({
                'type': 'positive',
                'category': 'Organic Traffic',
                'title': 'Traffic Growth Detected',
                'description': f"Organic traffic increased by {traffic_trend.get('strength', 0):.1f}%.",
                'action': 'Analyze top-performing content and replicate strategy'
            })

        # Rankings insights
        ranking_trend = trends.get('search_rankings', {})
        if ranking_trend.get('direction') == 'up':  # Up means better rankings (lower position numbers)
            insights.append({
                'type': 'positive',
                'category': 'Search Rankings',
                'title': 'Rankings Improving',
                'description': "Your average search position is improving.",
                'action': 'Continue current SEO strategy'
            })

        # Technical performance insights
        tech_metrics = current_metrics.get('technical_metrics', {})
        page_speed = tech_metrics.get('page_speed_score', 0)

        if page_speed < 70:
            insights.append({
                'type': 'warning',
                'category': 'Technical SEO',
                'title': 'Page Speed Needs Improvement',
                'description': f"Page speed score is {page_speed}/100. This affects both user experience and AI crawler efficiency.",
                'action': 'Optimize images, enable compression, and improve server response time'
            })

        # Content insights
        content_metrics = current_metrics.get('content_metrics', {})
        schema_coverage = content_metrics.get('schema_markup_coverage', 0)

        if schema_coverage < 0.5:
            insights.append({
                'type': 'opportunity',
                'category': 'Content Optimization',
                'title': 'Low Schema Markup Coverage',
                'description': f"Only {schema_coverage*100:.0f}% of your content has schema markup. This limits AI understanding.",
                'action': 'Implement FAQ, Article, and Product schemas on key pages'
            })

        # AI platform distribution insights
        ai_platforms = current_metrics.get('ai_citations', {}).get('ai_platforms', {})
        if ai_platforms:
            total_citations = sum(ai_platforms.values())
            chatgpt_share = ai_platforms.get('chatgpt', 0) / total_citations if total_citations > 0 else 0

            if chatgpt_share > 0.6:
                insights.append({
                    'type': 'info',
                    'category': 'AI Distribution',
                    'title': 'Heavy ChatGPT Citation Dependency',
                    'description': f"ChatGPT accounts for {chatgpt_share*100:.0f}% of your AI citations.",
                    'action': 'Diversify content strategy to appeal to other AI platforms'
                })

        return insights

    async def generate_performance_report(self, domain: str, timeframe: str = "30d") -> str:
        """Generate a formatted performance report."""
        performance_data = await self.track_performance(domain, timeframe)

        report_lines = [
            f"# SEO Performance Report: {domain}",
            f"Report Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"Timeframe: {timeframe}",
            "",
            "## Current Metrics",
            ""
        ]

        # AI Citations section
        ai_data = performance_data['current_metrics'].get('ai_citations', {})
        report_lines.extend([
            "### AI Search Citations",
            f"- Total Citations: {ai_data.get('count', 0)}",
            f"- Growth Rate: {ai_data.get('growth_rate', 0)*100:+.1f}%",
            f"- Top Platforms:",
        ])

        for platform, count in ai_data.get('ai_platforms', {}).items():
            report_lines.append(f"  - {platform.title()}: {count}")

        # Traffic section
        traffic_data = performance_data['current_metrics'].get('organic_traffic', {})
        report_lines.extend([
            "",
            "### Organic Traffic",
            f"- Sessions: {traffic_data.get('sessions', 0):,}",
            f"- Pageviews: {traffic_data.get('pageviews', 0):,}",
            f"- Avg Session Duration: {traffic_data.get('avg_session_duration', 0):.0f}s",
            f"- Bounce Rate: {traffic_data.get('bounce_rate', 0)*100:.1f}%",
        ])

        # Rankings section
        ranking_data = performance_data['current_metrics'].get('search_rankings', {})
        report_lines.extend([
            "",
            "### Search Rankings",
            f"- Average Position: {ranking_data.get('avg_position', 0)}",
            f"- Keywords Ranking: {ranking_data.get('keywords_ranking', 0)}",
            f"- Top 10 Keywords: {ranking_data.get('top_10_keywords', 0)}",
            f"- Featured Snippets: {ranking_data.get('featured_snippets', 0)}",
        ])

        # Insights section
        insights = performance_data.get('insights', [])
        if insights:
            report_lines.extend([
                "",
                "## Key Insights",
                ""
            ])

            for insight in insights:
                emoji = {'positive': '✅', 'warning': '⚠️', 'opportunity': '💡', 'info': 'ℹ️'}.get(insight['type'], '•')
                report_lines.extend([
                    f"### {emoji} {insight['title']}",
                    f"**Category:** {insight['category']}",
                    f"**Description:** {insight['description']}",
                    f"**Recommended Action:** {insight['action']}",
                    ""
                ])

        return "\n".join(report_lines)

    async def export_data(self, domain: str, format: str = "json") -> str:
        """Export performance data in specified format."""
        performance_data = await self.track_performance(domain)

        if format.lower() == "json":
            return json.dumps(performance_data, indent=2, default=str)
        elif format.lower() == "csv":
            return self._convert_to_csv(performance_data)
        else:
            raise ValueError(f"Unsupported export format: {format}")

    def _convert_to_csv(self, data: Dict) -> str:
        """Convert performance data to CSV format."""
        import csv
        import io

        output = io.StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow(['Date', 'Metric', 'Value'])

        # Current metrics
        current_date = datetime.now().strftime('%Y-%m-%d')
        metrics = data.get('current_metrics', {})

        for category, values in metrics.items():
            if isinstance(values, dict):
                for key, value in values.items():
                    if isinstance(value, (int, float)):
                        writer.writerow([current_date, f"{category}_{key}", value])

        return output.getvalue()