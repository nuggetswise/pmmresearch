import os
import hashlib
import sqlite3
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import groq
import streamlit as st
from dotenv import load_dotenv
from prompt_manager import prompt_manager

# Optional DeepSeek import
try:
    from openai import OpenAI
    DEEPSEEK_AVAILABLE = True
except ImportError:
    DEEPSEEK_AVAILABLE = False
    OpenAI = None

# Optional Tavily import
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyClient = None

# Load environment variables
load_dotenv()

# --- Modular agent functions ---
def trends_agent(query: str) -> str:
    return f"Identify 3-5 key market trends for: {query} (max 100 words)"

def competitor_examples_agent(query: str) -> str:
    return f"Provide 2-3 concrete competitor examples for: {query} (max 100 words)"

def conflicts_agent(query: str) -> str:
    return f"Highlight 2-3 conflicting insights for: {query} (max 80 words)"

def recommendations_agent(query: str) -> str:
    return f"Give 3-5 actionable recommendations for: {query} (max 100 words)"

def citations_agent(query: str) -> str:
    return f"List 3-5 credible sources with URLs for: {query}"

class PMMResearchAgent:
    def __init__(self):
        # Initialize DeepSeek as primary
        self.deepseek_client = None
        self.deepseek_enabled = False
        
        if DEEPSEEK_AVAILABLE:
            deepseek_api_key = self._get_api_key("DEEPSEEK_API_KEY")
            if deepseek_api_key:
                self.deepseek_client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")
                self.deepseek_enabled = True
                print("✅ DeepSeek initialized as primary backend")
        
        # Initialize Groq as secondary
        groq_api_key = self._get_api_key("GROQ_API_KEY")
        if groq_api_key:
            self.groq_client = groq.Groq(api_key=groq_api_key)
            print("✅ Groq initialized as secondary backend")
        else:
            self.groq_client = None
            print("⚠️ Groq API key not found")
        
        # Initialize Tavily client
        tavily_api_key = self._get_api_key("TAVILY_API_KEY")
        if tavily_api_key and TAVILY_AVAILABLE:
            self.tavily_client = TavilyClient(api_key=tavily_api_key)
            self.tavily_enabled = True
            print("✅ Tavily initialized for web search")
        else:
            self.tavily_client = None
            self.tavily_enabled = False
            print("⚠️ Tavily API key not found or package not available")
        
        if not self.deepseek_enabled and not self.groq_client:
            raise ValueError("No API keys found for DeepSeek or Groq")
        
        self.cache_db = "pmm_research_cache.db"
        self.init_cache()
    
    def _get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key from Streamlit secrets or environment"""
        try:
            return st.secrets.get(key_name)
        except:
            pass
        return os.getenv(key_name)
        
    def init_cache(self):
        """Initialize SQLite cache database"""
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS research_cache (
                query_hash TEXT PRIMARY KEY,
                response TEXT,
                timestamp DATETIME,
                model_used TEXT
            )
        ''')
        conn.commit()
        conn.close()
    
    def get_cache_key(self, query: str) -> str:
        """Generate hash-based cache key for query"""
        return hashlib.md5(query.encode()).hexdigest()
    
    def get_cached_response(self, query: str) -> Optional[Dict]:
        """Retrieve cached response if available and not expired"""
        cache_key = self.get_cache_key(query)
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT response, timestamp FROM research_cache 
            WHERE query_hash = ? AND timestamp > datetime('now', '-24 hours')
        ''', (cache_key,))
        
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return json.loads(result[0])
        return None
    
    def cache_response(self, query: str, response: Dict):
        """Cache the response with timestamp"""
        cache_key = self.get_cache_key(query)
        conn = sqlite3.connect(self.cache_db)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO research_cache (query_hash, response, timestamp, model_used)
            VALUES (?, ?, datetime('now'), ?)
        ''', (cache_key, json.dumps(response), "groq-compound-beta"))
        
        conn.commit()
        conn.close()
    
    def get_web_sources(self, query: str) -> List[Dict]:
        """Get web sources using Tavily if available"""
        sources = []
        if self.tavily_enabled:
            try:
                search_result = self.tavily_client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=5,
                    include_domains=[
                        "g2.com", "capterra.com", "trustradius.com",
                        "producthunt.com", "techcrunch.com", "venturebeat.com",
                        "linkedin.com", "medium.com", "forbes.com"
                    ]
                )
                sources = search_result.get("results", [])
                print(f"🔍 Found {len(sources)} web sources via Tavily")
            except Exception as e:
                print(f"Tavily search failed: {e}")
        return sources
    
    def generate_research_report(self, query: str, prompt_name: str = "default", use_web_search: bool = True) -> Dict:
        """Generate structured research report using DeepSeek (primary) or Groq (secondary)"""
        
        # Special handling for testprompt4 (data-driven approach)
        if prompt_name == "testprompt4":
            return self._generate_data_driven_report(query)
        
        # Check cache first
        cached = self.get_cached_response(query)
        if cached:
            return cached
        
        # Get web sources if enabled
        sources = []
        source_summaries = []
        if use_web_search and self.tavily_enabled:
            sources = self.get_web_sources(query)
            for source in sources[:5]:
                summary = f"Source: {source.get('title', 'Unknown')}\n"
                summary += f"URL: {source.get('url', 'N/A')}\n"
                summary += f"Content: {source.get('content', '')[:200]}...\n"
                source_summaries.append(summary)
        
        # Get prompt from manager
        system_prompt = prompt_manager.get_prompt(prompt_name)
        
        # Enhance user prompt with web sources if available
        if source_summaries:
            user_prompt = f"""Please research and analyze: {query}

