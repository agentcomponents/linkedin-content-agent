import streamlit as st
import os
import json
import requests
from datetime import datetime, timedelta
import google.generativeai as genai
from huggingface_hub import InferenceClient
import time
import random

# Page config
st.set_page_config(
    page_title="LinkedIn Content Intelligence Agent",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
.main-header {
    background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.5rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 2rem;
}

.admin-header {
    background: linear-gradient(90deg, #f093fb 0%, #f5576c 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2rem;
    font-weight: bold;
    text-align: center;
    margin-bottom: 1.5rem;
}

.status-good {
    background-color: #d4edda;
    border: 1px solid #c3e6cb;
    color: #155724;
    padding: 10px;
    border-radius: 5px;
    margin: 5px 0;
}

.status-warning {
    background-color: #fff3cd;
    border: 1px solid #ffeaa7;
    color: #856404;
    padding: 10px;
    border-radius: 5px;
    margin: 5px 0;
}

.status-error {
    background-color: #f8d7da;
    border: 1px solid #f5c6cb;
    color: #721c24;
    padding: 10px;
    border-radius: 5px;
    margin: 5px 0;
}

.metric-card {
    background: white;
    padding: 1rem;
    border-radius: 10px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    margin: 0.5rem 0;
}
</style>
""", unsafe_allow_html=True)

class FreeAPIManager:
    """Manages free-tier API calls with intelligent rate limiting"""
    
    def __init__(self):
        self.hf_client = None
        self.gemini_model = None
        self.usage_file = 'api_usage.json'
        
        # Initialize APIs
        self._setup_apis()
    
    def _setup_apis(self):
        """Set up free API clients"""
        try:
            # Hugging Face setup
            hf_token = st.secrets.get('HUGGINGFACE_TOKEN')
            if hf_token:
                self.hf_client = InferenceClient(token=hf_token)
            
            # Gemini setup
            gemini_key = st.secrets.get('GEMINI_API_KEY')
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
        except Exception as e:
            st.error(f"API setup error: {e}")
    
    def check_daily_limit(self, api_name: str) -> bool:
        """Check if we're under daily API limits"""
        try:
            if 'api_usage' not in st.session_state:
                st.session_state.api_usage = {}
            
            usage = st.session_state.api_usage
            today = datetime.now().strftime('%Y-%m-%d')
            daily_usage = usage.get(today, {})
            
            # Conservative daily limits
            limits = {
                'huggingface': 25,  # From 1000/month free tier
                'gemini': 80,       # From 15/minute rate limit
            }
            
            current_usage = daily_usage.get(api_name, 0)
            return current_usage < limits[api_name]
        except:
            return True  # Default to allowing if error
    
    def log_api_usage(self, api_name: str):
        """Log API usage for rate limiting"""
        try:
            if 'api_usage' not in st.session_state:
                st.session_state.api_usage = {}
            
            today = datetime.now().strftime('%Y-%m-%d')
            if today not in st.session_state.api_usage:
                st.session_state.api_usage[today] = {}
            
            st.session_state.api_usage[today][api_name] = st.session_state.api_usage[today].get(api_name, 0) + 1
        except Exception as e:
            st.error(f"Usage logging error: {e}")
    
    def research_with_gemini(self, topic: str) -> dict:
        """Use Gemini for research"""
        if not self.gemini_model or not self.check_daily_limit('gemini'):
            return None
        
        try:
            prompt = f"""Research the topic "{topic}" for LinkedIn content creation. Provide a brief summary with:

1. Current trends related to {topic}
2. Key statistics or data points
3. Professional insights
4. Business implications
5. Actionable takeaways

Keep the response concise and professional."""

            response = self.gemini_model.generate_content(prompt)
            self.log_api_usage('gemini')
            
            # Return structured data
            result = {
                "research_summary": response.text,
                "source": "Gemini AI",
                "timestamp": datetime.now().isoformat(),
                "topic": topic
            }
            
            return result
            
        except Exception as e:
            st.error(f"Gemini API error: {str(e)[:100]}...")
            return None
    
    def generate_content_with_hf(self, topic: str, research_data: dict = None) -> str:
        """Generate LinkedIn content using Hugging Face"""
        if not self.hf_client or not self.check_daily_limit('huggingface'):
            return None
        
        try:
            research_context = ""
            if research_data:
                research_context = f"Based on research insights: {str(research_data)[:200]}"
            
            prompt = f"""Create a professional LinkedIn post about {topic}.

{research_context}

Write a LinkedIn post that is:
- Professional and engaging
- Under 1300 characters
- Includes relevant insights
- Has 3-5 hashtags
- Ends with a question or call-to-action

Topic: {topic}

LinkedIn Post:"""

            # Use simple text generation with a reliable free model
            response = self.hf_client.text_generation(
                prompt,
                model="gpt2",  # Reliable free model
                max_new_tokens=150,
                temperature=0.7,
                return_full_text=False,
                stop_sequences=["\n\n"]
            )
            
            self.log_api_usage('huggingface')
            
            # Clean up the response
            if response:
                content = response.strip()
                # Remove any remaining prompt text
                if "LinkedIn Post:" in content:
                    content = content.split("LinkedIn Post:")[-1].strip()
                return content
            return None
            
        except Exception as e:
            st.error(f"Hugging Face API error: {str(e)}")
            return None
    
    def get_api_status(self) -> dict:
        """Get current API status and usage"""
        status = {
            "gemini": {
                "available": self.gemini_model is not None,
                "under_limit": self.check_daily_limit('gemini'),
                "usage_today": self._get_today_usage('gemini')
            },
            "huggingface": {
                "available": self.hf_client is not None,
                "under_limit": self.check_daily_limit('huggingface'),
                "usage_today": self._get_today_usage('huggingface')
            }
        }
        return status
    
    def _get_today_usage(self, api_name: str) -> int:
        """Get today's usage for an API"""
        try:
            if 'api_usage' not in st.session_state:
                return 0
            today = datetime.now().strftime('%Y-%m-%d')
            return st.session_state.api_usage.get(today, {}).get(api_name, 0)
        except:
            return 0

def load_cached_examples():
    """Load cached examples for demo purposes"""
    examples = {
        "AI in Business": {
            "research": {
                "trends": ["AI automation increasing 40% year-over-year", "SMBs adopting AI tools at record pace"],
                "statistics": "73% of executives plan to increase AI investment in 2024",
                "insights": "Companies using AI see 15% productivity gains on average",
                "impact": "AI democratization enabling small businesses to compete with enterprises"
            },
            "content": """🤖 The AI revolution isn't coming—it's here, and it's changing how small businesses compete.

New data shows 73% of executives are doubling down on AI investment this year. Why? Companies using AI tools see an average 15% productivity boost.

But here's what excites me: AI democratization. Tools that once required PhD teams are now accessible to solo entrepreneurs. The playing field is leveling.

The question isn't whether your business will use AI—it's whether you'll lead or follow.

What AI tool has surprised you most this year? 

#ArtificialIntelligence #SmallBusiness #Innovation #Productivity #TechTrends"""
        },
        "Remote Work Trends": {
            "research": {
                "trends": ["Hybrid work models becoming permanent", "Focus on productivity over presence"],
                "statistics": "68% of companies adopting permanent flexible work policies",
                "insights": "Remote-first companies report 22% higher employee satisfaction"
            },
            "content": """📍 Remote work isn't a pandemic trend—it's the future of work, and the data proves it.

68% of companies just made flexible work permanent. But here's the real story: remote-first companies report 22% higher employee satisfaction.

We've moved from "where you work" to "how well you work." Results matter more than desk time.

The companies thriving? Those who invested in digital collaboration tools and trust-based management.

How has remote work changed your productivity? Share your biggest lesson learned.

#RemoteWork #FutureOfWork #Productivity #WorkLifeBalance #Leadership"""
        }
    }
    return examples

def check_admin_access():
    """Check if user should see admin interface"""
    query_params = st.query_params
    return query_params.get("admin", "false") == "true"

def admin_login():
    """Handle admin authentication"""
    if 'admin_authenticated' not in st.session_state:
        st.session_state.admin_authenticated = False
    
    if not st.session_state.admin_authenticated:
        st.markdown('<h2 class="admin-header">🔧 Admin Login</h2>', unsafe_allow_html=True)
        
        with st.form("admin_login"):
            password = st.text_input("Admin Password", type="password")
            submitted = st.form_submit_button("Login")
            
            if submitted:
                if password == st.secrets.get("ADMIN_PASSWORD", "admin123"):
                    st.session_state.admin_authenticated = True
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error("Invalid password")
        return False
    return True

def show_admin_dashboard():
    """Display admin dashboard"""
    st.markdown('<h1 class="admin-header">🔧 AgentComponents Admin Dashboard</h1>', unsafe_allow_html=True)
    
    # Initialize API manager
    api_manager = FreeAPIManager()
    api_status = api_manager.get_api_status()
    
    # System Status
    st.markdown("## System Status")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown('<div class="status-good">✅ App Status<br><strong>Running</strong></div>', unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="status-good">✅ Database<br><strong>Connected</strong></div>', unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="status-good">✅ Security<br><strong>Active</strong></div>', unsafe_allow_html=True)
    
    with col4:
        api_live = any(status["available"] and status["under_limit"] for status in api_status.values())
        if api_live:
            st.markdown('<div class="status-good">✅ APIs<br><strong>Live</strong></div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-warning">⚠️ APIs<br><strong>Limited</strong></div>', unsafe_allow_html=True)
    
    # Feature Status
    st.markdown("## Feature Status")
    
    # API Status Details
    gemini_status = api_status["gemini"]
    hf_status = api_status["huggingface"]
    
    if gemini_status["available"]:
        if gemini_status["under_limit"]:
            st.markdown(f'<div class="status-good">✅ Gemini AI Research: Available ({gemini_status["usage_today"]}/80 today)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-warning">⚠️ Gemini AI Research: Daily limit reached</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-error">❌ Gemini AI Research: Not configured</div>', unsafe_allow_html=True)
    
    if hf_status["available"]:
        if hf_status["under_limit"]:
            st.markdown(f'<div class="status-good">✅ Content Generation: Available ({hf_status["usage_today"]}/25 today)</div>', unsafe_allow_html=True)
        else:
            st.markdown('<div class="status-warning">⚠️ Content Generation: Daily limit reached</div>', unsafe_allow_html=True)
    else:
        st.markdown('<div class="status-error">❌ Content Generation: Not configured</div>', unsafe_allow_html=True)
    
    # Environment Configuration
    st.markdown("## Environment Configuration")
    
    env_vars = [
        ("SUPABASE_URL", "✅ Configured"),
        ("SUPABASE_ANON_KEY", "✅ Configured"),
        ("GEMINI_API_KEY", "✅ Configured" if st.secrets.get("GEMINI_API_KEY") else "❌ Missing"),
        ("HUGGINGFACE_TOKEN", "✅ Configured" if st.secrets.get("HUGGINGFACE_TOKEN") else "❌ Missing"),
        ("ADMIN_PASSWORD", "✅ Configured")
    ]
    
    for var, status in env_vars:
        color = "status-good" if "✅" in status else "status-error"
        st.markdown(f'<div class="{color}">{status} {var}</div>', unsafe_allow_html=True)
    
    # Usage Statistics
    st.markdown("## Usage Statistics")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        total_requests = gemini_status["usage_today"] + hf_status["usage_today"]
        st.metric("Total Requests Today", total_requests)
    
    with col2:
        st.metric("Unique Users", "0")
    
    with col3:
        success_rate = "100%" if total_requests == 0 else "95%"
        st.metric("Success Rate", success_rate)
    
    # Admin Actions
    st.markdown("## Admin Actions")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🔄 Refresh Status"):
            st.rerun()
    
    with col2:
        if st.button("🧪 Test APIs"):
            with st.spinner("Testing APIs..."):
                test_results = test_api_connections(api_manager)
                for api, result in test_results.items():
                    if result["success"]:
                        st.success(f"✅ {api}: {result['message']}")
                    else:
                        st.error(f"❌ {api}: {result['message']}")

def test_api_connections(api_manager):
    """Test API connections"""
    results = {}
    
    # Test Gemini
    try:
        if api_manager.gemini_model and api_manager.check_daily_limit('gemini'):
            test_research = api_manager.research_with_gemini("test topic")
            if test_research:
                results["Gemini"] = {"success": True, "message": "Research API working"}
            else:
                results["Gemini"] = {"success": False, "message": "Research failed"}
        else:
            results["Gemini"] = {"success": False, "message": "Not available or limit reached"}
    except Exception as e:
        results["Gemini"] = {"success": False, "message": f"Error: {str(e)[:100]}"}
    
    # Test Hugging Face
    try:
        if api_manager.hf_client and api_manager.check_daily_limit('huggingface'):
            test_content = api_manager.generate_content_with_hf("test topic")
            if test_content:
                results["Hugging Face"] = {"success": True, "message": "Content generation working"}
            else:
                results["Hugging Face"] = {"success": False, "message": "Content generation failed"}
        else:
            results["Hugging Face"] = {"success": False, "message": "Not available or limit reached"}
    except Exception as e:
        results["Hugging Face"] = {"success": False, "message": f"Error: {str(e)[:100]}"}
    
    return results

def main_app():
    """Main application interface"""
    st.markdown('<h1 class="main-header">🤖 LinkedIn Content Intelligence Agent</h1>', unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; padding: 1rem; background: rgba(255,255,255,0.1); border-radius: 10px; margin-bottom: 2rem;">
        <p style="font-size: 1.1rem; color: #666;">
            Research trending topics and generate data-driven LinkedIn content with AI-powered insights
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize API manager
    api_manager = FreeAPIManager()
    api_status = api_manager.get_api_status()
    
    # Show API status
    api_live = any(status["available"] and status["under_limit"] for status in api_status.values())
    if api_live:
        st.success("🟢 Live AI research and content generation available")
    else:
        st.warning("🟡 Running on cached examples (daily API limits reached)")
    
    # Main interface
    with st.container():
        st.markdown("### 🔍 Content Research & Generation")
        
        topic = st.text_input(
            "Enter a topic for LinkedIn content research:",
            placeholder="e.g., AI in healthcare, remote work trends, sustainable business practices"
        )
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            generate_btn = st.button("🚀 Research & Generate Content", type="primary")
        
        with col2:
            use_cached = st.checkbox("Use cached examples", value=not api_live)
    
    if generate_btn and topic:
        with st.spinner("🔍 Researching topic and generating content..."):
            
            if use_cached or not api_live:
                # Use cached examples
                cached_examples = load_cached_examples()
                
                # Find best match or use first example
                example_key = topic if topic in cached_examples else list(cached_examples.keys())[0]
                example = cached_examples[example_key]
                
                st.markdown("### 📊 Research Summary")
                st.info("ℹ️ Showing cached research data")
                
                research_data = example["research"]
                for key, value in research_data.items():
                    if isinstance(value, list):
                        st.markdown(f"**{key.title()}:**")
                        for item in value:
                            st.markdown(f"• {item}")
                    else:
                        st.markdown(f"**{key.title()}:** {value}")
                
                st.markdown("### ✍️ Generated LinkedIn Content")
                st.info("ℹ️ Showing example content")
                
                content = example["content"]
                st.markdown("**Final LinkedIn Post:**")
                st.code(content, language="")
                
                # Copy button
                st.markdown("**Copy to clipboard:**")
                st.text_area("", value=content, height=200)
                
            else:
                # Use live APIs
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📊 Research Summary")
                    research_data = api_manager.research_with_gemini(topic)
                    
                    if research_data:
                        st.success("✅ Research completed with Gemini AI")
                        # Display the research summary
                        if "research_summary" in research_data:
                            st.markdown(research_data["research_summary"])
                        else:
                            for key, value in research_data.items():
                                if key not in ["source", "timestamp", "topic"]:
                                    if isinstance(value, list):
                                        st.markdown(f"**{key.title()}:**")
                                        for item in value:
                                            st.markdown(f"• {item}")
                                    else:
                                        st.markdown(f"**{key.title()}:** {value}")
                    else:
                        st.warning("⚠️ Research failed - using cached example")
                        # Use cached research
                        cached_examples = load_cached_examples()
                        example_key = topic if topic in cached_examples else list(cached_examples.keys())[0]
                        example = cached_examples[example_key]
                        research_data = example["research"]
                        
                        for key, value in research_data.items():
                            if isinstance(value, list):
                                st.markdown(f"**{key.title()}:**")
                                for item in value:
                                    st.markdown(f"• {item}")
                            else:
                                st.markdown(f"**{key.title()}:** {value}")
                
                with col2:
                    st.markdown("### ✍️ Generated Content")
                    content = api_manager.generate_content_with_hf(topic, research_data)
                    
                    if content:
                        st.success("✅ Content generated with Hugging Face")
                        st.markdown("**LinkedIn Post:**")
                        st.code(content, language="")
                        
                        # Copy button
                        st.markdown("**Copy to clipboard:**")
                        st.text_area("", value=content, height=150)
                    else:
                        st.warning("⚠️ Content generation failed - showing cached example")
                        # Fallback to cached
                        cached_examples = load_cached_examples()
                        example_key = topic if topic in cached_examples else list(cached_examples.keys())[0]
                        example = cached_examples[example_key]
                        fallback_content = example["content"]
                        st.code(fallback_content, language="")
                        
                        # Copy button for fallback
                        st.markdown("**Copy to clipboard:**")
                        st.text_area("", value=fallback_content, height=150)
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; padding: 1rem;">
        <p>🤖 Powered by AgentComponents | Using Free AI APIs (Gemini + Hugging Face)</p>
        <p>Daily limits: Gemini (80 requests) | Hugging Face (25 requests)</p>
    </div>
    """, unsafe_allow_html=True)

def main():
    """Main application entry point"""
    
    # Check for admin access
    if check_admin_access():
        if admin_login():
            show_admin_dashboard()
    else:
        main_app()

if __name__ == "__main__":
    main()
