# 🤖 LLM SEO Agent

> Your AI Search Optimization Consultant

A conversational AI agent powered by Claude that helps optimize websites for AI search engines like ChatGPT, Claude, Perplexity, and Gemini. Built for natural, expert-level SEO consultations.

## ✨ Features

### 🗣️ **Conversational Interface**
- Natural chat experience with an expert SEO consultant
- Memory of previous conversations and recommendations
- Context-aware responses that build on your SEO journey

### 🔍 **AI Search Optimization**
- Analyze websites for AI search readiness
- Optimize content structure for AI citations
- Implement FAQ and Q&A formats
- Schema markup optimization for AI understanding

### 🏆 **Competitive Analysis**
- Compare your site against competitors
- Identify content gaps and opportunities
- Benchmark AI citation performance
- Strategic recommendations based on competitive insights

### 📊 **Performance Monitoring**
- Track AI citation frequency over time
- Monitor organic traffic and rankings
- Performance dashboards and reports
- Progress tracking for recommendations

### 💻 **Multiple Interfaces**
- **CLI Chat**: Rich terminal interface with formatting
- **Web Dashboard**: Streamlit-based web interface
- **Quick Analysis**: One-shot website analysis
- **Interactive Setup**: Guided onboarding

## 🚀 Quick Start

### 1. Installation

```bash
# Clone the repository
git clone <repository-url>
cd llm_seo_agent

# Install with uv (recommended - much faster!)
uv sync

# Or install with specific optional features
uv sync --extra web --extra analysis --extra all

# Install spaCy model for advanced content analysis (optional)
uv run python -m spacy download en_core_web_sm
```

### 2. Setup

```bash
# Set your Claude API key
export CLAUDE_API_KEY='your-claude-api-key-here'

# Run setup to create directories and check dependencies
uv run python main.py setup
```

### 3. Start Using

```bash
# Interactive chat mode (recommended for first-time users)
uv run python main.py chat --setup

# Direct chat mode
uv run python main.py chat

# Web interface (requires --extra web)
uv run python main.py web

# Quick website analysis
uv run python main.py analyze https://example.com

# Compare against competitors
uv run python main.py compare https://yoursite.com https://competitor1.com https://competitor2.com
```

## 💬 Example Conversations

### Website Analysis
```
You: "Analyze my website: example.com"

Agent: "I'll analyze your website for AI search optimization. Let me check your content structure, schema markup, and authority signals..."

*runs analysis*

Agent: "I found several opportunities! Your content isn't structured for question-answering format, which AI models prefer. Here's what I recommend:

🔴 HIGH PRIORITY
• Add FAQ schema markup - This will help AI models understand your Q&A content
• Restructure your homepage with clear H2 questions - Makes content more citation-worthy
• Add missing meta descriptions - Currently 60% of pages lack descriptions

🟡 MEDIUM PRIORITY
• Expand content depth on key pages - Average 400 words, aim for 800-1200
• Implement breadcrumb schema - Helps AI understand site structure

Which area would you like to tackle first?"
```

### Ongoing Consultation
```
Agent: "Welcome back! Last time we discussed implementing FAQ schema markup. How did that go?"

You: "I added the FAQ schema to 10 pages but I'm not sure if it's working"

Agent: "Great progress! Let me check your implementation... I can see the schema is properly structured. It typically takes 2-4 weeks to see AI citation improvements.

Since you've made good progress there, ready for the next priority? I'd recommend working on your content structure - turning statements into questions and answers. Want me to show you how to optimize your top 3 pages?"
```

### Competitive Analysis
```
You: "My competitor always gets mentioned instead of me in AI searches"

Agent: "Let's figure out why. What's their domain?"

You: "competitor.com"

Agent: *analyzes competitor*

"I see the issue! They're getting cited 3x more than you in AI responses. Here's why:

📊 **Key Differences:**
- They structure content as direct answers to questions (you: 15%, them: 78%)
- They use comprehensive FAQ schema (you: none, them: full implementation)
- Their content is more question-focused (you: 2 questions/page, them: 8 questions/page)

🎯 **Quick Win:** Start with your top 5 pages - reformat each to include 3-5 questions with direct answers. This alone could increase your AI citations by 40-60%."
```

## 🛠️ CLI Commands

```bash
# Main commands
uv run python main.py chat           # Start interactive chat
uv run python main.py web            # Launch web interface
uv run python main.py analyze <url>  # Quick analysis
uv run python main.py compare <url> <competitor1> <competitor2>  # Competitive analysis

# Setup and configuration
uv run python main.py setup          # Initial setup
uv run python main.py config         # View configuration
uv run python main.py version        # Version info

# Chat options
uv run python main.py chat --setup   # Interactive onboarding
uv run python main.py chat --url example.com  # Quick analysis mode
uv run python main.py chat --api-key <key>    # Use specific API key

# Alternative: Use as installed script (after uv sync)
uv run llm-seo-agent chat            # Direct script access
uv run seo-agent analyze <url>       # Shorter alias
```

## 🎛️ Configuration

Customize behavior in `config/settings.yaml`:

```yaml
# Agent personality
agent:
  personality: "friendly_expert"  # friendly_expert, professional, casual
  proactive_suggestions: true
  memory_retention_days: 30

# Interface settings
interfaces:
  cli:
    enabled: true
    rich_formatting: true
  web:
    enabled: true
    port: 8501

# SEO tools configuration
seo_tools:
  web_crawler:
    max_concurrent_requests: 5
    max_pages_per_site: 10
  content_analyzer:
    enable_nlp: true
```

