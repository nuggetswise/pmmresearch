#!/usr/bin/env python3
"""
Test script for Enhanced PMM Research Agent
Tests both basic and enhanced research modes
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_enhanced_research():
    """Test the enhanced research functionality"""
    try:
        from enhanced_research import enhanced_researcher
        
        print("🧪 Testing Enhanced PMM Research Agent...\n")
        
        # Test query
        test_query = "Compare ClickUp and Asana pricing strategies 2024"
        print(f"🔍 Testing enhanced query: {test_query}")
        
        # Test enhanced research
        result = await enhanced_researcher.conduct_enhanced_research(test_query)
        
        if "error" in result:
            print(f"❌ Enhanced research failed: {result['error']}")
            return False
        else:
            print("✅ Enhanced research completed successfully")
            print(f"   Model: {result.get('model', 'Unknown')}")
            print(f"   Sources used: {result.get('sources_used', 0)}")
            print(f"   Tavily enabled: {result.get('tavily_enabled', False)}")
            
            # Show a snippet of the content
            content = result.get('content', '')
            if content:
                print(f"   Content preview: {content[:200]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ Enhanced research test failed: {e}")
        return False

async def test_basic_research():
    """Test the basic research functionality"""
    try:
        from deep_research import research_agent
        
        print("🧪 Testing Basic PMM Research Agent...\n")
        
        # Test query
        test_query = "What are the key trends in B2B SaaS pricing?"
        print(f"🔍 Testing basic query: {test_query}")
        
        # Test basic research
        result = research_agent.generate_research_report(test_query)
        
        if "error" in result:
            print(f"❌ Basic research failed: {result['error']}")
            return False
        else:
            print("✅ Basic research completed successfully")
            print(f"   Model: {result.get('model', 'Unknown')}")
            print(f"   Cached: {result.get('cached', False)}")
            
            # Show a snippet of the content
            content = result.get('content', '')
            if content:
                print(f"   Content preview: {content[:200]}...")
            
            return True
            
    except Exception as e:
        print(f"❌ Basic research test failed: {e}")
        return False

async def main():
    """Run all tests"""
    print("🚀 Testing PMM Research Agent (Enhanced + Basic)...\n")
    
    # Test API keys
    groq_key = os.getenv("GROQ_API_KEY")
    tavily_key = os.getenv("TAVILY_API_KEY")
    
    print("🔑 API Key Status:")
    if groq_key and groq_key != "your_groq_api_key_here":
        print("   ✅ Groq API key configured")
    else:
        print("   ❌ Groq API key not configured")
    
    if tavily_key and tavily_key != "your_tavily_api_key_here":
        print("   ✅ Tavily API key configured")
    else:
        print("   ⚠️  Tavily API key not configured (enhanced mode will be limited)")
    
    print()
    
    # Run tests
    basic_success = await test_basic_research()
    print()
    enhanced_success = await test_enhanced_research()
    
    print(f"\n📊 Test Results:")
    print(f"   Basic Research: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"   Enhanced Research: {'✅ PASS' if enhanced_success else '❌ FAIL'}")
    
    if basic_success and enhanced_success:
        print("\n🎉 All tests passed! Your Enhanced PMM Research Agent is ready!")
        print("   Run 'streamlit run app.py' to start the web interface.")
    else:
        print("\n⚠️  Some tests failed. Please check your configuration.")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main()) 