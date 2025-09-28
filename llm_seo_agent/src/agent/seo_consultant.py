import uuid
import asyncio
from typing import Dict, List, Any, Optional
from .memory import ConversationMemory
from .tools import SEOTools
from ..utils.claude_client import ClaudeClient
from ..utils.data_models import (
    ConversationRole, SEORecommendation, ToolResponse
)


class SEOConsultant:
    def __init__(self, claude_api_key: Optional[str] = None, storage_path: str = "data/conversations"):
        self.claude = ClaudeClient(api_key=claude_api_key)
        self.memory = ConversationMemory(storage_path=storage_path)
        self.current_user_id = "default_user"  # In production, this would be dynamic

    async def start_conversation(self, user_id: str = None, website_url: str = None) -> str:
        """Start a new conversation or continue existing one."""
        if user_id:
            self.current_user_id = user_id

        # Get or create session
        session = self.memory.get_or_create_session(self.current_user_id, website_url)

        # Generate welcome message
        welcome_context = self.memory.get_user_summary()

        if len(session.messages) == 0:
            # First time user
            welcome_message = await self.claude.casual_conversation(
                user_message="Generate a warm welcome message for a new SEO consultation client",
                context=welcome_context
            )
        else:
            # Returning user
            welcome_message = await self.claude.casual_conversation(
                user_message="Generate a welcome back message for a returning SEO client",
                context=welcome_context
            )

        # Add welcome to memory
        self.memory.add_message(ConversationRole.ASSISTANT, welcome_message)

        return welcome_message

    async def chat(self, user_message: str) -> str:
        """Process a user message and generate response."""

        # Add user message to memory
        self.memory.add_message(ConversationRole.USER, user_message)

        # Get conversation context
        context = self.memory.get_conversation_context()

        # Classify user intent
        intent = await self.claude.classify_intent(user_message)

        response = ""

        if intent.get('needs_analysis', False):
            # User needs analysis - use tools
            response = await self._handle_analysis_request(user_message, context, intent)
        else:
            # Casual conversation
            response = await self.claude.casual_conversation(user_message, context)

        # Add response to memory
        self.memory.add_message(ConversationRole.ASSISTANT, response)

        return response

    async def _handle_analysis_request(self, user_message: str, context: str, intent: Dict) -> str:
        """Handle requests that require SEO analysis tools."""

        tool_results = {}

        async with SEOTools() as tools:
            # Determine which tools to use based on intent
            if intent.get('intent_type') == 'website_audit':
                # Extract URL from entities or ask for it
                urls = [entity for entity in intent.get('entities', [])
                       if self._is_url(entity)]

                if urls:
                    result = await tools.analyze_website(urls[0])
                    tool_results['website_analysis'] = result

                    if result.success:
                        # Generate recommendations
                        recommendations = await self._create_recommendations(result.data)
                        for rec in recommendations:
                            self.memory.add_recommendation(rec)

            elif intent.get('intent_type') == 'competitor_analysis':
                urls = [entity for entity in intent.get('entities', [])
                       if self._is_url(entity)]

                if len(urls) >= 2:
                    your_site = urls[0]
                    competitors = urls[1:]
                    result = await tools.compare_competitors(your_site, competitors)
                    tool_results['competitor_analysis'] = result

            elif intent.get('intent_type') == 'performance_tracking':
                # Use domain from user profile or entities
                domain = None
                if self.memory.current_session and self.memory.current_session.user_profile.website_url:
                    domain = str(self.memory.current_session.user_profile.website_url)
                elif intent.get('entities'):
                    domain = intent['entities'][0]

                if domain:
                    result = await tools.track_performance(domain)
                    tool_results['performance_tracking'] = result

        # Generate response with tool results
        if tool_results:
            response = await self.claude.process_with_tools(
                user_message=user_message,
                context=context,
                available_tools=[],  # Define available tools here
                tool_results=tool_results
            )
        else:
            # No tools executed, ask for more information
            response = await self.claude.casual_conversation(
                user_message=f"I'd like to help with {intent.get('intent_type', 'your request')}, but I need more information. {user_message}",
                context=context
            )

        return response

    async def _create_recommendations(self, analysis_data: Dict) -> List[SEORecommendation]:
        """Create SEO recommendations based on analysis data."""
        recommendations = []

        # Technical issues recommendations
        for issue in analysis_data.get('technical_issues', []):
            rec = SEORecommendation(
                id=str(uuid.uuid4()),
                title=f"Fix: {issue}",
                description=f"Address the technical SEO issue: {issue}",
                priority="high" if "missing" in issue.lower() else "medium",
                category="technical_seo"
            )
            recommendations.append(rec)

        # Content suggestions recommendations
        for suggestion in analysis_data.get('content_suggestions', []):
            rec = SEORecommendation(
                id=str(uuid.uuid4()),
                title=f"Content: {suggestion}",
                description=f"Content optimization: {suggestion}",
                priority="medium",
                category="content_optimization"
            )
            recommendations.append(rec)

        # AI readiness improvements
        ai_score = analysis_data.get('ai_readiness_score', 0)
        if ai_score < 70:
            rec = SEORecommendation(
                id=str(uuid.uuid4()),
                title="Improve AI Search Readiness",
                description=f"Your AI readiness score is {ai_score}%. Focus on structured content and schema markup.",
                priority="high",
                category="ai_optimization",
                estimated_impact="High - Better AI citations"
            )
            recommendations.append(rec)

        return recommendations

    def _is_url(self, text: str) -> bool:
        """Check if text appears to be a URL."""
        return any(text.startswith(protocol) for protocol in ['http://', 'https://']) or \
               ('.' in text and len(text.split('.')) >= 2 and ' ' not in text)

    async def get_user_progress(self) -> Dict[str, Any]:
        """Get user's SEO progress summary."""
        if not self.memory.current_session:
            return {}

        session = self.memory.current_session
        total_recommendations = len(session.recommendations)
        completed = len([r for r in session.recommendations if r.implementation_status == "completed"])
        in_progress = len([r for r in session.recommendations if r.implementation_status == "in_progress"])

        return {
            'total_conversations': len(session.messages) // 2,
            'recommendations': {
                'total': total_recommendations,
                'completed': completed,
                'in_progress': in_progress,
                'completion_rate': (completed / total_recommendations * 100) if total_recommendations > 0 else 0
            },
            'website_analyses': len(session.website_analyses),
            'last_activity': session.updated_at,
            'user_profile': session.user_profile.dict()
        }

    async def update_recommendation_status(self, recommendation_id: str, status: str) -> str:
        """Update recommendation status and provide feedback."""
        self.memory.update_recommendation_status(recommendation_id, status)

        if status == "completed":
            congratulations = await self.claude.casual_conversation(
                user_message=f"The user completed a recommendation with ID {recommendation_id}. Congratulate them and suggest next steps.",
                context=self.memory.get_conversation_context()
            )
            self.memory.add_message(ConversationRole.ASSISTANT, congratulations)
            return congratulations
        elif status == "in_progress":
            return "Great! I've marked that recommendation as in progress. Let me know if you need any help implementing it."
        else:
            return "I've updated the recommendation status. What would you like to work on next?"

    async def proactive_check_in(self) -> Optional[str]:
        """Generate proactive check-in message if appropriate."""
        if not self.memory.current_session:
            return None

        session = self.memory.current_session
        days_since_update = (session.updated_at - session.created_at).days

        # Check if it's been a while since last interaction
        if days_since_update >= 7:
            context = self.memory.get_user_summary()
            check_in = await self.claude.casual_conversation(
                user_message="Generate a proactive check-in message for an SEO client we haven't heard from in a week",
                context=context
            )
            return check_in

        return None