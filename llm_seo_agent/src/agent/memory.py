import json
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from ..utils.data_models import (
    ConversationSession, ConversationMessage, UserProfile,
    SEORecommendation, WebsiteAnalysis, CompetitorAnalysis, ConversationRole
)


class ConversationMemory:
    def __init__(self, storage_path: str = "data/conversations"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[ConversationSession] = None
        self.retention_days = 30

    def create_session(self, user_id: str, website_url: Optional[str] = None,
                      industry: Optional[str] = None) -> ConversationSession:
        """Create a new conversation session."""
        session_id = str(uuid.uuid4())

        user_profile = UserProfile(
            user_id=user_id,
            website_url=website_url,
            industry=industry
        )

        session = ConversationSession(
            session_id=session_id,
            user_profile=user_profile
        )

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

    def get_or_create_session(self, user_id: str, website_url: Optional[str] = None) -> ConversationSession:
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

        message = ConversationMessage(
            role=role,
            content=content,
            metadata=metadata or {}
        )

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
                status_emoji = {"pending": "⏳", "in_progress": "🔄", "completed": "✅", "dismissed": "❌"}
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
        completed_recommendations = len([r for r in self.current_session.recommendations
                                       if r.implementation_status == "completed"])

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

                created_at = datetime.fromisoformat(session_data['created_at'].replace('Z', '+00:00'))

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
                    updated_at = datetime.fromisoformat(session_data['updated_at'].replace('Z', '+00:00'))

                    if recent_time is None or updated_at > recent_time:
                        recent_time = updated_at
                        recent_session = ConversationSession.parse_obj(session_data)

            except Exception as e:
                print(f"Error processing {session_file}: {e}")

        return recent_session