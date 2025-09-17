import os
import json
import requests
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import google.generativeai as genai
from huggingface_hub import InferenceClient
import time

class FreeAPIManager:
    """Manages free-tier API calls with enhanced security and monitoring"""
    
    def __init__(self, database_manager=None):
        self.db = database_manager
        
        # Initialize APIs
        self.hf_client = None
        self.gemini_model = None
        self.anthropic_client = None
        
        # Rate limits (daily)
        self.limits = {
            'gemini': int(os.getenv('GEMINI_DAILY_LIMIT', 100)),
            'huggingface': int(os.getenv('HUGGINGFACE_DAILY_LIMIT', 30)),
            'anthropic': int(os.getenv('ANTHROPIC_DAILY_LIMIT', 10))
        }
        
        # Set up APIs
        self._initialize_apis()
    
    def _initialize_apis(self):
        """Initialize all available APIs"""
        try:
            # Set up Hugging Face
            hf_token = os.getenv('HUGGINGFACE_TOKEN')
            if hf_token:
                self.hf_client = InferenceClient(token=hf_token)
            
            # Set up Gemini
            gemini_key = os.getenv('GEMINI_API_KEY')
            if gemini_key:
                genai.configure(api_key=gemini_key)
                self.gemini_model = genai.GenerativeModel('gemini-pro')
            
            # Set up Anthropic (optional)
            anthropic_key = os.getenv('ANTHROPIC_API_KEY')
            if anthropic_key:
                try:
                    import anthropic
                    self.anthropic_client = anthropic.Anthropic(api_key=anthropic_key)
                except ImportError:
                    print("Anthropic library not installed")
                    
        except Exception as e:
            print(f"API initialization error: {e}")
    
    def check_daily_limit(self, api_name: str) -> bool:
        """Check if we're under daily API limits using database"""
        if not self.db:
            return self._fallback_check_limit(api_name)
        
        try:
            # Get today's usage from database
            usage_data = self.db.get_api_usage(api_name=api_name)
            current_usage = len([u for u in usage_data if u['success']])
            
            limit = self.limits.get(api_name, 100)
            return current_usage < limit
            
        except Exception as e:
            print(f"Database check failed: {e}")
            return self._fallback_check_limit(api_name)
    
    def _fallback_check_limit(self, api_name: str) -> bool:
        """Fallback rate limiting using file storage"""
        try:
            with open('api_usage_fallback.json', 'r') as f:
                usage = json.load(f)
        except FileNotFoundError:
            usage = {}
        
        today = datetime.now().strftime('%Y-%m-%d')
        daily_usage = usage.get(today, {})
        
        current_usage = daily_usage.get(api_name, 0)
        limit = self.limits.get(api_name, 100)
        
        return current_usage < limit
    
    def log_api_usage(self, api_name: str, success: bool = True, error_message: str = None):
        """Log API usage with enhanced tracking"""
        if self.db:
            try:
                self.db.log_api_usage(api_name, success, error_message)
            except Exception as e:
                print(f"Database logging failed: {e}")
                self._fallback_log_usage(api_name, success, error_message)
        else:
            self._fallback_log_usage(api_name, success, error_message)
    
    def _fallback_log_usage(self, api_name: str, success: bool, error_message: str):
        """Fallback usage logging"""
        try:
            with open('api_usage_fallback.json', 'r') as f:
                usage = json.load(f)
        except FileNotFoundError:
            usage = {}
        
        today = datetime.now().strftime('%Y-%m-%d')
        if today not in usage:
            usage[today] = {}
        
        usage[today][api_name] = usage[today].get(api_name, 0) + 1
        
        with open('api_usage_fallback.json', 'w') as f:
            json.dump(usage, f)
    
    def research_with_gemini(self, topic: str) -> Optional[Dict[str, Any]]:
        """Use Gemini for research with enhanced error handling"""
        if not self.gemini_model:
            return None
        
        if not self.check_daily_limit('gemini'):
            print("Gemini daily limit reached")
            return None
        
        try:
            prompt = self._create_research_prompt(topic)
            
            # Add timeout and retry logic
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = self.gemini_model.generate_content(
                        prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=0.7,
                            top_p=0.8,
                            top_k=40,
                            max_output_tokens=1000,
                        )
                    )
                    
                    self.log_api_usage('gemini', success=True)
                    
                    # Parse and validate response
                    result = self._parse_gemini_response(response.text, topic)
                    if result:
                        return result
                    
                except Exception as e:
                    if attempt == max_retries - 1:
                        self.log_api_usage('gemini', success=False, error_message=str(e))
                        print(f"Gemini API error after {max_retries} attempts: {e}")
                    else:
                        time.sleep(2 ** attempt)  # Exponential backoff
                        continue
            
            return None
            
        except Exception as e:
            self.log_api_usage('gemini', success=False, error_message=str(e))
            print(f"Gemini API error: {e}")
            return None
    
    def _create_research_prompt(self, topic: str) -> str:
        """Create optimized research prompt"""
        return f"""Research the business topic "{topic}" and provide comprehensive insights.

Please analyze:
1. Current market trends and developments
2. Key insights that business professionals should know
3. Why this topic is important or trending right now
4. Practical implications for businesses

Format your response as JSON:
{{
    "summary": "A comprehensive summary in 2-3 sentences",
    "key_insights": [
        "First key insight about market trends",
        "Second insight about business implications", 
        "Third insight about future outlook"
    ],
    "trending_reason": "Why this topic is currently relevant",
    "business_impact": "How this affects businesses today"
}}

Keep insights factual, professional, and actionable. Focus on information that would be valuable for LinkedIn content."""
    
    def _parse_gemini_response(self, response_text: str, topic: str) -> Optional[Dict[str, Any]]:
        """Parse and validate Gemini response"""
        try:
            # Extract JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                parsed_data = json.loads(json_match.group())
                
                # Validate required fields
                required_fields = ['summary', 'key_insights', 'trending_reason']
                if all(field in parsed_data for field in required_fields):
                    return parsed_data
            
            # Fallback: Create structured response from text
            return {
                "summary": f"Research analysis on {topic}: " + response_text[:200] + "...",
                "key_insights": [
                    f"Current developments in {topic} are driving business interest",
                    f"Organizations are exploring {topic} for competitive advantage",
                    f"Market trends indicate growing adoption of {topic} solutions"
                ],
                "trending_reason": "Increasing business relevance and market activity",
                "business_impact": "Significant implications for strategic planning and operations"
            }
            
        except json.JSONDecodeError as e:
            print(f"JSON parsing error: {e}")
            return None
        except Exception as e:
            print(f"Response parsing error: {e}")
            return None
    
    def generate_content_with_hf(self, topic: str, research_data: Dict) -> Optional[List[Dict]]:
        """Generate content using Hugging Face with improved prompting"""
        if not self.hf_client:
            return None
        
        if not self.check_daily_limit('huggingface'):
            print("Hugging Face daily limit reached")
            return None
        
        try:
            # Create content generation prompt
            prompt = self._create_content_prompt(topic, research_data)
            
            # Try multiple models for better results
            models = [
                "microsoft/DialoGPT-medium",
                "facebook/blenderbot-400M-distill",
                "microsoft/DialoGPT-small"
            ]
            
            for model in models:
                try:
                    response = self.hf_client.text_generation(
                        prompt,
                        model=model,
                        max_new_tokens=300,
                        temperature=0.7,
                        do_sample=True,
                        top_p=0.9
                    )
                    
                    if response and len(response.strip()) > 50:
                        self.log_api_usage('huggingface', success=True)
                        return self._format_content_response(response, topic, research_data)
                
                except Exception as e:
                    print(f"Model {model} failed: {e}")
                    continue
            
            # If all models fail, log error
            self.log_api_usage('huggingface', success=False, error_message="All models failed")
            return None
            
        except Exception as e:
            self.log_api_usage('huggingface', success=False, error_message=str(e))
            print(f"Hugging Face API error: {e}")
            return None
    
    def _create_content_prompt(self, topic: str, research_data: Dict) -> str:
        """Create optimized content generation prompt"""
        summary = research_data.get('summary', f'Research on {topic}')
        insights = research_data.get('key_insights', [])
        
        insights_text = "\n".join([f"- {insight}" for insight in insights[:3]])
        
        return f"""Write a professional LinkedIn post about {topic}.

Research insights:
{summary}

Key points:
{insights_text}

Create engaging LinkedIn content that:
- Starts with a compelling hook
- Shares valuable insights
- Includes a call-to-action question
- Uses professional but conversational tone
- Stays under 200 words
- Includes 2-3 relevant hashtags

Write the post now:"""
    
    def _format_content_response(self, response: str, topic: str, research_data: Dict) -> List[Dict]:
        """Format the content response into structured data"""
        # Clean up the response
        content_text = response.strip()
        
        # Extract hashtags
        import re
        hashtags = re.findall(r'#\w+', content_text)
        
        # Calculate quality score based on various factors
        quality_score = self._calculate_content_quality(content_text, topic)
        
        return [{
            'type': 'professional',
            'text': content_text,
            'quality_score': quality_score,
            'word_count': len(content_text.split()),
            'hashtags': hashtags[:5],  # Limit to 5 hashtags
            'sources': ['AI-generated based on research'],
            'generation_method': 'huggingface'
        }]
    
    def _calculate_content_quality(self, content: str, topic: str) -> float:
        """Calculate content quality score"""
        score = 5.0  # Base score
        
        # Length check (optimal range: 100-200 words)
        word_count = len(content.split())
        if 100 <= word_count <= 200:
            score += 1.5
        elif 50 <= word_count <= 250:
            score += 1.0
        
        # Hashtag presence
        hashtag_count = content.count('#')
        if 2 <= hashtag_count <= 4:
            score += 1.0
        
        # Question presence (engagement)
        if '?' in content:
            score += 0.5
        
        # Topic relevance
        if topic.lower() in content.lower():
            score += 1.0
        
        # Professional language indicators
        professional_words = ['insights', 'trends', 'business', 'strategy', 'innovation']
        for word in professional_words:
            if word in content.lower():
                score += 0.2
                break
        
        # Avoid excessive enthusiasm
        exclamation_count = content.count('!')
        if exclamation_count > 3:
            score -= 0.5
        
        return min(score, 10.0)
    
    def research_with_anthropic(self, topic: str) -> Optional[Dict[str, Any]]:
        """Use Anthropic Claude for research (if available)"""
        if not self.anthropic_client:
            return None
        
        if not self.check_daily_limit('anthropic'):
            print("Anthropic daily limit reached")
            return None
        
        try:
            prompt = f"""Research the business topic "{topic}" and provide professional insights.

Please provide:
1. A comprehensive summary (2-3 sentences)
2. Three key business insights
3. Why this topic is currently relevant
4. Business implications

Format as JSON for easy parsing."""
            
            response = self.anthropic_client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=500,
                temperature=0.7,
                messages=[{"role": "user", "content": prompt}]
            )
            
            self.log_api_usage('anthropic', success=True)
            
            # Parse response
            return self._parse_anthropic_response(response.content[0].text, topic)
            
        except Exception as e:
            self.log_api_usage('anthropic', success=False, error_message=str(e))
            print(f"Anthropic API error: {e}")
            return None
    
    def _parse_anthropic_response(self, response_text: str, topic: str) -> Dict[str, Any]:
        """Parse Anthropic response"""
        try:
            # Try to parse JSON
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            
            if json_match:
                return json.loads(json_match.group())
            
            # Fallback to structured parsing
            return {
                "summary": response_text[:200] + "..." if len(response_text) > 200 else response_text,
                "key_insights": [
                    f"Analysis of {topic} reveals important market dynamics",
                    f"Current trends in {topic} are reshaping business strategies",
                    f"Organizations should consider {topic} in their planning"
                ],
                "trending_reason": "Growing business relevance and market interest",
                "business_impact": "Significant implications for strategic decision-making"
            }
            
        except Exception as e:
            print(f"Anthropic response parsing error: {e}")
            return {
                "summary": f"Professional analysis of {topic} and its business implications",
                "key_insights": [f"Key insights about {topic} from industry analysis"],
                "trending_reason": "Current market relevance",
                "business_impact": "Strategic considerations for businesses"
            }
    
    def can_use_live_research(self) -> bool:
        """Check if any APIs are available for live research"""
        available_apis = []
        
        if self.gemini_model and self.check_daily_limit('gemini'):
            available_apis.append('gemini')
        
        if self.hf_client and self.check_daily_limit('huggingface'):
            available_apis.append('huggingface')
        
        if self.anthropic_client and self.check_daily_limit('anthropic'):
            available_apis.append('anthropic')
        
        return len(available_apis) > 0
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get current usage statistics"""
        if self.db:
            try:
                return self.db.get_daily_api_counts()
            except Exception as e:
                print(f"Database stats error: {e}")
                return self._fallback_get_stats()
        else:
            return self._fallback_get_stats()
    
    def _fallback_get_stats(self) -> Dict[str, int]:
        """Fallback usage statistics"""
        try:
            with open('api_usage_fallback.json', 'r') as f:
                usage = json.load(f)
            
            today = datetime.now().strftime('%Y-%m-%d')
            return usage.get(today, {'gemini': 0, 'huggingface': 0, 'anthropic': 0})
            
        except FileNotFoundError:
            return {'gemini': 0, 'huggingface': 0, 'anthropic': 0}
    
    def get_available_apis(self) -> List[str]:
        """Get list of currently available APIs"""
        available = []
        
        if self.gemini_model and self.check_daily_limit('gemini'):
            available.append('gemini')
        
        if self.hf_client and self.check_daily_limit('huggingface'):
            available.append('huggingface')
        
        if self.anthropic_client and self.check_daily_limit('anthropic'):
            available.append('anthropic')
        
        return available
    
    def research_with_best_available_api(self, topic: str) -> Optional[Dict[str, Any]]:
        """Use the best available API for research"""
        # Try APIs in order of preference
        api_priority = ['anthropic', 'gemini', 'huggingface']
        
        for api_name in api_priority:
            if api_name == 'anthropic' and self.anthropic_client and self.check_daily_limit('anthropic'):
                result = self.research_with_anthropic(topic)
                if result:
                    return result
            
            elif api_name == 'gemini' and self.gemini_model and self.check_daily_limit('gemini'):
                result = self.research_with_gemini(topic)
                if result:
                    return result
        
        return None
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health and availability"""
        health = {
            'apis_available': self.get_available_apis(),
            'total_apis': len([api for api in [self.gemini_model, self.hf_client, self.anthropic_client] if api]),
            'usage_stats': self.get_usage_stats(),
            'can_research': self.can_use_live_research()
        }
        
        return health
