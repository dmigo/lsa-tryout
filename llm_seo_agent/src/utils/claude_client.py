import asyncio
import logging
from typing import Dict, List, Optional, Any
from anthropic import Anthropic
import json
import os
from ..utils.data_models import ToolResponse


class ClaudeClient:
    def __init__(self, api_key: Optional[str] = None, model: str = "claude-3-sonnet-20240229"):
        self.api_key = api_key or os.getenv("CLAUDE_API_KEY")
        if not self.api_key:
            raise ValueError("Claude API key must be provided or set as CLAUDE_API_KEY environment variable")

        self.client = Anthropic(api_key=self.api_key)
        self.model = model
        self.logger = logging.getLogger(__name__)

    async def generate_response(self, user_message: str, context: str = "",
                              system_prompt: str = "", tools: List[Dict] = None) -> str:
        """Generate a response using Claude with conversation context."""

        messages = []

        if context:
            messages.append({
                "role": "user",
                "content": f"Context from previous conversation:\n{context}\n\nCurrent message: {user_message}"
            })
        else:
            messages.append({
                "role": "user",
                "content": user_message
            })

        try:
            if tools:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=messages,
                    tools=tools
                )
            else:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    system=system_prompt,
                    messages=messages
                )

            if response.content:
                if isinstance(response.content[0], dict) and 'text' in response.content[0]:
                    return response.content[0]['text']
                else:
                    return str(response.content[0])

            return "I apologize, but I couldn't generate a response. Please try again."

        except Exception as e:
            self.logger.error(f"Error generating response: {e}")
            return f"I encountered an error: {str(e)}. Please try rephrasing your question."

    async def classify_intent(self, user_message: str) -> Dict[str, Any]:
        """Classify user intent to determine if tools are needed."""

        classification_prompt = """
        Analyze this user message and determine what type of SEO assistance they need.
        Return a JSON response with:
        - needs_analysis: boolean (true if they need website/competitor analysis)
        - intent_type: string (one of: website_audit, competitor_analysis, content_strategy, technical_seo, general_question, greeting)
        - urgency: string (high, medium, low)
        - entities: list of URLs, domains, or keywords mentioned

        User message: {message}
        """

        try:
            response = await self.generate_response(
                user_message=classification_prompt.format(message=user_message),
                system_prompt="You are an intent classification system. Always respond with valid JSON."
            )

            # Try to parse JSON response
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Fallback classification
                return {
                    "needs_analysis": any(keyword in user_message.lower()
                                        for keyword in ["analyze", "audit", "check", "compare", "competitor"]),
                    "intent_type": "general_question",
                    "urgency": "medium",
                    "entities": []
                }

        except Exception as e:
            self.logger.error(f"Error classifying intent: {e}")
            return {
                "needs_analysis": False,
                "intent_type": "general_question",
                "urgency": "low",
                "entities": []
            }

    async def generate_seo_recommendations(self, analysis_data: Dict[str, Any]) -> List[str]:
        """Generate specific SEO recommendations based on analysis data."""

        recommendations_prompt = f"""
        Based on this SEO analysis data, provide 3-5 specific, actionable recommendations.
        Each recommendation should be:
        - Specific and actionable
        - Prioritized by impact
        - Focused on AI search optimization

        Analysis data:
        {json.dumps(analysis_data, indent=2)}

        Format as a numbered list of recommendations.
        """

        try:
            response = await self.generate_response(
                user_message=recommendations_prompt,
                system_prompt="You are an expert SEO consultant specializing in AI search optimization."
            )
            return response.split('\n')

        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return ["I encountered an error generating recommendations. Please try again."]

    async def process_with_tools(self, user_message: str, context: str,
                               available_tools: List[Dict], tool_results: Dict[str, ToolResponse]) -> str:
        """Process a message that requires tool usage."""

        tools_context = ""
        if tool_results:
            tools_context = "\nTool Results:\n"
            for tool_name, result in tool_results.items():
                if result.success:
                    tools_context += f"- {tool_name}: {json.dumps(result.data, indent=2)}\n"
                else:
                    tools_context += f"- {tool_name}: Error - {result.error_message}\n"

        full_context = f"{context}{tools_context}"

        system_prompt = """
        You are an expert SEO consultant specializing in AI search optimization.
        You help businesses optimize their websites to appear in AI-generated responses from ChatGPT, Claude, Perplexity, and other AI systems.

        Your expertise includes:
        - Content structure for AI citations
        - Schema markup and structured data
        - Authority building and E-A-T optimization
        - Technical SEO for AI crawlers
        - Competitive analysis for AI search

        Always provide specific, actionable advice with clear next steps.
        Reference the tool results in your response and explain what they mean for the user's SEO strategy.
        """

        return await self.generate_response(
            user_message=user_message,
            context=full_context,
            system_prompt=system_prompt
        )

    async def casual_conversation(self, user_message: str, context: str) -> str:
        """Handle casual conversation without tools."""

        system_prompt = """
        You are a friendly SEO consultant who specializes in AI search optimization.
        You're having a casual conversation with a client about their website and SEO strategy.

        Your personality:
        - Friendly and approachable, but professional
        - Passionate about SEO and always ready to help
        - Ask clarifying questions to better understand their needs
        - Reference previous conversations when relevant
        - Proactively suggest next steps

        Keep responses conversational but informative.
        """

        return await self.generate_response(
            user_message=user_message,
            context=context,
            system_prompt=system_prompt
        )