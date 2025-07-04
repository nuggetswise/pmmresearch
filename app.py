import streamlit as st
import os
import json
import asyncio
from datetime import datetime
from deep_research import research_agent
from advanced_research import advanced_researcher
from prompt_manager import prompt_manager
import markdown

# Page configuration
st.set_page_config(
    page_title="PMM Research Agent",
    page_icon="🧠",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .subtitle {
        font-size: 1.2rem;
        color: #666;
        text-align: center;
        margin-bottom: 2rem;
    }
    .query-box {
        background-color: #f0f2f6;
        padding: 1.5rem;
        border-radius: 10px;
        margin-bottom: 2rem;
    }
    .result-box {
        background-color: white;
        border: 1px solid #e0e0e0;
        border-radius: 10px;
        padding: 1.5rem;
        margin-bottom: 1rem;
    }
    .cache-indicator {
        background-color: #e8f5e8;
        color: #2e7d32;
        padding: 0.5rem;
        border-radius: 5px;
        font-size: 0.9rem;
    }
    .error-box {
        background-color: #ffebee;
        color: #c62828;
        padding: 1rem;
        border-radius: 5px;
        border-left: 4px solid #c62828;
    }
</style>
""", unsafe_allow_html=True)

def main():
    # Header
    st.markdown('<h1 class="main-header">🧠 PMM Research Agent</h1>', unsafe_allow_html=True)
    st.markdown('<p class="subtitle">Strategic research assistant for Product Marketing Managers</p>', unsafe_allow_html=True)
    
    # Sidebar for configuration
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # API Key status
        groq_key = os.getenv("GROQ_API_KEY")
        if groq_key and groq_key != "your_groq_api_key_here":
            st.success("✅ Groq API Key configured")
        else:
            st.error("❌ Groq API Key not configured")
            st.info("Set GROQ_API_KEY in your environment or .env file")
        
        # Tavily API Key status
        tavily_key = os.getenv("TAVILY_API_KEY")
        if tavily_key and tavily_key != "your_tavily_api_key_here":
            st.success("✅ Tavily API Key configured")
        else:
            st.warning("⚠️ Tavily API Key not configured")
            st.info("Set TAVILY_API_KEY for enhanced web research")
        
        # Research mode removed - now automatically determined by prompt selection
        
        # Prompt selection for A/B testing
        available_prompts = prompt_manager.get_available_prompts()
        selected_prompt = st.selectbox(
            "Prompt Version (A/B Testing)",
            list(available_prompts.keys()),
            index=0,
            format_func=lambda x: f"{x}: {available_prompts[x]}",
            help="Choose different prompt versions for A/B testing"
        )
        
        # Reload prompts button
        if st.button("🔄 Reload Prompts"):
            prompt_manager.reload_prompts()
            st.success("Prompts reloaded! Refresh the page to see updates.")
        
        # Cache settings
        st.subheader("💾 Cache Settings")
        cache_enabled = st.checkbox("Enable caching", value=True)
        cache_duration = st.slider("Cache duration (hours)", 1, 72, 24)
        
        # Example queries
        st.subheader("💡 Example Queries")
        example_queries = [
            "Compare ClickUp and Asana's onboarding for technical users",
            "What are the key trends in B2B SaaS pricing strategies?",
            "How do Slack and Microsoft Teams approach enterprise sales?",
            "What's the competitive landscape for project management tools?",
            "Analyze the go-to-market strategies of Notion vs Airtable"
        ]
        
        for query in example_queries:
            if st.button(query, key=f"example_{hash(query)}"):
                st.session_state.user_query = query
                st.rerun()
    
    # Main content area
    col1, col2 = st.columns([3, 1])
    
    with col1:
        st.markdown('<div class="query-box">', unsafe_allow_html=True)
        st.subheader("🔍 Ask Your Research Question")
        
        # Query input
        user_query = st.text_area(
            "Enter your strategic research question:",
            value=st.session_state.get("user_query", ""),
            height=100,
            placeholder="e.g., Compare ClickUp and Asana's onboarding for technical users"
        )
        
        # Research button
        col1_1, col1_2, col1_3 = st.columns([1, 1, 1])
        with col1_2:
            research_button = st.button("🚀 Generate Research Report", type="primary", use_container_width=True)
        
        st.markdown('</div>', unsafe_allow_html=True)
        
        # Process research request
        if research_button and user_query.strip():
            with st.spinner("🧠 Analyzing your question..."):
                try:
                    # Choose research method based on selected prompt
                    if selected_prompt == "testprompt3":
                        # Use advanced 3-stage research pipeline
                        result = asyncio.run(advanced_researcher.conduct_advanced_research(user_query, selected_prompt))
                    elif selected_prompt == "testprompt4":
                        # Use data-driven research (executive reports)
                        result = asyncio.run(advanced_researcher.conduct_advanced_research(user_query, selected_prompt))
                    else:
                        # Use basic research (Groq/DeepSeek only)
                        result = research_agent.generate_research_report(user_query, selected_prompt)
                    
                    if "error" in result:
                        st.markdown('<div class="error-box">', unsafe_allow_html=True)
                        st.error(f"Research failed: {result['error']}")
                        st.markdown('</div>', unsafe_allow_html=True)
                    else:
                        # Display results
                        st.markdown('<div class="result-box">', unsafe_allow_html=True)
                        
                        # Research method indicator based on prompt
                        if selected_prompt == "testprompt3":
                            st.markdown('<div class="cache-indicator">🚀 Advanced 3-stage research</div>', unsafe_allow_html=True)
                        elif selected_prompt == "testprompt4":
                            st.markdown('<div class="cache-indicator">📊 Data-driven executive report</div>', unsafe_allow_html=True)
                        else:
                            st.markdown('<div class="cache-indicator">📋 Basic research mode</div>', unsafe_allow_html=True)
                        
                        # Display the markdown content
                        st.markdown(result["content"])
                        
                        # Enhanced metadata
                        st.markdown("---")
                        col_meta1, col_meta2, col_meta3, col_meta4 = st.columns(4)
                        with col_meta1:
                            st.caption(f"📅 Generated: {datetime.fromisoformat(result['timestamp']).strftime('%Y-%m-%d %H:%M')}")
                        with col_meta2:
                            st.caption(f"🤖 Model: {result.get('model', 'Unknown')}")
                        with col_meta3:
                            st.caption(f"📊 Query: {result['query'][:50]}...")
                        with col_meta4:
                            if result.get("sources_used"):
                                st.caption(f"🔗 Sources: {result.get('sources_used', 0)}")
                            elif result.get("total_sources"):
                                st.caption(f"🔗 Sources: {result.get('total_sources', 0)}")
                            elif result.get("sub_questions_researched"):
                                st.caption(f"🔬 Questions: {result.get('sub_questions_researched', 0)}")
                        
                        st.markdown('</div>', unsafe_allow_html=True)
                        
                        # Store result in session state for export
                        st.session_state.last_result = result
                        
                except Exception as e:
                    st.error(f"An error occurred: {str(e)}")
    
    with col2:
        st.subheader("📤 Export Options")
        
        if st.session_state.get("last_result"):
            # Export as markdown
            if st.button("📄 Export as Markdown"):
                result = st.session_state.last_result
                markdown_content = f"""# PMM Research Report

**Query:** {result['query']}
**Generated:** {result['timestamp']}
**Model:** {result.get('model', 'Unknown')}

{result['content']}
"""
                st.download_button(
                    label="💾 Download Markdown",
                    data=markdown_content,
                    file_name=f"pmm_research_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md",
                    mime="text/markdown"
                )
            
            # Copy to clipboard
            if st.button("📋 Copy to Clipboard"):
                result = st.session_state.last_result
                st.code(result['content'], language="markdown")
                st.success("Content copied to clipboard!")
        
        # Cache management
        st.subheader("🗄️ Cache Management")
        if st.button("🗑️ Clear Cache"):
            try:
                import sqlite3
                conn = sqlite3.connect("pmm_research_cache.db")
                cursor = conn.cursor()
                cursor.execute("DELETE FROM research_cache")
                conn.commit()
                conn.close()
                st.success("Cache cleared successfully!")
            except Exception as e:
                st.error(f"Failed to clear cache: {str(e)}")

if __name__ == "__main__":
    main() 