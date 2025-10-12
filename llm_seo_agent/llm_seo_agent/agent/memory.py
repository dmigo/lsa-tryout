import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from llm_seo_agent.utils.data_models import (
    ConversationSession,
    ConversationMessage,
    UserProfile,
    SEORecommendation,
    WebsiteAnalysis,
    CompetitorAnalysis,
    ConversationRole,
)


class ConversationMemory:
    def __init__(self, storage_path: str = "data/conversations"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[ConversationSession] = None
        self.retention_days = 30

    def create_session(
        self, user_id: str, website_url: Optional[str] = None, industry: Optional[str] = None
    ) -> ConversationSession:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())

        user_profile = UserProfile(user_id=user_id, website_url=website_url, industry=industry)

        session = ConversationSession(session_id=session_id, user_profile=user_profile)

        self.current_session = session
        self._save_session(session)
        return session

    def load_session(self, session_id: str) -> Optional[ConversationSession]:
        """Load an existing conversation session."""
        session_file = self.storage_path / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file, 'r') as f:
                session_data = json.load(f)

            session = ConversationSession.parse_obj(session_data)
            self.current_session = session
            return session
        except Exception as e:
            print(f"Error loading session {session_id}: {e}")
            return None

    def get_or_create_session(
        self, user_id: str, website_url: Optional[str] = None
    ) -> ConversationSession:
        """Get the most recent session for a user or create a new one."""
        recent_session = self._find_recent_session(user_id)

        if recent_session:
            self.current_session = recent_session
            return recent_session

        return self.create_session(user_id, website_url)

    def add_message(self, role: ConversationRole, content: str, metadata: Dict[str, Any] = None):
        """Add a message to the current conversation."""
        if not self.current_session:
            raise ValueError("No active session. Create or load a session first.")

        message = ConversationMessage(role=role, content=content, metadata=metadata or {})

        self.current_session.messages.append(message)
        self.current_session.updated_at = datetime.now()
        self._save_session(self.current_session)

    def add_recommendation(self, recommendation: SEORecommendation):
        """Add an SEO recommendation to the current session."""
        if not self.current_session:
            raise ValueError("No active session")

        self.current_session.recommendations.append(recommendation)
        self.current_session.updated_at = datetime.now()
        self._save_session(self.current_session)

    def update_recommendation_status(self, recommendation_id: str, status: str):
        """Update the status of an SEO recommendation."""
        if not self.current_session:
            return

        for rec in self.current_session.recommendations:
            if rec.id == recommendation_id:
                rec.implementation_status = status
                self.current_session.updated_at = datetime.now()
                self._save_session(self.current_session)
                break

    def add_website_analysis(self, analysis: WebsiteAnalysis):
        """Add a website analysis to the current session."""
        if not self.current_session:
            raise ValueError("No active session")

        self.current_session.website_analyses.append(analysis)
        self.current_session.updated_at = datetime.now()
        self._save_session(self.current_session)

    def get_conversation_context(self, max_messages: int = 10) -> str:
        """Get formatted conversation context for Claude."""
        if not self.current_session:
            return ""

        recent_messages = self.current_session.messages[-max_messages:]
        context_parts = []

        # Add user profile context
        profile = self.current_session.user_profile
        if profile.website_url:
            context_parts.append(f"User's website: {profile.website_url}")
        if profile.industry:
            context_parts.append(f"Industry: {profile.industry}")
        if profile.seo_goals:
            context_parts.append(f"SEO Goals: {', '.join(profile.seo_goals)}")

        # Add recent conversation
        context_parts.append("\nRecent conversation:")
        for msg in recent_messages:
            role_label = "User" if msg.role == ConversationRole.USER else "Assistant"
            context_parts.append(f"{role_label}: {msg.content}")

        # Add recent recommendations
        if self.current_session.recommendations:
            context_parts.append("\nRecent recommendations:")
            for rec in self.current_session.recommendations[-3:]:
                status_emoji = {
                    "pending": "⏳",
                    "in_progress": "🔄",
                    "completed": "✅",
                    "dismissed": "❌",
                }
                emoji = status_emoji.get(rec.implementation_status, "")
                context_parts.append(f"{emoji} {rec.title} ({rec.priority} priority)")

        return "\n".join(context_parts)

    def get_user_summary(self) -> str:
        """Get a summary of the user's SEO journey."""
        if not self.current_session:
            return ""

        profile = self.current_session.user_profile
        total_messages = len(self.current_session.messages)
        total_recommendations = len(self.current_session.recommendations)
        completed_recommendations = len(
            [
                r
                for r in self.current_session.recommendations
                if r.implementation_status == "completed"
            ]
        )

        summary = f"""
User Profile Summary:
- Website: {profile.website_url or 'Not provided'}
- Industry: {profile.industry or 'Not specified'}
- Total conversations: {total_messages // 2}
- Recommendations given: {total_recommendations}
- Recommendations completed: {completed_recommendations}
- Account age: {(datetime.now() - profile.created_at).days} days
"""
        return summary.strip()

    def cleanup_old_sessions(self):
        """Remove sessions older than retention period."""
        cutoff_date = datetime.now() - timedelta(days=self.retention_days)

        for session_file in self.storage_path.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)

                created_at = datetime.fromisoformat(
                    session_data['created_at'].replace('Z', '+00:00')
                )

                if created_at < cutoff_date:
                    session_file.unlink()
                    print(f"Cleaned up old session: {session_file.name}")

            except Exception as e:
                print(f"Error processing {session_file}: {e}")

    def _save_session(self, session: ConversationSession):
        """Save session to disk."""
        session_file = self.storage_path / f"{session.session_id}.json"

        try:
            with open(session_file, 'w') as f:
                json.dump(session.dict(), f, indent=2, default=str)
        except Exception as e:
            print(f"Error saving session: {e}")

    def _find_recent_session(self, user_id: str) -> Optional[ConversationSession]:
        """Find the most recent session for a user."""
        recent_session = None
        recent_time = None

        for session_file in self.storage_path.glob("*.json"):
            try:
                with open(session_file, 'r') as f:
                    session_data = json.load(f)

                if session_data['user_profile']['user_id'] == user_id:
                    updated_at = datetime.fromisoformat(
                        session_data['updated_at'].replace('Z', '+00:00')
                    )

                    if recent_time is None or updated_at > recent_time:
                        recent_time = updated_at
                        recent_session = ConversationSession.parse_obj(session_data)

            except Exception as e:
                print(f"Error processing {session_file}: {e}")

        return recent_session

    def export_to_markdown(
        self, output_path: Optional[str] = None, include_conversation: bool = False
    ) -> str:
        """Export current session's recommendations and analysis to markdown.

        Args:
            output_path: Path to save the markdown file. If None, returns content only.
            include_conversation: Whether to include full conversation history.

        Returns:
            The markdown content as a string.
        """
        if not self.current_session:
            raise ValueError("No active session to export")

        session = self.current_session
        profile = session.user_profile

        # Build markdown content
        lines = []

        # Header
        lines.append("# SEO Consultation Report")
        lines.append("")
        lines.append(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        lines.append(f"**Session ID:** `{session.session_id}`")
        lines.append("")

        # User Profile
        lines.append("## 👤 Client Profile")
        lines.append("")
        if profile.website_url:
            lines.append(f"**Website:** {profile.website_url}")
        if profile.industry:
            lines.append(f"**Industry:** {profile.industry}")
        if profile.seo_goals:
            lines.append(f"**SEO Goals:** {', '.join(profile.seo_goals)}")
        if profile.current_challenges:
            lines.append(f"**Current Challenges:** {', '.join(profile.current_challenges)}")
        lines.append("")

        # Website Analyses
        if session.website_analyses:
            lines.append("## 🔍 Website Analysis")
            lines.append("")

            for i, analysis in enumerate(session.website_analyses, 1):
                lines.append(f"### Analysis #{i}: {analysis.url}")
                lines.append("")
                lines.append(f"**Analyzed:** {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append("")

                # AI Readiness Score with visual indicator
                score = analysis.ai_readiness_score or 0
                if score >= 80:
                    score_indicator = "🟢 Excellent"
                elif score >= 60:
                    score_indicator = "🟡 Good"
                elif score >= 40:
                    score_indicator = "🟠 Needs Improvement"
                else:
                    score_indicator = "🔴 Critical"

                lines.append(f"**AI Readiness Score:** {score}/100 {score_indicator}")
                lines.append("")

                # Page Metadata
                lines.append("#### 📄 Page Metadata")
                lines.append("")
                if analysis.title:
                    lines.append(f"**Title:** {analysis.title}")
                else:
                    lines.append("**Title:** ❌ Missing")

                if analysis.meta_description:
                    lines.append(f"**Meta Description:** {analysis.meta_description}")
                else:
                    lines.append("**Meta Description:** ❌ Missing")
                lines.append("")

                # Content Structure
                lines.append("#### 📐 Content Structure")
                lines.append("")
                if analysis.h1_tags:
                    lines.append(f"**H1 Tags ({len(analysis.h1_tags)}):**")
                    for h1 in analysis.h1_tags[:5]:  # Show max 5
                        lines.append(f"- {h1}")
                    if len(analysis.h1_tags) > 5:
                        lines.append(f"- *...and {len(analysis.h1_tags) - 5} more*")
                else:
                    lines.append("**H1 Tags:** ❌ None found")
                lines.append("")

                if analysis.content_quality_score is not None:
                    lines.append(f"**Content Quality Score:** {analysis.content_quality_score}/100")
                    lines.append("")

                # Technical Issues
                if analysis.technical_issues:
                    lines.append("#### 🚨 Technical Issues")
                    lines.append("")
                    for issue in analysis.technical_issues:
                        lines.append(f"- ❌ {issue}")
                    lines.append("")

                # Content Suggestions
                if analysis.content_suggestions:
                    lines.append("#### 💡 Content Optimization Suggestions")
                    lines.append("")
                    for suggestion in analysis.content_suggestions:
                        lines.append(f"- 📝 {suggestion}")
                    lines.append("")

        # Recommendations
        if session.recommendations:
            lines.append("## 📋 SEO Recommendations")
            lines.append("")

            # Group by status
            pending = [r for r in session.recommendations if r.implementation_status == "pending"]
            in_progress = [
                r for r in session.recommendations if r.implementation_status == "in_progress"
            ]
            completed = [
                r for r in session.recommendations if r.implementation_status == "completed"
            ]

            if pending:
                lines.append("### 🔴 Pending Recommendations")
                lines.append("")
                for rec in pending:
                    lines.append(f"#### {rec.title}")
                    lines.append(
                        f"**Priority:** {rec.priority.upper()} | **Category:** {rec.category}"
                    )
                    lines.append("")
                    lines.append(rec.description)
                    lines.append("")
                    if rec.estimated_impact:
                        lines.append(f"**Estimated Impact:** {rec.estimated_impact}")
                        lines.append("")

            if in_progress:
                lines.append("### 🟡 In Progress")
                lines.append("")
                for rec in in_progress:
                    lines.append(f"#### {rec.title}")
                    lines.append(
                        f"**Priority:** {rec.priority.upper()} | **Category:** {rec.category}"
                    )
                    lines.append("")
                    lines.append(rec.description)
                    lines.append("")

            if completed:
                lines.append("### ✅ Completed")
                lines.append("")
                for rec in completed:
                    lines.append(f"- {rec.title} ({rec.category})")
                lines.append("")

        # Competitor Analyses
        if session.competitor_analyses:
            lines.append("## 🏆 Competitive Analysis")
            lines.append("")

            for analysis in session.competitor_analyses:
                lines.append(f"### {analysis.your_domain} vs Competitors")
                lines.append("")
                lines.append(f"**Analyzed:** {analysis.analyzed_at.strftime('%Y-%m-%d %H:%M')}")
                lines.append("")

                if analysis.key_insights:
                    lines.append("**Key Insights:**")
                    for insight in analysis.key_insights:
                        lines.append(f"- {insight}")
                    lines.append("")

                if analysis.recommendations:
                    lines.append("**Recommendations:**")
                    for rec in analysis.recommendations:
                        lines.append(f"- {rec}")
                    lines.append("")

        # Conversation History (optional)
        if include_conversation and session.messages:
            lines.append("## 💬 Conversation History")
            lines.append("")

            for msg in session.messages:
                role_emoji = "👤" if msg.role == ConversationRole.USER else "🤖"
                role_label = "You" if msg.role == ConversationRole.USER else "Agent"
                lines.append(
                    f"### {role_emoji} {role_label} ({msg.timestamp.strftime('%H:%M:%S')})"
                )
                lines.append("")
                lines.append(msg.content)
                lines.append("")

        # Summary
        lines.append("## 📊 Summary")
        lines.append("")
        lines.append(f"- **Total Conversations:** {len(session.messages) // 2}")
        lines.append(f"- **Recommendations Given:** {len(session.recommendations)}")
        lines.append(
            f"- **Completed Actions:** {len([r for r in session.recommendations if r.implementation_status == 'completed'])}"
        )
        lines.append(f"- **Website Analyses:** {len(session.website_analyses)}")
        lines.append(f"- **Competitor Analyses:** {len(session.competitor_analyses)}")
        lines.append("")
        lines.append("---")
        lines.append("")
        lines.append("*Generated by LLM SEO Agent*")

        markdown_content = "\n".join(lines)

        # Save to file if path provided
        if output_path:
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

        return markdown_content
