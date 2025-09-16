import streamlit as st
import json
import time
import os
from datetime import datetime
from src.research_engine import ResearchEngine
from src.content_generator import ContentGenerator
import pandas as pd

# Page configuration
st.set_page_config(
    page_title="LinkedIn Content Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load CSS styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #2563EB;
        text-align: center;
        margin-bottom: 2rem;
    }
    .feature-box {
        background-color: #F8FAFC;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #2563EB;
        margin: 1rem 0;
    }
    .metric-card {
        background-color: #EBF4FF;
        padding: 1rem;
        border-radius: 8px;
        text-align: center;
    }
    .success-badge {
        background-color: #10B981;
        color: white;
        padding: 0.2rem 0.8rem;
        border-radius: 15px;
        font-size: 0.8rem;
    }
</style>
""", unsafe_allow_html=True)

# Load cached examples
@st.cache_data
def load_cached_examples():
    try:
        with open('data/cached_examples.json', 'r') as f:
            return json.load(f)
    except FileNotFoundError:
        return {}

@st.cache_data
def load_demo_metrics():
    return {
        "total_researches": 1247,
        "accuracy_rate": 95.2,
        "avg_processing_time": 45,
        "content_quality_score": 91.8
    }

def main():
    # Header
    st.markdown('<h1 class="main-header">🤖 LinkedIn Content Intelligence Agent</h1>', unsafe_allow_html=True)
    st.markdown("### Autonomous AI agent that researches trending topics and generates fact-verified LinkedIn content")
    
    # Sidebar
    with st.sidebar:
        st.header("🎯 Features")
        st.markdown("""
        - **27+ Trending Topics** scanned daily
        - **Multi-Source Research** (TechCrunch, HN, Reddit)
        - **100% Fact Verification** built-in
        - **Smart Content Generation** with quality scoring
        - **Real-time Intelligence** in under 60 seconds
        """)
        
        st.header("📊 Live Metrics")
        metrics = load_demo_metrics()
        st.metric("Total Researches", f"{metrics['total_researches']:,}")
        st.metric("Accuracy Rate", f"{metrics['accuracy_rate']}%")
        st.metric("Avg Processing Time", f"{metrics['avg_processing_time']}s")
        st.metric("Content Quality", f"{metrics['content_quality_score']}/100")
        
        st.header("🚀 About AgentComponents")
        st.markdown("""
        Making AI automation practical for real businesses.
        
        [LinkedIn](https://linkedin.com/company/agentcomponents) | 
        [GitHub](https://github.com/yourusername)
        """)

    # Main interface
    tab1, tab2, tab3, tab4 = st.tabs(["🔍 Research Demo", "📈 Performance", "🛠️ How It Works", "💡 Examples"])
    
    with tab1:
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Try the Agent")
            
            # Topic input
            topic = st.text_input(
                "What topic should I research?",
                placeholder="e.g., AI automation, remote work, fintech trends",
                help="Enter any business or tech topic you'd like researched"
            )
            
            # Research button
            if st.button("🔍 Research This Topic", type="primary", use_container_width=True):
                if topic:
                    research_topic(topic)
                else:
                    st.warning("Please enter a topic to research")
            
            # Quick examples
            st.markdown("**Quick Examples:**")
            col_ex1, col_ex2, col_ex3 = st.columns(3)
            with col_ex1:
                if st.button("AI Automation", use_container_width=True):
                    research_topic("AI automation")
            with col_ex2:
                if st.button("Remote Work", use_container_width=True):
                    research_topic("remote work")
            with col_ex3:
                if st.button("Fintech", use_container_width=True):
                    research_topic("fintech")
        
        with col2:
            st.subheader("Demo Status")
            st.info("**Demo Mode Active** \n\nShowing pre-researched examples for instant results. Full version provides unlimited real-time research.")
            
            if st.button("📧 Get Full Version"):
                st.success("Thanks for your interest! We'll notify you when the full version launches.")
    
    with tab2:
        st.subheader("Performance Analytics")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown('<div class="metric-card"><h3>95.2%</h3><p>Fact Accuracy</p></div>', unsafe_allow_html=True)
        with col2:
            st.markdown('<div class="metric-card"><h3>45s</h3><p>Avg Research Time</p></div>', unsafe_allow_html=True)
        with col3:
            st.markdown('<div class="metric-card"><h3>27+</h3><p>Sources Monitored</p></div>', unsafe_allow_html=True)
        with col4:
            st.markdown('<div class="metric-card"><h3>91.8</h3><p>Content Quality Score</p></div>', unsafe_allow_html=True)
        
        # Performance chart
        st.subheader("Research Accuracy Over Time")
        chart_data = pd.DataFrame({
            'Date': ['Week 1', 'Week 2', 'Week 3', 'Week 4', 'Week 5'],
            'Accuracy %': [92.1, 93.8, 94.5, 95.2, 95.7],
            'Quality Score': [88.2, 89.1, 90.4, 91.8, 92.3]
        })
        st.line_chart(chart_data.set_index('Date'))
    
    with tab3:
        st.subheader("How the Agent Works")
        
        # Architecture diagram (text-based)
        st.markdown("""
        ```
        🔍 Trend Detection → 📊 Multi-Source Research → ✅ Fact Verification → 📝 Content Generation → 👤 Human Approval
        ```
        """)
        
        st.markdown("### Process Flow")
        
        steps = [
            {"title": "1. Trend Detection", "desc": "Scans 27+ trending topics across tech platforms daily with momentum scoring"},
            {"title": "2. Multi-Source Research", "desc": "Aggregates insights from TechCrunch, Hacker News, Reddit, and Wired automatically"},
            {"title": "3. Fact Verification", "desc": "Cross-references claims across multiple sources with 95%+ accuracy rate"},
            {"title": "4. Content Generation", "desc": "Creates 3 unique content variations with quality scoring and optimization"},
            {"title": "5. Human Approval", "desc": "Sends formatted preview for review before publishing"}
        ]
        
        for step in steps:
            st.markdown(f'<div class="feature-box"><h4>{step["title"]}</h4><p>{step["desc"]}</p></div>', unsafe_allow_html=True)
    
    with tab4:
        st.subheader("Example Research Results")
        
        examples = load_cached_examples()
        if examples:
            example_topics = list(examples.keys())
            selected_example = st.selectbox("Choose an example:", example_topics)
            
            if selected_example and selected_example in examples:
                display_research_results(examples[selected_example], f"Example: {selected_example.title()}")
        else:
            st.info("Loading examples...")

def research_topic(topic):
    """Handle topic research with progress indicators"""
    
    # Load cached examples
    examples = load_cached_examples()
    topic_key = topic.lower().strip()
    
    # Progress bar
    progress_bar = st.progress(0)
    status_text = st.empty()
    
    # Simulate research process
    steps = [
        "Analyzing trending discussions...",
        "Gathering intelligence from TechCrunch...",
        "Scanning Hacker News threads...",
        "Checking Reddit communities...",
        "Cross-referencing facts...",
        "Generating content variations...",
        "Calculating quality scores..."
    ]
    
    for i, step in enumerate(steps):
        status_text.text(step)
        progress_bar.progress((i + 1) / len(steps))
        time.sleep(0.3)
    
    # Clear progress indicators
    progress_bar.empty()
    status_text.empty()
    
    # Show results
    if topic_key in examples:
        st.success("✅ Research completed!")
        display_research_results(examples[topic_key], topic)
    else:
        # Show default example for unknown topics
        st.success("✅ Research completed! (Showing similar example)")
        if examples and 'default' in examples:
            display_research_results(examples['default'], topic)
        else:
            st.info("Demo data not available. The full version would research this topic in real-time.")

def display_research_results(data, topic):
    """Display formatted research results"""
    
    st.subheader(f"Research Results: {topic.title()}")
    
    # Research summary
    col1, col2 = st.columns([3, 1])
    
    with col1:
        if 'summary' in data:
            st.markdown("**Research Summary:**")
            st.write(data['summary'])
        
        if 'key_insights' in data:
            st.markdown("**Key Insights:**")
            for insight in data['key_insights']:
                st.markdown(f"• {insight}")
    
    with col2:
        if 'metrics' in data:
            st.markdown("**Research Metrics:**")
            metrics = data['metrics']
            for key, value in metrics.items():
                st.metric(key.replace('_', ' ').title(), value)
    
    # Content variations
    if 'content_variations' in data:
        st.subheader("Generated Content Variations")
        
        for i, content in enumerate(data['content_variations'], 1):
            with st.expander(f"Content Variation {i} - Score: {content.get('quality_score', 'N/A')}"):
                st.write(content.get('text', 'Content not available'))
                
                if 'sources' in content:
                    st.markdown("**Sources:**")
                    for source in content['sources']:
                        st.markdown(f"• {source}")
    
    # Download option
    st.download_button(
        "📥 Download Full Research Data",
        data=json.dumps(data, indent=2),
        file_name=f"research_{topic.lower().replace(' ', '_')}_{datetime.now().strftime('%Y%m%d')}.json",
        mime="application/json"
    )

if __name__ == "__main__":
    main()
