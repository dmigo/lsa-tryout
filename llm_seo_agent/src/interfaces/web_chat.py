import streamlit as st
import asyncio
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Any, List
import json

from ..agent.conversation_manager import ConversationManager


class StreamlitWebInterface:
    """Streamlit-based web interface for the SEO Agent."""

    def __init__(self):
        self.setup_page_config()

    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="🤖 LLM SEO Agent",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )

    def run(self):
        """Main web interface."""
        self.setup_sidebar()
        self.main_chat_interface()

    def setup_sidebar(self):
        """Setup the sidebar with user profile and navigation."""
        with st.sidebar:
            st.title("🤖 LLM SEO Agent")
            st.markdown("*Your AI Search Optimization Consultant*")

            st.divider()

            # User Profile Section
            st.subheader("👤 Your Profile")

            # Get or create user profile
            if 'user_profile' not in st.session_state:
                st.session_state.user_profile = {
                    'user_id': 'web_user',
                    'website_url': '',
                    'industry': 'Other',
                    'seo_goals': []
                }

            # Profile inputs
            website_url = st.text_input(
                "Website URL",
                value=st.session_state.user_profile.get('website_url', ''),
                placeholder="https://example.com"
            )

            industry = st.selectbox(
                "Industry",
                ["Tech", "E-commerce", "B2B", "Healthcare", "Finance", "Other"],
                index=["Tech", "E-commerce", "B2B", "Healthcare", "Finance", "Other"].index(
                    st.session_state.user_profile.get('industry', 'Other')
                )
            )

            # SEO Goals
            st.subheader("🎯 SEO Goals")
            goal_options = [
                "Increase AI citations",
                "Improve organic traffic",
                "Better content structure",
                "Technical SEO fixes",
                "Competitor analysis",
                "Content strategy"
            ]

            selected_goals = st.multiselect(
                "What are your SEO priorities?",
                goal_options,
                default=st.session_state.user_profile.get('seo_goals', [])
            )

            # Update profile
            if st.button("Update Profile"):
                st.session_state.user_profile.update({
                    'website_url': website_url,
                    'industry': industry,
                    'seo_goals': selected_goals
                })
                st.success("Profile updated!")

            st.divider()

            # Progress Section
            self.show_progress_sidebar()

            st.divider()

            # Quick Actions
            st.subheader("⚡ Quick Actions")

            if st.button("🔍 Analyze My Website", use_container_width=True):
                if website_url:
                    self.add_message("user", f"Analyze my website: {website_url}")
                else:
                    st.error("Please enter your website URL first!")

            if st.button("📊 SEO Dashboard", use_container_width=True):
                self.show_seo_dashboard()

            if st.button("🔄 New Conversation", use_container_width=True):
                self.reset_conversation()

    def show_progress_sidebar(self):
        """Show progress information in sidebar."""
        st.subheader("📈 Your Progress")

        # Mock progress data (in real app, get from conversation manager)
        if 'progress_data' not in st.session_state:
            st.session_state.progress_data = {
                'conversations': 3,
                'recommendations': 8,
                'completed': 3,
                'ai_score': 72
            }

        progress = st.session_state.progress_data

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Conversations", progress['conversations'])
            st.metric("Completed", progress['completed'])

        with col2:
            st.metric("Recommendations", progress['recommendations'])
            st.metric("AI Score", f"{progress['ai_score']}%")

        # Progress bar
        completion_rate = (progress['completed'] / progress['recommendations']) * 100 if progress['recommendations'] > 0 else 0
        st.progress(completion_rate / 100, text=f"Completion Rate: {completion_rate:.1f}%")

    def main_chat_interface(self):
        """Main chat interface."""
        st.title("💬 SEO Consultation Chat")

        # Initialize chat history
        if 'messages' not in st.session_state:
            st.session_state.messages = [
                {
                    "role": "assistant",
                    "content": "Hi! I'm your LLM SEO consultant. I help optimize websites for AI search engines like ChatGPT, Claude, and Perplexity. What's your website URL or SEO question?",
                    "timestamp": datetime.now()
                }
            ]

        # Initialize conversation manager
        if 'conversation_manager' not in st.session_state:
            st.session_state.conversation_manager = ConversationManager()

        # Display chat history
        chat_container = st.container()
        with chat_container:
            for message in st.session_state.messages:
                with st.chat_message(message["role"]):
                    st.markdown(message["content"])

                    # Show timestamp and additional info for assistant messages
                    if message["role"] == "assistant":
                        st.caption(f"🕒 {message['timestamp'].strftime('%H:%M:%S')}")

        # Chat input
        if prompt := st.chat_input("Ask me about SEO optimization..."):
            self.add_message("user", prompt)

    def add_message(self, role: str, content: str):
        """Add a message to the chat and get response."""
        # Add user message
        st.session_state.messages.append({
            "role": role,
            "content": content,
            "timestamp": datetime.now()
        })

        # Get AI response
        if role == "user":
            with st.chat_message("user"):
                st.markdown(content)

            with st.chat_message("assistant"):
                with st.spinner("Thinking..."):
                    response = asyncio.run(self.get_ai_response(content))

                st.markdown(response)

                # Add assistant message
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": response,
                    "timestamp": datetime.now()
                })

        # Rerun to update the interface
        st.rerun()

    async def get_ai_response(self, user_message: str) -> str:
        """Get response from the conversation manager."""
        try:
            if not hasattr(st.session_state.conversation_manager, 'is_active') or not st.session_state.conversation_manager.is_active:
                # Start session with user profile
                profile = st.session_state.user_profile
                await st.session_state.conversation_manager.start_session(
                    user_id=profile['user_id'],
                    website_url=profile['website_url'] if profile['website_url'] else None
                )

            response = await st.session_state.conversation_manager.process_message(user_message)
            return response

        except Exception as e:
            return f"I apologize, but I encountered an error: {str(e)}. Please try again."

    def show_seo_dashboard(self):
        """Show SEO analytics dashboard."""
        st.subheader("📊 SEO Analytics Dashboard")

        # Create tabs for different views
        tab1, tab2, tab3, tab4 = st.tabs(["📈 Overview", "🔍 Website Analysis", "🏆 Competitors", "📋 Recommendations"])

        with tab1:
            self.show_overview_dashboard()

        with tab2:
            self.show_website_analysis()

        with tab3:
            self.show_competitor_analysis()

        with tab4:
            self.show_recommendations_dashboard()

    def show_overview_dashboard(self):
        """Show overview dashboard."""
        st.subheader("📈 SEO Performance Overview")

        # Mock data for demonstration
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                label="AI Citations",
                value=42,
                delta=8,
                delta_color="normal"
            )

        with col2:
            st.metric(
                label="Organic Traffic",
                value="5.4K",
                delta="12%",
                delta_color="normal"
            )

        with col3:
            st.metric(
                label="AI Score",
                value="72%",
                delta="5%",
                delta_color="normal"
            )

        with col4:
            st.metric(
                label="Avg. Position",
                value=12.3,
                delta=-2.1,
                delta_color="inverse"
            )

        # Performance chart
        st.subheader("📊 Performance Trends")

        # Generate mock time series data
        dates = pd.date_range(start='2024-01-01', end='2024-12-31', freq='W')
        data = {
            'Date': dates,
            'AI Citations': [20 + i*0.5 + (i%4)*2 for i in range(len(dates))],
            'Organic Traffic': [3000 + i*50 + (i%3)*100 for i in range(len(dates))],
            'AI Score': [60 + i*0.2 + (i%5)*1 for i in range(len(dates))]
        }

        df = pd.DataFrame(data)

        # Create line chart
        fig = px.line(
            df,
            x='Date',
            y=['AI Citations', 'Organic Traffic', 'AI Score'],
            title="SEO Performance Over Time"
        )

        st.plotly_chart(fig, use_container_width=True)

    def show_website_analysis(self):
        """Show website analysis results."""
        st.subheader("🔍 Website Analysis")

        website_url = st.session_state.user_profile.get('website_url', '')

        if not website_url:
            st.warning("Please enter your website URL in the sidebar to see analysis.")
            return

        col1, col2 = st.columns([2, 1])

        with col1:
            st.write(f"**Analyzing:** {website_url}")

            # Mock analysis results
            analysis_data = {
                'Technical Score': 78,
                'Content Quality': 72,
                'AI Readiness': 65,
                'Schema Markup': 45
            }

            # Create radar chart
            categories = list(analysis_data.keys())
            values = list(analysis_data.values())

            fig = go.Figure()

            fig.add_trace(go.Scatterpolar(
                r=values,
                theta=categories,
                fill='toself',
                name='Your Website'
            ))

            fig.update_layout(
                polar=dict(
                    radialaxis=dict(
                        visible=True,
                        range=[0, 100]
                    )),
                showlegend=True,
                title="Website Analysis Scores"
            )

            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.subheader("📋 Key Issues")
            issues = [
                "Missing schema markup",
                "Content needs FAQ structure",
                "Title tags too long",
                "Limited internal linking"
            ]

            for i, issue in enumerate(issues):
                st.write(f"{i+1}. {issue}")

            st.button("🔧 Get Detailed Recommendations", use_container_width=True)

    def show_competitor_analysis(self):
        """Show competitor analysis."""
        st.subheader("🏆 Competitor Analysis")

        competitor_url = st.text_input("Competitor URL", placeholder="https://competitor.com")

        if competitor_url:
            st.write(f"**Comparing against:** {competitor_url}")

            # Mock comparison data
            comparison_data = {
                'Metric': ['AI Citations', 'Content Depth', 'Technical SEO', 'Schema Usage'],
                'Your Site': [42, 72, 78, 45],
                'Competitor': [68, 85, 82, 90]
            }

            df = pd.DataFrame(comparison_data)

            fig = px.bar(
                df,
                x='Metric',
                y=['Your Site', 'Competitor'],
                title="Competitive Comparison",
                barmode='group'
            )

            st.plotly_chart(fig, use_container_width=True)

            # Insights
            st.subheader("🎯 Competitive Insights")
            insights = [
                "Competitor has 61% more AI citations",
                "They use comprehensive schema markup",
                "Better FAQ structure for AI queries",
                "Stronger topical authority"
            ]

            for insight in insights:
                st.write(f"• {insight}")

    def show_recommendations_dashboard(self):
        """Show recommendations dashboard."""
        st.subheader("📋 SEO Recommendations")

        # Mock recommendations data
        recommendations = [
            {"title": "Add FAQ Schema Markup", "priority": "High", "status": "Pending", "impact": "High"},
            {"title": "Optimize Content Structure", "priority": "High", "status": "In Progress", "impact": "Medium"},
            {"title": "Fix Title Tag Length", "priority": "Medium", "status": "Completed", "impact": "Low"},
            {"title": "Improve Internal Linking", "priority": "Medium", "status": "Pending", "impact": "Medium"},
            {"title": "Add Breadcrumb Schema", "priority": "Low", "status": "Pending", "impact": "Low"}
        ]

        # Create recommendations table
        df = pd.DataFrame(recommendations)

        # Style the dataframe
        styled_df = df.style.apply(lambda x: [
            'background-color: #ffebee' if v == 'High' else
            'background-color: #fff3e0' if v == 'Medium' else
            'background-color: #e8f5e8' if v == 'Low' else ''
            for v in x
        ], subset=['priority'])

        st.dataframe(styled_df, use_container_width=True)

        # Action buttons
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📝 Add Recommendation", use_container_width=True):
                st.session_state.show_add_rec = True

        with col2:
            if st.button("✅ Mark Completed", use_container_width=True):
                st.success("Recommendation marked as completed!")

        with col3:
            if st.button("📊 Export Report", use_container_width=True):
                self.export_recommendations(recommendations)

    def export_recommendations(self, recommendations: List[Dict]):
        """Export recommendations as downloadable file."""
        df = pd.DataFrame(recommendations)
        csv = df.to_csv(index=False)

        st.download_button(
            label="📁 Download CSV",
            data=csv,
            file_name=f"seo_recommendations_{datetime.now().strftime('%Y%m%d')}.csv",
            mime="text/csv"
        )

    def reset_conversation(self):
        """Reset the conversation."""
        st.session_state.messages = [
            {
                "role": "assistant",
                "content": "Hi! I'm your LLM SEO consultant. Ready for a fresh consultation?",
                "timestamp": datetime.now()
            }
        ]
        if 'conversation_manager' in st.session_state:
            del st.session_state.conversation_manager
        st.rerun()


def main():
    """Main entry point for Streamlit app."""
    app = StreamlitWebInterface()
    app.run()


if __name__ == "__main__":
    main()