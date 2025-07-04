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
        # Try to get API key from Streamlit secrets first, then environment
        api_key = None
        try:
            api_key = st.secrets.get("GROQ_API_KEY")
        except:
            pass
        
        if not api_key:
            api_key = os.getenv("GROQ_API_KEY")
        
        if not api_key:
            raise ValueError("GROQ_API_KEY not found in secrets or environment variables")
        
        self.groq_client = groq.Groq(api_key=api_key)
        self.cache_db = "pmm_research_cache.db"
        self.init_cache()
        
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
    
    def generate_research_report(self, query: str, prompt_name: str = "default") -> Dict:
        """Generate structured research report using Groq"""
        
        # Check cache first
        cached = self.get_cached_response(query)
        if cached:
            return cached
        
        # Get prompt from manager
        system_prompt = prompt_manager.get_prompt(prompt_name)

        # User prompt
        user_prompt = f"Please research and analyze: {query}\nProvide a comprehensive PMM-focused analysis with the exact structure specified above."

        try:
            # Add retry logic for rate limiting
            max_retries = 3
            retry_delay = 5  # Start with 5 seconds
            
            for attempt in range(max_retries):
                try:
                    # Call Groq API with compound-beta model
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
                "cached": False
            }
            
            # Cache the response
            self.cache_response(query, response)
            
            return response
            
        except Exception as e:
            return {
                "error": f"Failed to generate research report: {str(e)}",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }

# Export for use in Streamlit app
research_agent = PMMResearchAgent() 