Use the following web sources to enhance your analysis:
{chr(10).join(source_summaries)}

Provide a comprehensive PMM-focused analysis with the exact structure specified above."""
        else:
            user_prompt = f"Please research and analyze: {query}\nProvide a comprehensive PMM-focused analysis with the exact structure specified above."

        # Try DeepSeek first (primary)
        if self.deepseek_enabled:
            try:
                print("🔍 Using DeepSeek (primary) for research...")
                completion = self.deepseek_client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,  # Higher limit for DeepSeek
                    stream=False
                )
                
                response_content = completion.choices[0].message.content
                
                # Structure the response
                response = {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "content": response_content,
                    "model": "deepseek-reasoner",
                    "backend": "deepseek",
                    "cached": False,
                    "sources_used": len(sources),
                    "tavily_enabled": self.tavily_enabled
                }
                
                # Cache the response
                self.cache_response(query, response)
                
                return response
                
            except Exception as e:
                print(f"⚠️ DeepSeek failed: {str(e)}")
                if self.groq_client:
                    print("🔄 Falling back to Groq...")
                else:
                    return {
                        "error": f"DeepSeek failed and no Groq fallback available: {str(e)}",
                        "query": query,
                        "timestamp": datetime.now().isoformat()
                    }
        
        # Fallback to Groq (secondary)
        if self.groq_client:
            try:
                print("🔍 Using Groq (secondary) for research...")
                # Add retry logic for rate limiting
                max_retries = 3
                retry_delay = 5  # Start with 5 seconds
                
                for attempt in range(max_retries):
                    try:
                        completion = self.groq_client.chat.completions.create(
                            model="compound-beta",
                            messages=[
                                {"role": "system", "content": system_prompt},
                                {"role": "user", "content": user_prompt}
                            ],
                            temperature=0.7,
                            top_p=1,
                            stream=False,
                            stop=None
                        )
                        break  # Success, exit retry loop
                        
                    except Exception as e:
                        if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                            print(f"Rate limit hit, waiting {retry_delay} seconds...")
                            time.sleep(retry_delay)
                            retry_delay *= 2  # Exponential backoff
                            continue
                        else:
                            raise e
                
                response_content = completion.choices[0].message.content
                
                # Structure the response
                response = {
                    "query": query,
                    "timestamp": datetime.now().isoformat(),
                    "content": response_content,
                    "model": "groq-compound-beta",
                    "backend": "groq",
                    "cached": False,
                    "sources_used": len(sources),
                    "tavily_enabled": self.tavily_enabled
                }
                
                # Cache the response
                self.cache_response(query, response)
                
                return response
                
            except Exception as e:
                return {
                    "error": f"Both DeepSeek and Groq failed: {str(e)}",
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "error": "No available backends (DeepSeek or Groq)",
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
    
    def _generate_data_driven_report(self, query: str) -> Dict:
        """Generate data-driven report using testprompt4 approach"""
        print(f"📊 Starting data-driven research for: {query}")
        
        # Get web sources using Tavily
        sources = []
        if self.tavily_enabled:
            try:
                print("🔍 Gathering web sources via Tavily...")
                search_result = self.tavily_client.search(
                    query=query,
                    search_depth="advanced",
                    max_results=10,  # More results for data-driven analysis
                    include_domains=[
                        "g2.com", "capterra.com", "trustradius.com",
                        "producthunt.com", "techcrunch.com", "venturebeat.com",
                        "linkedin.com", "medium.com", "forbes.com",
                        "bloomberg.com", "reuters.com", "wsj.com"
                    ]
                )
                sources = search_result.get("results", [])
                print(f"✅ Found {len(sources)} web sources")
            except Exception as e:
                print(f"⚠️ Tavily search failed: {e}")
                sources = []
        
        # Prepare JSON data for testprompt4
        results_data = []
        for source in sources:
            results_data.append({
                "title": source.get('title', 'Unknown'),
                "url": source.get('url', 'N/A'),
                "snippet": source.get('content', '')[:300] + "..." if len(source.get('content', '')) > 300 else source.get('content', ''),
                "date": source.get('published_date', 'Unknown'),
                "annotation": "Web search result"
            })
        
        # Prepare the JSON input for testprompt4
        json_input = {
            "query": query,
            "num_results": len(results_data),
            "results": results_data
        }
        
        # Get testprompt4
        prompt4_content = prompt_manager.get_prompt("testprompt4")
        
        # Create the full prompt with JSON data
        full_prompt = f"{prompt4_content}\n\n**Input JSON Schema:**\n```json\n{json.dumps(json_input, indent=2)}\n```"
        
        # Try DeepSeek first (primary)
        if self.deepseek_enabled:
            try:
                print("🔍 Using DeepSeek (primary) for data-driven analysis...")
                completion = self.deepseek_client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "user", "content": full_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    stream=False
                )
                
                content = completion.choices[0].message.content
                
            except Exception as e:
                print(f"⚠️ DeepSeek failed in data-driven research: {str(e)}")
                if self.groq_client:
                    print("🔄 Falling back to Groq for data-driven research...")
                    content = self._fallback_data_driven_research(full_prompt)
                else:
                    content = f"Research failed: {str(e)}"
        
        # Fallback to Groq (secondary)
        elif self.groq_client:
            content = self._fallback_data_driven_research(full_prompt)
        else:
            content = "No AI backend available for data-driven research"
        
        return {
            "query": query,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "model": "deepseek-reasoner" if self.deepseek_enabled else "groq-compound-beta",
            "total_sources": len(sources),
            "research_type": "data_driven",
            "prompt_used": "testprompt4"
        }
    
    def _fallback_data_driven_research(self, full_prompt: str) -> str:
        """Fallback method for data-driven research using Groq"""
        try:
            print("🔍 Using Groq (secondary) for data-driven analysis...")
            # Add retry logic for rate limiting
            max_retries = 3
            retry_delay = 5
            
            for attempt in range(max_retries):
                try:
                    completion = self.groq_client.chat.completions.create(
                        model="compound-beta",
                        messages=[
                            {"role": "user", "content": full_prompt}
                        ],
                        temperature=0.7,
                        top_p=1,
                        stream=False,
                        stop=None
                    )
                    return completion.choices[0].message.content
                    
                except Exception as e:
                    if "rate_limit" in str(e).lower() and attempt < max_retries - 1:
                        print(f"Rate limit hit, waiting {retry_delay} seconds...")
                        time.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        raise e
                        
        except Exception as e:
            print(f"⚠️ Groq failed in data-driven research: {str(e)}")
            return f"Data-driven research failed: {str(e)}"

# Export for use in Streamlit app
research_agent = PMMResearchAgent() 