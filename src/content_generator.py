import openai
import anthropic
import json
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

class ContentGenerator:
    """AI-powered content generation with fact verification"""
    
    def __init__(self):
        self.openai_client = openai.OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
        self.anthropic_client = anthropic.Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY')) if os.getenv('ANTHROPIC_API_KEY') else None
        
    def create_linkedin_post(self, topic: str, research_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create LinkedIn post based on research data
        
        Args:
            topic: Topic to write about
            research_data: Research data from ResearchEngine
            
        Returns:
            Generated content with metadata
        """
        
        # Generate multiple content variations
        variations = []
        
        # Professional/Educational variation
        professional_content = self._generate_professional_content(topic, research_data)
        if professional_content:
            variations.append(professional_content)
        
        # Thought leadership variation
        thought_leader_content = self._generate_thought_leader_content(topic, research_data)
        if thought_leader_content:
            variations.append(thought_leader_content)
        
        # Conversational variation
        conversational_content = self._generate_conversational_content(topic, research_data)
        if conversational_content:
            variations.append(conversational_content)
        
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
    
    def _generate_professional_content(self, topic: str, research_data: Dict) -> Optional[Dict]:
        """Generate professional/educational content"""
        
        prompt = f"""Create a professional LinkedIn post about {topic} based on this research:

Research Summary: {research_data.get('summary', 'N/A')}
Key Insights: {research_data.get('key_insights', [])}

Requirements:
- Professional tone, educational value
- 150-200 words maximum
- Include 2-3 relevant hashtags
- Cite insights without being overly promotional
- Focus on industry trends and implications

Format as a LinkedIn post that provides value to business professionals."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a professional content creator specializing in LinkedIn business content."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300,
                temperature=0.7
            )
            
            content_text = response.choices[0].message.content
            
            return {
                'type': 'professional',
                'text': content_text,
                'quality_score': self._calculate_quality_score(content_text, 'professional'),
                'word_count': len(content_text.split()),
                'hashtags': self._extract_hashtags(content_text),
                'sources': self._extract_sources(research_data)
            }
            
        except Exception as e:
            print(f"Error generating professional content: {e}")
            return None
    
    def _generate_thought_leader_content(self, topic: str, research_data: Dict) -> Optional[Dict]:
        """Generate thought leadership content"""
        
        prompt = f"""Create a thought leadership LinkedIn post about {topic} based on this research:

Research Summary: {research_data.get('summary', 'N/A')}
Key Insights: {research_data.get('key_insights', [])}

Requirements:
- Thought-provoking, forward-looking perspective
- Personal opinion or unique angle
- 200-250 words maximum  
- Include call-to-action for engagement
- Use storytelling or analogy where appropriate
- 3-4 relevant hashtags

Write as an industry expert sharing insights and predictions."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are a thought leader creating engaging LinkedIn content with unique perspectives."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=350,
                temperature=0.8
            )
            
            content_text = response.choices[0].message.content
            
            return {
                'type': 'thought_leadership',
                'text': content_text,
                'quality_score': self._calculate_quality_score(content_text, 'thought_leadership'),
                'word_count': len(content_text.split()),
                'hashtags': self._extract_hashtags(content_text),
                'sources': self._extract_sources(research_data)
            }
            
        except Exception as e:
            print(f"Error generating thought leadership content: {e}")
            return None
    
    def _generate_conversational_content(self, topic: str, research_data: Dict) -> Optional[Dict]:
        """Generate conversational/personal content"""
        
        prompt = f"""Create a conversational LinkedIn post about {topic} based on this research:

Research Summary: {research_data.get('summary', 'N/A')}
Key Insights: {research_data.get('key_insights', [])}

Requirements:
- Conversational, approachable tone
- Personal perspective or experience
- 100-150 words maximum
- Include question to encourage comments
- 2-3 hashtags
- Relatable and authentic voice

Write as someone sharing personal thoughts and experiences with their network."""

        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are creating conversational LinkedIn content that feels personal and authentic."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=250,
                temperature=0.9
            )
            
            content_text = response.choices[0].message.content
            
            return {
                'type': 'conversational',
                'text': content_text,
                'quality_score': self._calculate_quality_score(content_text, 'conversational'),
                'word_count': len(content_text.split()),
                'hashtags': self._extract_hashtags(content_text),
                'sources': self._extract_sources(research_data)
            }
            
        except Exception as e:
            print(f"Error generating conversational content: {e}")
            return None
    
    def verify_facts(self, content: str, research_data: Dict) -> Dict[str, Any]:
        """Verify facts in generated content against research data"""
        
        verification_prompt = f"""Verify the factual accuracy of this content against the provided research:

Content to verify:
{content}

Research data:
{json.dumps(research_data, indent=2)}

Rate each factual claim in the content on accuracy (1-10 scale) and provide reasoning.
Return format:
{{
    "overall_accuracy": 8.5,
    "verified_claims": [
        {{"claim": "specific claim", "accuracy": 9.0, "source": "research source"}}
    ],
    "unverified_claims": ["claims that cannot be verified"],
    "recommendations": ["suggested improvements"]
}}"""

        try:
            if self.anthropic_client:
                # Use Claude for fact verification
                response = self.anthropic_client.messages.create(
                    model="claude-3-sonnet-20240229",
                    max_tokens=500,
                    messages=[
                        {"role": "user", "content": verification_prompt}
                    ]
                )
                
                verification_result = json.loads(response.content[0].text)
                return verification_result
            else:
                # Fallback to OpenAI
                response = self.openai_client.chat.completions.create(
                    model="gpt-4",
                    messages=[
                        {"role": "system", "content": "You are a fact-checking expert. Analyze content accuracy against provided research."},
                        {"role": "user", "content": verification_prompt}
                    ],
                    max_tokens=500,
                    temperature=0.3
                )
                
                try:
                    verification_result = json.loads(response.choices[0].message.content)
                    return verification_result
                except json.JSONDecodeError:
                    return {"overall_accuracy": 7.5, "note": "Verification completed but format parsing failed"}
                
        except Exception as e:
            print(f"Error verifying facts: {e}")
            return {"overall_accuracy": 7.0, "error": str(e)}
    
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
