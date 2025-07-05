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

class AdvancedPMMResearcher:
    def __init__(self):
        # Initialize DeepSeek as primary
        self.deepseek_client = None
        self.deepseek_enabled = False
        
        if DEEPSEEK_AVAILABLE:
            deepseek_api_key = self._get_api_key("DEEPSEEK_API_KEY")
            if deepseek_api_key:
                self.deepseek_client = OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com")
                self.deepseek_enabled = True
                print("✅ DeepSeek initialized as primary backend for advanced research")
        
        # Initialize Groq as secondary
        groq_api_key = self._get_api_key("GROQ_API_KEY")
        if groq_api_key:
            self.groq_client = groq.Groq(api_key=groq_api_key)
            print("✅ Groq initialized as secondary backend for advanced research")
        else:
            self.groq_client = None
            print("⚠️ Groq API key not found for advanced research")
        
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
    
    async def research_planner(self, query: str, prompt_name: str = "testprompt3") -> List[str]:
        """Stage 1: Generate detailed research questions"""
        # Get system and user prompts from specified prompt
        system_prompt = prompt_manager.get_system_prompt(prompt_name, "planner")
        user_prompt = prompt_manager.get_user_prompt(prompt_name, "planner")
        user_prompt = user_prompt.replace("<user query>", query)

        # Try DeepSeek first (primary)
        if self.deepseek_enabled:
            try:
                print("🔍 Using DeepSeek (primary) for research planning...")
                completion = self.deepseek_client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    # Let LLM decide appropriate length
                    stream=False
                )
                
                questions = completion.choices[0].message.content.strip().split('\n')
                # Clean up questions (remove numbering, empty lines, etc.)
                questions = [q.strip() for q in questions if q.strip() and not q.strip().startswith(('1.', '2.', '3.', '4.', '5.', '6.', '7.', '8.', '9.', '10.'))]
                
                return questions[:10]  # Limit to 10 questions
                
            except Exception as e:
                print(f"⚠️ DeepSeek failed in planner: {str(e)}")
                if self.groq_client:
                    print("🔄 Falling back to Groq for planning...")
                else:
                    return [f"Research the competitive landscape for {query}", 
                           f"Analyze market trends in {query}",
                           f"Identify key players in {query}",
                           f"Examine pricing strategies for {query}",
                           f"Investigate customer segments for {query}"]

        # Fallback to Groq (secondary)
        if self.groq_client:
            try:
                print("🔍 Using Groq (secondary) for research planning...")
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
                print(f"⚠️ Groq failed in planner: {str(e)}")
                return [f"Research the competitive landscape for {query}", 
                       f"Analyze market trends in {query}",
                       f"Identify key players in {query}",
                       f"Examine pricing strategies for {query}",
                       f"Investigate customer segments for {query}"]
        
        return [f"Research the competitive landscape for {query}", 
               f"Analyze market trends in {query}",
               f"Identify key players in {query}",
               f"Examine pricing strategies for {query}",
               f"Investigate customer segments for {query}"]
    
    async def execution_agent(self, sub_question: str, prompt_name: str = "testprompt3") -> Dict:
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
        
        # Get system and user prompts from specified prompt
        system_prompt = prompt_manager.get_system_prompt(prompt_name, "execution")
        user_prompt = prompt_manager.get_user_prompt(prompt_name, "execution")
        user_prompt = user_prompt.replace("<sub-question>", sub_question)
        user_prompt = user_prompt.replace("<source_summaries>", 
            f"Sources found:\n{chr(10).join(source_summaries)}" if source_summaries else "No web sources available. Use your knowledge to provide insights.")

        # Try DeepSeek first (primary)
        if self.deepseek_enabled:
            try:
                print(f"🔍 Using DeepSeek (primary) for execution: {sub_question[:50]}...")
                completion = self.deepseek_client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    # Let LLM decide appropriate length
                    stream=False
                )
                
                return {
                    "question": sub_question,
                    "summary": completion.choices[0].message.content,
                    "sources": sources,
                    "source_count": len(sources)
                }
                
            except Exception as e:
                print(f"⚠️ DeepSeek failed in execution: {str(e)}")
                if self.groq_client:
                    print("🔄 Falling back to Groq for execution...")
                else:
                    return {
                        "question": sub_question,
                        "summary": f"Research failed: {str(e)}",
                        "sources": [],
                        "source_count": 0
                    }

        # Fallback to Groq (secondary)
        if self.groq_client:
            try:
                print(f"🔍 Using Groq (secondary) for execution: {sub_question[:50]}...")
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
                print(f"⚠️ Groq failed in execution: {str(e)}")
                return {
                    "question": sub_question,
                    "summary": f"Research failed: {str(e)}",
                    "sources": [],
                    "source_count": 0
                }
        
        return {
            "question": sub_question,
            "summary": f"Research failed: No available backends",
            "sources": [],
            "source_count": 0
        }
    
    async def research_publisher(self, query: str, research_results: List[Dict], prompt_name: str = "testprompt3") -> Dict:
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
        
        # Get system and user prompts from specified prompt
        system_prompt = prompt_manager.get_system_prompt(prompt_name, "publisher")
        user_prompt = prompt_manager.get_user_prompt(prompt_name, "publisher")
        user_prompt = user_prompt.replace("<research_data>", research_text)

        # Try DeepSeek first (primary)
        if self.deepseek_enabled:
            try:
                print("🔍 Using DeepSeek (primary) for research synthesis...")
                completion = self.deepseek_client.chat.completions.create(
                    model="deepseek-reasoner",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.7,
                    max_tokens=4000,
                    stream=False
                )
                
                return {
                    "query": query,
                    "content": completion.choices[0].message.content,
                    "timestamp": datetime.now().isoformat(),
                    "model": "deepseek-reasoner-advanced",
                    "sub_questions_researched": len(research_results),
                    "total_sources": sum(r.get('source_count', 0) for r in research_results),
                    "tavily_enabled": self.tavily_enabled
                }
                
            except Exception as e:
                print(f"⚠️ DeepSeek failed in synthesis: {str(e)}")
                if self.groq_client:
                    print("🔄 Falling back to Groq for synthesis...")
                else:
                    return {
                        "error": f"Research synthesis failed: {str(e)}",
                        "query": query,
                        "timestamp": datetime.now().isoformat()
                    }

        # Fallback to Groq (secondary)
        if self.groq_client:
            try:
                print("🔍 Using Groq (secondary) for research synthesis...")
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
                    "query": query,
                    "content": completion.choices[0].message.content,
                    "timestamp": datetime.now().isoformat(),
                    "model": "groq-compound-beta-advanced",
                    "sub_questions_researched": len(research_results),
                    "total_sources": sum(r.get('source_count', 0) for r in research_results),
                    "tavily_enabled": self.tavily_enabled
                }
                
            except Exception as e:
                print(f"⚠️ Groq failed in synthesis: {str(e)}")
                return {
                    "error": f"Research synthesis failed: {str(e)}",
                    "query": query,
                    "timestamp": datetime.now().isoformat()
                }
        
        return {
            "error": "Research synthesis failed: No available backends",
            "query": query,
            "timestamp": datetime.now().isoformat()
        }
    
    async def conduct_advanced_research(self, query: str, prompt_name: str = "testprompt3") -> Dict:
        """Conduct advanced research using the 3-stage pipeline"""
        
        # Special handling for testprompt4 (data-driven approach)
        if prompt_name == "testprompt4":
            return await self._conduct_data_driven_research(query)
        
        print(f"🚀 Starting advanced research with {prompt_name}")
        start_time = time.time()
        
        # Stage 1: Research Planning
        print("📋 Stage 1: Research Planning...")
        sub_questions = await self.research_planner(query, prompt_name)
        print(f"✅ Generated {len(sub_questions)} research questions")
        
        # Stage 2: Execution
        print("🔍 Stage 2: Research Execution...")
        research_results = []
        for i, question in enumerate(sub_questions, 1):
            print(f"  📝 Researching question {i}/{len(sub_questions)}: {question[:50]}...")
            result = await self.execution_agent(question, prompt_name)
            research_results.append(result)
        
        # Stage 3: Publishing
        print("📊 Stage 3: Research Publishing...")
        final_report = await self.research_publisher(query, research_results, prompt_name)
        
        end_time = time.time()
        print(f"✅ Advanced research completed in {end_time - start_time:.2f} seconds")
        
        return final_report
    
    async def _conduct_data_driven_research(self, query: str) -> Dict:
        """Conduct data-driven research using testprompt4 approach"""
        print(f"📊 Starting data-driven research for: {query}")
        start_time = time.time()
        
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
                    content = await self._fallback_data_driven_research(full_prompt)
                else:
                    content = f"Research failed: {str(e)}"
        
        # Fallback to Groq (secondary)
        elif self.groq_client:
            content = await self._fallback_data_driven_research(full_prompt)
        else:
            content = "No AI backend available for data-driven research"
        
        end_time = time.time()
        print(f"✅ Data-driven research completed in {end_time - start_time:.2f} seconds")
        
        return {
            "query": query,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            "model": "deepseek-reasoner" if self.deepseek_enabled else "groq-compound-beta",
            "total_sources": len(sources),
            "research_type": "data_driven",
            "prompt_used": "testprompt4"
        }
    
    async def _fallback_data_driven_research(self, full_prompt: str) -> str:
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
                        await asyncio.sleep(retry_delay)
                        retry_delay *= 2
                        continue
                    else:
                        raise e
                        
        except Exception as e:
            print(f"⚠️ Groq failed in data-driven research: {str(e)}")
            return f"Data-driven research failed: {str(e)}"

# Export for use in Streamlit app
advanced_researcher = AdvancedPMMResearcher() 