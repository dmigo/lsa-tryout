import uuid
import asyncio
from typing import Dict, List, Any, Optional
from .memory import ConversationMemory
from .tools import SEOTools
from llm_seo_agent.utils.claude_client import ClaudeClient
from llm_seo_agent.utils.data_models import (
    ConversationRole, SEORecommendation, ToolResponse
)


class SEOConsultant:
    def __init__(self, claude_api_key: Optional[str] = None, storage_path: str = "data/conversations"):
        self.claude = ClaudeClient(api_key=claude_api_key)
        self.memory = ConversationMemory(storage_path=storage_path)
        self.current_user_id = "default_user"  # In production, this would be dynamic
        self.tool_schemas = self._define_tool_schemas()

    def _define_tool_schemas(self) -> List[Dict[str, Any]]:
        """Define tool schemas for Claude API."""
        return [
            {
                "name": "analyze_website",
                "description": "Analyzes a website for SEO optimization opportunities. Returns comprehensive SEO metrics including title tags, meta descriptions, heading structure, content analysis, schema markup detection, and AI readiness score. Use this when the user asks to analyze, audit, or check their website.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "url": {
                            "type": "string",
                            "description": "The website URL to analyze (e.g., 'https://example.com' or 'example.com')"
                        }
                    },
                    "required": ["url"]
                }
            },
            {
                "name": "compare_competitors",
                "description": "Compares your website against competitor websites for SEO metrics. Analyzes AI readiness scores, content depth, schema markup usage, and provides competitive insights. Use this when the user wants to compare their site with competitors.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "your_site": {
                            "type": "string",
                            "description": "The user's website URL"
                        },
                        "competitor_sites": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of competitor website URLs (up to 3)"
                        }
                    },
                    "required": ["your_site", "competitor_sites"]
                }
            },
            {
                "name": "check_ai_citations",
                "description": "Checks how often a domain is cited by AI search engines like ChatGPT, Claude, and Perplexity. Provides citation frequency, trending topics, and recommendations for improvement. Use when user asks about AI search visibility or citations.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "The domain to check (e.g., 'example.com')"
                        },
                        "keywords": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional list of keywords to analyze"
                        }
                    },
                    "required": ["domain"]
                }
            },
            {
                "name": "track_performance",
                "description": "Tracks SEO performance metrics over time including AI citations, organic traffic, and search rankings. Use when user wants to see performance trends or track progress.",
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "domain": {
                            "type": "string",
                            "description": "The domain to track"
                        },
                        "timeframe": {
                            "type": "string",
                            "description": "Timeframe for analysis (e.g., '30d', '7d', '90d')",
                            "default": "30d"
                        }
                    },
                    "required": ["domain"]
                }
            }
        ]

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
        """Process a user message and generate response with tool calling."""

        # Add user message to memory
        self.memory.add_message(ConversationRole.USER, user_message)

        # Get conversation context
        context = self.memory.get_conversation_context()

        # System prompt for SEO consultant
        system_prompt = """You are an expert SEO consultant specializing in AI search optimization.
        You help businesses optimize their websites to appear in AI-generated responses from ChatGPT, Claude, Perplexity, and other AI systems.

        Your expertise includes:
        - Content structure for AI citations
        - Schema markup and structured data
        - Authority building and E-A-T optimization
        - Technical SEO for AI crawlers
        - Competitive analysis for AI search

        When a user asks about analyzing a website, checking competitors, or tracking performance, use the appropriate tools.
        Always provide specific, actionable advice with clear next steps.
        """

        try:
            # Call Claude with tools available
            response = await self.claude.generate_response_with_tools(
                user_message=user_message,
                context=context,
                system_prompt=system_prompt,
                tools=self.tool_schemas
            )

            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Execute tools and get results
                final_response = await self._execute_tools_and_respond(response, user_message, context, system_prompt)
            else:
                # No tools needed, extract text response
                final_response = self._extract_text_from_response(response)

            # Add response to memory
            self.memory.add_message(ConversationRole.ASSISTANT, final_response)

            return final_response

        except Exception as e:
            error_response = f"I encountered an error: {str(e)}. Let me try to help you differently."
            self.memory.add_message(ConversationRole.ASSISTANT, error_response)
            return error_response

    def _extract_text_from_response(self, response) -> str:
        """Extract text from Claude response object."""
        for content_block in response.content:
            if hasattr(content_block, 'text'):
                return content_block.text
            elif isinstance(content_block, dict) and 'text' in content_block:
                return content_block['text']
        return "I apologize, but I couldn't generate a proper response."

    async def _execute_tools_and_respond(self, initial_response, user_message: str, context: str, system_prompt: str) -> str:
        """Execute tools requested by Claude and generate final response."""

        # Extract tool use requests from response
        tool_use_blocks = [block for block in initial_response.content
                          if hasattr(block, 'type') and block.type == "tool_use"]

        if not tool_use_blocks:
            return self._extract_text_from_response(initial_response)

        # Execute each tool
        tool_results = []
        async with SEOTools() as tools:
            for tool_use in tool_use_blocks:
                tool_name = tool_use.name
                tool_input = tool_use.input
                tool_use_id = tool_use.id

                # Execute the appropriate tool
                result = await self._execute_single_tool(tools, tool_name, tool_input)

                # Store result in Claude's expected format
                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_use_id,
                    "content": str(result.data if result.success else result.error_message)
                })

                # If website analysis succeeded, create recommendations
                if tool_name == "analyze_website" and result.success:
                    recommendations = await self._create_recommendations(result.data)
                    for rec in recommendations:
                        self.memory.add_recommendation(rec)

        # Send tool results back to Claude for final response
        messages = [
            {
                "role": "user",
                "content": f"Context: {context}\n\nUser message: {user_message}" if context else user_message
            },
            {
                "role": "assistant",
                "content": initial_response.content
            },
            {
                "role": "user",
                "content": tool_results
            }
        ]

        final_response = self.claude.client.messages.create(
            model=self.claude.model,
            max_tokens=4000,
            system=system_prompt,
            messages=messages,
            tools=self.tool_schemas
        )

        return self._extract_text_from_response(final_response)

    async def _execute_single_tool(self, tools: SEOTools, tool_name: str, tool_input: Dict) -> ToolResponse:
        """Execute a single tool and return the result."""
        try:
            if tool_name == "analyze_website":
                return await tools.analyze_website(tool_input["url"])
            elif tool_name == "compare_competitors":
                return await tools.compare_competitors(
                    tool_input["your_site"],
                    tool_input["competitor_sites"]
                )
            elif tool_name == "check_ai_citations":
                keywords = tool_input.get("keywords", [])
                return await tools.check_ai_citations(tool_input["domain"], keywords)
            elif tool_name == "track_performance":
                timeframe = tool_input.get("timeframe", "30d")
                return await tools.track_performance(tool_input["domain"], timeframe)
            else:
                return ToolResponse(
                    tool_name=tool_name,
                    success=False,
                    error_message=f"Unknown tool: {tool_name}"
                )
        except Exception as e:
            return ToolResponse(
                tool_name=tool_name,
                success=False,
                error_message=str(e)
            )

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