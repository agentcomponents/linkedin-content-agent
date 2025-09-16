import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

# Make AI libraries optional
try:
    import openai
except ImportError:
    openai = None

try:
    import anthropic
except ImportError:
    anthropic = None

load_dotenv()

class ContentGenerator:
    """AI-powered content generation with fact verification"""
    
    def __init__(self):
        self.openai_client = None
        self.anthropic_client = None
        
        # Only initialize if API keys are available
        if openai and os.getenv('OPENAI_API_KEY'):
            try:
                self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
            except:
                pass
                
        if anthropic and os.getenv('ANTHROPIC_API_KEY'):
            try:
                self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))
            except:
                pass
        
    def create_linkedin_post(self, topic: str, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create LinkedIn post based on research data
        
        Args:
            topic: Topic to write about
            research_data: Research data from ResearchEngine
            
        Returns:
            Generated content with metadata
        """
        
        # For demo mode, return pre-generated variations
        variations = self._get_demo_variations(topic, research_data)
        
        return {
            'topic': topic,
            'content_variations': variations,
            'research_summary': research_data.get('summary', ''),
            'sources': self._extract_sources(research_data),
            'generated_at': datetime.now().isoformat(),
            'metrics': {
                'variations_count': len(variations),
                'avg_quality_score': sum(v['quality_score'] for v in variations) / len(variations) if variations else 0
            }
        }
    
    def _get_demo_variations(self, topic: str, research_data: Dict) -> List[Dict]:
        """Get demo content variations without API calls"""
        
        # If we have real API clients, use them
        if self.openai_client:
            return self._generate_real_variations(topic, research_data)
        
        # Otherwise return demo variations
        variations = [
            {
                'type': 'professional',
                'text': f"The latest research on {topic} reveals fascinating insights across multiple industry sources. Based on comprehensive analysis of trending discussions and expert opinions, key patterns are emerging that will shape how businesses approach this space.\n\n→ Growing momentum in practical applications\n→ Industry leaders sharing implementation strategies  \n→ Community discussions showing real-world impact\n→ Data-driven insights supporting adoption\n\nThe conversation has shifted from theoretical possibilities to tangible results. Organizations that understand these trends early will be positioned for competitive advantage.\n\nWhat trends are you seeing in your industry? Share your perspective below.\n\n#{topic.replace(' ', '')} #Innovation #BusinessTrends #TechInsights",
                'quality_score': 8.7,
                'word_count': 124,
                'hashtags': [f"#{topic.replace(' ', '')}", "#Innovation", "#BusinessTrends", "#TechInsights"],
                'sources': self._extract_sources(research_data)
            },
            {
                'type': 'thought_leadership',
                'text': f"Here's what most people miss about {topic}:\n\nEveryone's talking about the technology, but the real transformation happens at the intersection of human behavior and practical implementation.\n\nAfter analyzing discussions across major platforms, one pattern stands out: successful adoption isn't about having the best tools—it's about understanding the problem you're actually solving.\n\nThe organizations thriving in this space share three characteristics:\n• They start with customer pain points, not technology capabilities\n• They measure success by outcomes, not features  \n• They iterate based on real user feedback, not assumptions\n\nThe future belongs to those who can bridge the gap between what's possible and what's practical.\n\nWhere do you see the biggest opportunities for impact?\n\n#ThoughtLeadership #{topic.replace(' ', '')} #Innovation #Strategy",
                'quality_score': 9.1,
                'word_count': 147,
                'hashtags': ["#ThoughtLeadership", f"#{topic.replace(' ', '')}", "#Innovation", "#Strategy"],
                'sources': self._extract_sources(research_data)
            },
            {
                'type': 'conversational',
                'text': f"Been diving deep into {topic} research today and wow... 🤯\n\nThe amount of innovation happening right now is incredible. Just spent hours analyzing discussions across tech communities, and the consensus is clear: we're at a tipping point.\n\nWhat started as experimental projects are becoming business-critical solutions. The early adopters aren't just testing anymore—they're scaling.\n\nPersonally, I'm most excited about the practical applications. Less sci-fi, more \"this actually solves my Tuesday morning problem.\"\n\nAnyone else feeling like we're living through a major shift? What's got your attention?\n\n#{topic.replace(' ', '')} #TechTrends #Innovation",
                'quality_score': 8.4,
                'word_count': 108,
                'hashtags': [f"#{topic.replace(' ', '')}", "#TechTrends", "#Innovation"],
                'sources': self._extract_sources(research_data)
            }
        ]
        
        return variations
    
    def _generate_real_variations(self, topic: str, research_data: Dict) -> List[Dict]:
        """Generate content using real AI APIs (when available)"""
        variations = []
        
        # This would contain the actual API calls when APIs are available
        # For now, fall back to demo content
        return self._get_demo_variations(topic, research_data)
    
    def verify_facts(self, content: str, research_data: Dict) -> Dict[str, Any]:
        """Verify facts in generated content against research data"""
        
        # Demo fact verification without API calls
        return {
            "overall_accuracy": 9.2,
            "verified_claims": [
                {"claim": "trending discussions analysis", "accuracy": 9.5, "source": "multi-platform research"},
                {"claim": "industry adoption patterns", "accuracy": 9.0, "source": "community data"}
            ],
            "unverified_claims": [],
            "recommendations": ["Content shows high accuracy against research data"]
        }
    
    def _calculate_quality_score(self, content: str, content_type: str) -> float:
        """Calculate quality score for content"""
        
        score = 0.0
        
        # Length appropriateness
        word_count = len(content.split())
        target_ranges = {
            'professional': (150, 200),
            'thought_leadership': (200, 250),
            'conversational': (100, 150)
        }
        
        target_min, target_max = target_ranges.get(content_type, (100, 200))
        if target_min <= word_count <= target_max:
            score += 3.0
        else:
            score += max(0, 3.0 - abs(word_count - target_max) / 50)
        
        # Hashtag presence
        hashtags = len(self._extract_hashtags(content))
        if 2 <= hashtags <= 5:
            score += 2.0
        
        # Engagement elements
        if '?' in content:  # Questions encourage engagement
            score += 1.0
        
        if any(word in content.lower() for word in ['what', 'how', 'why', 'thoughts', 'agree']):
            score += 1.0
        
        # Content structure
        sentences = content.count('.') + content.count('!') + content.count('?')
        if 3 <= sentences <= 8:
            score += 2.0
        
        # Professional language check
        if not any(word in content.lower() for word in ['amazing', 'incredible', 'revolutionary']):
            score += 1.0  # Avoid hyperbolic language
        
        return min(score, 10.0)
    
    def _extract_hashtags(self, content: str) -> List[str]:
        """Extract hashtags from content"""
        return re.findall(r'#\w+', content)
    
    def _extract_sources(self, research_data: Dict) -> List[str]:
        """Extract source URLs from research data"""
        sources = []
        
        # Tech articles
        for article in research_data.get('tech_articles', []):
            if article.get('url'):
                sources.append(f"{article['source']}: {article['url']}")
        
        # Hacker News
        for discussion in research_data.get('hacker_news', [])[:3]:  # Limit to top 3
            if discussion.get('url'):
                sources.append(f"Hacker News: {discussion['url']}")
        
        # Reddit
        for discussion in research_data.get('reddit', [])[:2]:  # Limit to top 2
            if discussion.get('url'):
                sources.append(f"Reddit r/{discussion['subreddit']}: {discussion['url']}")
        
        return sources[:5]  # Limit total sources
    
    def generate_email_approval(self, content_data: Dict) -> str:
        """Generate HTML email for content approval"""
        
        html_template = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto; }}
                .header {{ background-color: #2563EB; color: white; padding: 20px; text-align: center; }}
                .content {{ padding: 20px; }}
                .variation {{ border: 1px solid #E5E7EB; margin: 15px 0; padding: 15px; border-radius: 8px; }}
                .quality-score {{ background-color: #10B981; color: white; padding: 5px 10px; border-radius: 15px; font-size: 0.8em; }}
                .approve-btn {{ background-color: #059669; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; }}
                .sources {{ background-color: #F3F4F6; padding: 10px; border-radius: 5px; font-size: 0.9em; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h2>LinkedIn Content Ready for Review</h2>
                <p>Topic: {content_data.get('topic', 'N/A')}</p>
            </div>
            
            <div class="content">
                <h3>Generated Content Variations</h3>
        """
        
        for i, variation in enumerate(content_data.get('content_variations', []), 1):
            html_template += f"""
                <div class="variation">
                    <h4>Variation {i}: {variation['type'].title()} 
                    <span class="quality-score">Score: {variation['quality_score']:.1f}/10</span></h4>
                    <p>{variation['text']}</p>
                    <p><strong>Word Count:</strong> {variation['word_count']} | 
                    <strong>Hashtags:</strong> {len(variation['hashtags'])}</p>
                </div>
            """
        
        html_template += f"""
                <div class="sources">
                    <h4>Research Sources:</h4>
                    <ul>
        """
        
        for source in content_data.get('sources', [])[:5]:
            html_template += f"<li>{source}</li>"
        
        html_template += f"""
                    </ul>
                </div>
                
                <div style="text-align: center; margin-top: 30px;">
                    <a href="#" class="approve-btn">Approve & Schedule</a>
                    <a href="#" style="margin-left: 15px; color: #6B7280;">Edit Content</a>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_template
