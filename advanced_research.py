import os
import asyncio
import json
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
import groq
import streamlit as st
from dotenv import load_dotenv
from prompt_manager import prompt_manager

# Optional Tavily import
try:
    from tavily import TavilyClient
    TAVILY_AVAILABLE = True
except ImportError:
    TAVILY_AVAILABLE = False
    TavilyClient = None

# Load environment variables
load_dotenv()

class AdvancedPMMResearcher:
    def __init__(self):
        # Initialize Groq client
        groq_api_key = self._get_api_key("GROQ_API_KEY")
        self.groq_client = groq.Groq(api_key=groq_api_key)
        
        # Initialize Tavily client
        tavily_api_key = self._get_api_key("TAVILY_API_KEY")
        if tavily_api_key and TAVILY_AVAILABLE:
            self.tavily_client = TavilyClient(api_key=tavily_api_key)
            self.tavily_enabled = True
        else:
            self.tavily_client = None
            self.tavily_enabled = False
    
    def _get_api_key(self, key_name: str) -> Optional[str]:
        """Get API key from Streamlit secrets or environment"""
        try:
            return st.secrets.get(key_name)
        except:
            pass
        return os.getenv(key_name)
    
    async def research_planner(self, query: str) -> List[str]:
        """Stage 1: Generate detailed research questions"""
        # Get system and user prompts from testprompt3
        system_prompt = prompt_manager.get_system_prompt("testprompt3", "planner")
        user_prompt = prompt_manager.get_user_prompt("testprompt3", "planner")
        user_prompt = user_prompt.replace("<user query>", query)

        try:
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
            
            questions = completion.choices[0].message.content.strip().split('\n')
            # Clean up questions (remove numbering, empty lines, etc.)
            questions = [q.strip() for q in questions if q.strip() and not q.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.'))]
            
            return questions[:10]  # Limit to 10 questions
            
        except Exception as e:
            return [f"Research the competitive landscape for {query}", 
                   f"Analyze market trends in {query}",
                   f"Identify key players in {query}",
                   f"Examine pricing strategies for {query}",
                   f"Investigate customer segments for {query}"]
    
    async def execution_agent(self, sub_question: str) -> Dict:
        """Stage 2: Research individual sub-question with sources"""
        
        # Get web sources if Tavily is available
        sources = []
        if self.tavily_enabled:
            try:
                search_result = self.tavily_client.search(
                    query=sub_question,
                    search_depth="advanced",
                    max_results=5,
                    include_domains=[
                        "g2.com", "capterra.com", "trustradius.com",
                        "producthunt.com", "techcrunch.com", "venturebeat.com",
                        "linkedin.com", "medium.com", "forbes.com"
                    ]
                )
                sources = search_result.get("results", [])
            except Exception as e:
                print(f"Tavily search failed: {e}")
        
        # Create source summaries
        source_summaries = []
        for source in sources[:5]:
            summary = f"Source: {source.get('title', 'Unknown')}\n"
            summary += f"URL: {source.get('url', 'N/A')}\n"
            summary += f"Content: {source.get('content', '')[:200]}...\n"
            source_summaries.append(summary)
        
        # Get system and user prompts from testprompt3
        system_prompt = prompt_manager.get_system_prompt("testprompt3", "execution")
        user_prompt = prompt_manager.get_user_prompt("testprompt3", "execution")
        user_prompt = user_prompt.replace("<sub-question>", sub_question)
        user_prompt = user_prompt.replace("<source_summaries>", 
            f"Sources found:\n{chr(10).join(source_summaries)}" if source_summaries else "No web sources available. Use your knowledge to provide insights.")

        try:
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
            
            return {
                "question": sub_question,
                "summary": completion.choices[0].message.content,
                "sources": sources,
                "source_count": len(sources)
            }
            
        except Exception as e:
            return {
                "question": sub_question,
                "summary": f"Research failed: {str(e)}",
                "sources": [],
                "source_count": 0
            }
    
    async def research_publisher(self, query: str, research_results: List[Dict]) -> Dict:
        """Stage 3: Synthesize research into cohesive report"""
        
        # Prepare research data for synthesis
        research_text = f"Original Query: {query}\n\n"
        research_text += "Research Results:\n\n"
        
        for i, result in enumerate(research_results, 1):
            research_text += f"Question {i}: {result['question']}\n"
            research_text += f"Summary: {result['summary']}\n"
            if result.get('sources'):
                research_text += f"Sources: {result['source_count']} found\n"
            research_text += "\n"
        
        # Get system and user prompts from testprompt3
        system_prompt = prompt_manager.get_system_prompt("testprompt3", "publisher")
        user_prompt = prompt_manager.get_user_prompt("testprompt3", "publisher")
        user_prompt = user_prompt.replace("<research_data>", research_text)

        try:
            # Add retry logic for rate limiting
            max_retries = 3
            retry_delay = 5  # Start with 5 seconds
            
            for attempt in range(max_retries):
                try:
                    completion = self.groq_client.chat.completions.create(
                        model="compound-beta",
                        messages=[
                            {"role": "system", "content": "You are a Research Publisher creating comprehensive PMM reports."},
                            {"role": "user", "content": publisher_prompt}
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
            
            return {
                "query": query,
                "content": completion.choices[0].message.content,
                "timestamp": datetime.now().isoformat(),
                "model": "groq-compound-beta-advanced",
                "sub_questions_researched": len(research_results),
                "total_sources": sum(r.get('source_count', 0) for r in research_results),
                "tavily_enabled": self.tavily_enabled
            }
            
        except Exception as e:
            return {
                "error": f"Research synthesis failed: {str(e)}",
                "query": query,
                "timestamp": datetime.now().isoformat()
            }
    
    async def conduct_advanced_research(self, query: str) -> Dict:
        """Main method: Execute the three-stage research pipeline"""
        
        print(f"🔍 Stage 1: Planning research for '{query}'")
        sub_questions = await self.research_planner(query)
        print(f"   Generated {len(sub_questions)} research questions")
        
        print(f"🔬 Stage 2: Executing research on {len(sub_questions)} questions")
        research_tasks = [self.execution_agent(q) for q in sub_questions]
        research_results = await asyncio.gather(*research_tasks, return_exceptions=True)
        
        # Handle any exceptions
        valid_results = []
        for result in research_results:
            if isinstance(result, Exception):
                print(f"   Research failed: {result}")
            else:
                valid_results.append(result)
        
        print(f"   Completed {len(valid_results)} research tasks")
        
        print(f"📝 Stage 3: Publishing comprehensive report")
        final_report = await self.research_publisher(query, valid_results)
        
        return final_report

# Export for use in Streamlit app
advanced_researcher = AdvancedPMMResearcher() 