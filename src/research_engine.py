import requests
import feedparser
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

# Make praw optional
try:
    import praw
except ImportError:
    praw = None

load_dotenv()

class ResearchEngine:
    """Multi-source research engine for trending topic analysis"""
    
    def __init__(self):
        self.sources = {
            'techcrunch': 'https://techcrunch.com/feed/',
            'wired': 'https://www.wired.com/feed/rss',
            'oreilly': 'https://feeds.feedburner.com/oreilly/radar',
            'hacker_news': 'https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=10'
        }
        self.reddit_client = self._init_reddit()
        
    def _init_reddit(self) -> Optional:
        """Initialize Reddit client if credentials available"""
        if praw is None:
            return None
        try:
            return praw.Reddit(
                client_id=os.getenv('REDDIT_CLIENT_ID', ''),
                client_secret=os.getenv('REDDIT_CLIENT_SECRET', ''),
                user_agent='LinkedInAgent/1.0'
            )
        except:
            return None
    
    def research_topic(self, topic: str) -> Dict[str, Any]:
        """
        Research a topic across multiple sources
        
        Args:
            topic: Topic to research
            
        Returns:
            Comprehensive research data
        """
        research_data = {
            'topic': topic,
            'timestamp': datetime.now().isoformat(),
            'sources_analyzed': [],
            'key_insights': [],
            'trending_discussions': [],
            'metrics': {
                'sources_count': 0,
                'articles_analyzed': 0,
                'discussions_found': 0,
                'confidence_score': 0.0
            }
        }
        
        # Tech news analysis
        tech_articles = self._analyze_tech_news(topic)
        research_data['tech_articles'] = tech_articles
        research_data['sources_analyzed'].extend(['TechCrunch', 'Wired', 'O\'Reilly'])
        research_data['metrics']['articles_analyzed'] = len(tech_articles)
        
        # Hacker News analysis
        hn_discussions = self._analyze_hacker_news(topic)
        research_data['hacker_news'] = hn_discussions
        research_data['sources_analyzed'].append('Hacker News')
        research_data['metrics']['discussions_found'] += len(hn_discussions)
        
        # Reddit analysis (if available)
        if self.reddit_client:
            reddit_discussions = self._analyze_reddit(topic)
            research_data['reddit'] = reddit_discussions
            research_data['sources_analyzed'].append('Reddit')
            research_data['metrics']['discussions_found'] += len(reddit_discussions)
        
        # Generate insights
        research_data['key_insights'] = self._extract_insights(research_data)
        research_data['summary'] = self._generate_summary(research_data)
        research_data['metrics']['sources_count'] = len(research_data['sources_analyzed'])
        research_data['metrics']['confidence_score'] = self._calculate_confidence(research_data)
        
        return research_data
    
    def _analyze_tech_news(self, topic: str) -> List[Dict]:
        """Analyze tech news sources"""
        articles = []
        
        for source_name, feed_url in self.sources.items():
            if source_name == 'hacker_news':
                continue
                
            try:
                feed = feedparser.parse(feed_url)
                for entry in feed.entries[:5]:  # Limit for demo
                    if self._is_relevant(entry.title + ' ' + entry.get('summary', ''), topic):
                        articles.append({
                            'source': source_name,
                            'title': entry.title,
                            'url': entry.link,
                            'published': entry.get('published', ''),
                            'summary': entry.get('summary', '')[:200] + '...',
                            'relevance_score': self._calculate_relevance(entry.title, topic)
                        })
            except Exception as e:
                print(f"Error fetching {source_name}: {e}")
                
        return sorted(articles, key=lambda x: x['relevance_score'], reverse=True)
    
    def _analyze_hacker_news(self, topic: str) -> List[Dict]:
        """Analyze Hacker News discussions"""
        try:
            url = f"https://hn.algolia.com/api/v1/search?query={topic}&tags=story&hitsPerPage=5"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            discussions = []
            for hit in data.get('hits', []):
                discussions.append({
                    'title': hit.get('title', ''),
                    'url': hit.get('url', ''),
                    'points': hit.get('points', 0),
                    'comments': hit.get('num_comments', 0),
                    'author': hit.get('author', ''),
                    'created_at': hit.get('created_at', ''),
                    'relevance_score': self._calculate_relevance(hit.get('title', ''), topic)
                })
            
            return sorted(discussions, key=lambda x: x['points'], reverse=True)
            
        except Exception as e:
            print(f"Error fetching Hacker News: {e}")
            return []
    
    def _analyze_reddit(self, topic: str) -> List[Dict]:
        """Analyze Reddit discussions"""
        if not self.reddit_client:
            return []
            
        try:
            discussions = []
            subreddits = ['technology', 'programming', 'artificial', 'MachineLearning', 'entrepreneur']
            
            for subreddit_name in subreddits:
                try:
                    subreddit = self.reddit_client.subreddit(subreddit_name)
                    for submission in subreddit.search(topic, limit=2):
                        discussions.append({
                            'subreddit': subreddit_name,
                            'title': submission.title,
                            'url': f"https://reddit.com{submission.permalink}",
                            'score': submission.score,
                            'comments': submission.num_comments,
                            'created': datetime.fromtimestamp(submission.created_utc).isoformat(),
                            'relevance_score': self._calculate_relevance(submission.title, topic)
                        })
                except Exception as e:
                    continue
            
            return sorted(discussions, key=lambda x: x['score'], reverse=True)[:10]
            
        except Exception as e:
            print(f"Error fetching Reddit: {e}")
            return []
    
    def _is_relevant(self, text: str, topic: str) -> bool:
        """Check if text is relevant to topic"""
        text_lower = text.lower()
        topic_lower = topic.lower()
        topic_words = topic_lower.split()
        
        # Simple relevance check
        return any(word in text_lower for word in topic_words)
    
    def _calculate_relevance(self, text: str, topic: str) -> float:
        """Calculate relevance score between text and topic"""
        text_lower = text.lower()
        topic_words = topic.lower().split()
        
        matches = sum(1 for word in topic_words if word in text_lower)
        return matches / len(topic_words) if topic_words else 0.0
    
    def _extract_insights(self, data: Dict) -> List[str]:
        """Extract key insights from research data"""
        insights = []
        
        # Analyze article trends
        if data.get('tech_articles'):
            article_count = len(data['tech_articles'])
            insights.append(f"Found {article_count} relevant articles across major tech publications")
        
        # Analyze discussion activity
        total_discussions = data['metrics']['discussions_found']
        if total_discussions > 0:
            insights.append(f"Active discussions found across {len(data['sources_analyzed'])} platforms")
        
        # Analyze engagement patterns
        if data.get('hacker_news'):
            avg_points = sum(d['points'] for d in data['hacker_news']) / len(data['hacker_news'])
            if avg_points > 100:
                insights.append("High engagement on technical discussion platforms")
        
        return insights
    
    def _generate_summary(self, data: Dict) -> str:
        """Generate research summary"""
        topic = data['topic']
        sources = len(data['sources_analyzed'])
        articles = data['metrics']['articles_analyzed']
        
        return f"Comprehensive research on '{topic}' across {sources} major sources, analyzing {articles} articles and multiple community discussions. Research confidence: {data['metrics'].get('confidence_score', 0):.1f}/10"
    
    def _calculate_confidence(self, data: Dict) -> float:
        """Calculate confidence score for research"""
        score = 0.0
        
        # Source diversity bonus
        score += min(len(data['sources_analyzed']) * 2, 6)
        
        # Content quantity bonus
        score += min(data['metrics']['articles_analyzed'] * 0.5, 2)
        score += min(data['metrics']['discussions_found'] * 0.3, 2)
        
        return min(score, 10.0)
    
    def get_trending_topics(self) -> List[Dict[str, Any]]:
        """Get current trending topics"""
        topics = []
        
        try:
            # Analyze Hacker News front page
            url = "https://hn.algolia.com/api/v1/search?tags=front_page&hitsPerPage=20"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            topic_counts = {}
            for hit in data.get('hits', []):
                title = hit.get('title', '').lower()
                # Extract keywords (simplified)
                for word in title.split():
                    if len(word) > 4:
                        topic_counts[word] = topic_counts.get(word, 0) + hit.get('points', 0)
            
            # Sort by engagement
            sorted_topics = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
            
            for topic, score in sorted_topics[:10]:
                topics.append({
                    'topic': topic,
                    'momentum_score': min(score / 100, 1.0),
                    'platform': 'Hacker News'
                })
                
        except Exception as e:
            print(f"Error getting trending topics: {e}")
        
        return topics