## 📁 Project Structure

```
llm_seo_agent/
├── src/
│   ├── agent/                 # Core agent logic
│   │   ├── conversation_manager.py  # Main conversation flow
│   │   ├── seo_consultant.py       # Claude-powered expertise
│   │   ├── memory.py               # Conversation memory
│   │   └── tools.py                # SEO analysis tools
│   ├── interfaces/            # User interfaces
│   │   ├── cli_chat.py            # Terminal interface
│   │   └── web_chat.py            # Streamlit web interface
│   ├── seo_engine/           # SEO analysis engine
│   │   ├── crawler.py             # Website crawling
│   │   ├── content_analyzer.py    # Content analysis
│   │   ├── competitor_tracker.py  # Competitive analysis
│   │   └── performance_monitor.py # Performance tracking
│   ├── utils/                # Utilities
│   │   ├── claude_client.py       # Claude SDK wrapper
│   │   └── data_models.py         # Pydantic models
│   └── prompts/              # AI prompts
│       ├── system_prompt.txt      # Core personality
│       ├── seo_analysis.txt       # Analysis templates
│       └── conversation_flow.txt  # Conversation patterns
├── config/
│   └── settings.yaml         # Configuration
├── data/                     # Data storage
│   ├── conversations/        # Chat history
│   └── performance/          # Analytics data
├── main.py                   # Entry point
└── requirements.txt          # Dependencies
```

## 🔧 Advanced Usage

### Custom Analysis Workflows

```python
from src.agent.conversation_manager import ConversationManager

# Create custom analysis workflow
async def custom_analysis():
    manager = ConversationManager()
    await manager.start_session(user_id="analyst", website_url="example.com")

    # Run specific analysis
    response = await manager.process_message("Focus on technical SEO issues")
    print(response)

    # Get structured recommendations
    progress = await manager.consultant.get_user_progress()
    return progress
```

### Batch Website Analysis

```bash
# Analyze multiple sites
for site in site1.com site2.com site3.com; do
    uv run python main.py analyze $site --format json >> analysis_results.json
done
```

### Performance Monitoring Setup

```python
from src.seo_engine.performance_monitor import PerformanceMonitor

# Set up automated monitoring
monitor = PerformanceMonitor()
report = await monitor.track_performance("example.com", "30d")
formatted_report = await monitor.generate_performance_report("example.com")
```

## 🤝 Conversation Commands

While chatting with the agent, you can use these commands:

- `/help` - Show available commands
- `/status` - View your SEO progress
- `/recommendations` - See your recommendations
- `/complete <rec_id>` - Mark recommendation as completed
- `/progress <rec_id>` - Mark recommendation as in progress
- `/new` - Start fresh conversation
- `/export` - Export conversation history

## 🔌 Integrations

The agent supports integration with popular SEO tools:

- **Google Search Console** - Track organic performance
- **Google Analytics** - Monitor traffic metrics
- **Ahrefs API** - Backlink and keyword data
- **SEMrush API** - Competitive intelligence
- **Slack** - Team notifications and bot integration

## 📈 Performance Metrics

The agent tracks these key metrics:

### AI Search Metrics
- AI citation frequency across platforms
- Question-answer content performance
- Schema markup effectiveness
- Featured snippet captures

### Traditional SEO
- Organic traffic and rankings
- Technical SEO scores
- Content quality metrics
- User engagement signals

### Competitive Intelligence
- Relative AI citation performance
- Content gap analysis
- Authority signal comparison
- Market share trends

## 🛡️ Security & Privacy

- All conversations stored locally by default
- No data shared with third parties
- Configurable data retention policies
- Optional cloud storage with encryption

## 📋 Requirements

- Python 3.8+
- [uv](https://docs.astral.sh/uv/) (recommended) or pip for package management
- Claude API key (required)
- 100MB disk space for data storage
- Optional: spaCy model for advanced content analysis

### Installing uv

```bash
# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# Or with pip
pip install uv
```

## 🚨 Troubleshooting

### Common Issues

**"Claude API key not found"**
```bash
export CLAUDE_API_KEY='your-api-key-here'
# Or use --api-key flag
```

**"Website analysis failed"**
- Check if the website is accessible
- Verify URL format (include https://)
- Some sites may block automated analysis

**"Streamlit won't start"**
```bash
uv sync --extra web
uv run python main.py web
```

**"Memory issues with large sites"**
- Reduce `max_pages_per_site` in config
- Use `--url` for quick analysis instead of full crawl

## 🎯 Best Practices

### For Best Results
1. **Be Specific**: "Analyze my homepage for FAQ opportunities" vs "help with SEO"
2. **Provide Context**: Share your industry, goals, and current challenges
3. **Follow Through**: Implement recommendations and report back on progress
4. **Ask Questions**: Don't hesitate to ask for clarification or examples

### Recommended Workflow
1. Start with website analysis
2. Implement high-priority recommendations
3. Schedule regular check-ins (weekly/bi-weekly)
4. Monitor performance and adjust strategy
5. Expand to competitive analysis and advanced optimizations

## 📄 License

MIT License - See LICENSE file for details

## 🤖 About

Built with ❤️ for the SEO community. This agent demonstrates how conversational AI can make expert SEO knowledge more accessible and actionable.

**Powered by:**
- Claude by Anthropic for AI conversations
- Rich for beautiful CLI interfaces
- Streamlit for web dashboards
- BeautifulSoup for web scraping
- spaCy for content analysis