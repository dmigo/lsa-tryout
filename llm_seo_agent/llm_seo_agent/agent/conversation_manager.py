import asyncio
from typing import Dict, List, Any, Optional, Callable
from .seo_consultant import SEOConsultant
from llm_seo_agent.utils.data_models import ConversationRole


class ConversationManager:
    def __init__(self, claude_api_key: Optional[str] = None):
        self.consultant = SEOConsultant(claude_api_key=claude_api_key)
        self.is_active = False
        self.message_handlers: List[Callable] = []

    def add_message_handler(self, handler: Callable):
        """Add a handler that gets called for each message exchange."""
        self.message_handlers.append(handler)

    async def start_session(self, user_id: str = None, website_url: str = None) -> str:
        """Start a new conversation session."""
        self.is_active = True
        welcome_message = await self.consultant.start_conversation(user_id, website_url)

        # Notify handlers
        for handler in self.message_handlers:
            try:
                await handler("session_start", {
                    "user_id": user_id,
                    "website_url": website_url,
                    "welcome_message": welcome_message
                })
            except Exception as e:
                print(f"Handler error: {e}")

        return welcome_message

    async def process_message(self, user_input: str) -> str:
        """Process a user message and return the assistant's response."""
        if not self.is_active:
            await self.start_session()

        # Handle special commands
        if user_input.startswith('/'):
            return await self._handle_command(user_input)

        # Process normal conversation
        response = await self.consultant.chat(user_input)

        # Notify handlers
        for handler in self.message_handlers:
            try:
                await handler("message_exchange", {
                    "user_message": user_input,
                    "assistant_response": response
                })
            except Exception as e:
                print(f"Handler error: {e}")

        return response

    async def _handle_command(self, command: str) -> str:
        """Handle special commands like /help, /status, etc."""
        command = command.lower().strip()

        if command == '/help':
            return self._get_help_message()

        elif command == '/status':
            progress = await self.consultant.get_user_progress()
            return self._format_status(progress)

        elif command == '/recommendations' or command == '/recs':
            return await self._show_recommendations()

        elif command.startswith('/complete '):
            rec_id = command.replace('/complete ', '').strip()
            return await self.consultant.update_recommendation_status(rec_id, "completed")

        elif command.startswith('/progress '):
            rec_id = command.replace('/progress ', '').strip()
            return await self.consultant.update_recommendation_status(rec_id, "in_progress")

        elif command == '/export':
            return await self._export_conversation()

        elif command == '/new' or command == '/restart':
            return await self.start_session()

        else:
            return "Unknown command. Type /help to see available commands."

    def _get_help_message(self) -> str:
        """Return help message with available commands."""
        return """
🤖 **SEO Agent Commands:**

**Analysis Commands:**
- Just ask! "Analyze my website: example.com"
- "Compare me to competitor.com"
- "Check my AI search performance"

**Progress Management:**
- `/status` - View your SEO progress
- `/recommendations` or `/recs` - See your recommendations
- `/complete <rec_id>` - Mark recommendation as completed
- `/progress <rec_id>` - Mark recommendation as in progress

**Session Management:**
- `/new` or `/restart` - Start fresh conversation
- `/export` - Export conversation history
- `/help` - Show this message

**Examples:**
- "My website isn't showing up in ChatGPT responses"
- "Analyze example.com for AI search optimization"
- "How do I improve my content for AI citations?"
"""

    def _format_status(self, progress: Dict[str, Any]) -> str:
        """Format user progress into readable message."""
        if not progress:
            return "No progress data available. Start by sharing your website URL!"

        recs = progress.get('recommendations', {})
        total_convos = progress.get('total_conversations', 0)

        status_msg = f"""
📊 **Your SEO Progress:**

**Conversations:** {total_convos} sessions
**Recommendations:** {recs.get('total', 0)} total
  - ✅ Completed: {recs.get('completed', 0)}
  - 🔄 In Progress: {recs.get('in_progress', 0)}
  - ⏳ Pending: {recs.get('total', 0) - recs.get('completed', 0) - recs.get('in_progress', 0)}

**Completion Rate:** {recs.get('completion_rate', 0):.1f}%
**Website Analyses:** {progress.get('website_analyses', 0)}
"""

        return status_msg.strip()

    async def _show_recommendations(self) -> str:
        """Show current recommendations."""
        if not self.consultant.memory.current_session:
            return "No active session. Start by sharing your website URL!"

        recommendations = self.consultant.memory.current_session.recommendations

        if not recommendations:
            return "No recommendations yet. Let me analyze your website first!"

        rec_msg = "📋 **Your SEO Recommendations:**\n\n"

        for rec in recommendations[-10:]:  # Show last 10
            status_emoji = {
                "pending": "⏳",
                "in_progress": "🔄",
                "completed": "✅",
                "dismissed": "❌"
            }

            priority_emoji = {
                "high": "🔴",
                "medium": "🟡",
                "low": "🟢"
            }

            emoji = status_emoji.get(rec.implementation_status, "⏳")
            priority = priority_emoji.get(rec.priority, "🟡")

            rec_msg += f"{emoji} {priority} **{rec.title}**\n"
            rec_msg += f"   ID: `{rec.id[:8]}...` | Category: {rec.category}\n"
            rec_msg += f"   {rec.description}\n\n"

        rec_msg += "💡 Use `/complete <rec_id>` or `/progress <rec_id>` to update status"

        return rec_msg

    async def _export_conversation(self) -> str:
        """Export conversation history."""
        if not self.consultant.memory.current_session:
            return "No conversation to export."

        session = self.consultant.memory.current_session
        export_data = {
            "session_id": session.session_id,
            "created_at": session.created_at.isoformat(),
            "user_profile": session.user_profile.dict(),
            "total_messages": len(session.messages),
            "total_recommendations": len(session.recommendations),
            "export_timestamp": session.updated_at.isoformat()
        }

        # In a real implementation, you'd save this to a file
        return f"""
📄 **Conversation Export:**

Session ID: {export_data['session_id']}
Created: {export_data['created_at']}
Messages: {export_data['total_messages']}
Recommendations: {export_data['total_recommendations']}

*In a full implementation, this would be saved as a downloadable file.*
"""

    async def end_session(self) -> str:
        """End the current conversation session."""
        self.is_active = False

        # Generate goodbye message
        goodbye_message = "Thanks for the SEO consultation! Feel free to return anytime for more optimization advice. Your progress has been saved."

        # Notify handlers
        for handler in self.message_handlers:
            try:
                await handler("session_end", {"goodbye_message": goodbye_message})
            except Exception as e:
                print(f"Handler error: {e}")

        return goodbye_message

    async def check_proactive_opportunities(self) -> Optional[str]:
        """Check if there are opportunities for proactive engagement."""
        return await self.consultant.proactive_check_in()

    def get_session_info(self) -> Dict[str, Any]:
        """Get current session information."""
        if not self.consultant.memory.current_session:
            return {"active": False}

        session = self.consultant.memory.current_session
        return {
            "active": self.is_active,
            "session_id": session.session_id,
            "user_id": session.user_profile.user_id,
            "website_url": str(session.user_profile.website_url) if session.user_profile.website_url else None,
            "message_count": len(session.messages),
            "recommendation_count": len(session.recommendations),
            "last_updated": session.updated_at.isoformat()
        }