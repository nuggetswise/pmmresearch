#!/usr/bin/env python3
"""
Simple test script for PMM Research Agent
Run this to verify the core functionality works
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_imports():
    """Test that all required modules can be imported"""
    try:
        import streamlit
        import groq
        import sqlite3
        print("✅ All imports successful")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_api_key():
    """Test that Groq API key is configured"""
    # Check environment first
    api_key = os.getenv("GROQ_API_KEY")
    
    # If not in environment, check if we can access Streamlit secrets
    if not api_key or api_key == "your_groq_api_key_here":
        try:
            import streamlit as st
            # This will only work when running in Streamlit context
            api_key = st.secrets.get("GROQ_API_KEY")
        except:
            pass
    
    if api_key and api_key != "your_groq_api_key_here":
        print("✅ Groq API key configured")
        return True
    else:
        print("❌ Groq API key not configured")
        print("   Set GROQ_API_KEY in your .env file, environment, or .streamlit/secrets.toml")
        return False

def test_database():
    """Test SQLite database creation"""
    try:
        from deep_research import research_agent
        print("✅ Research agent initialized successfully")
        return True
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False

def test_simple_query():
    """Test a simple research query"""
    try:
        from deep_research import research_agent
        
        # Test query
        test_query = "What are the key trends in B2B SaaS pricing?"
        print(f"🧠 Testing query: {test_query}")
        
        result = research_agent.generate_research_report(test_query)
        
        if "error" in result:
            print(f"❌ Query failed: {result['error']}")
            return False
        else:
            print("✅ Query executed successfully")
            print(f"   Model used: {result.get('model', 'Unknown')}")
            print(f"   Cached: {result.get('cached', False)}")
            return True
            
    except Exception as e:
        print(f"❌ Query test failed: {e}")
        return False

def main():
    """Run all tests"""
    print("🧪 Testing PMM Research Agent...\n")
    
    tests = [
        ("Import Check", test_imports),
        ("API Key Check", test_api_key),
        ("Database Check", test_database),
        ("Query Test", test_simple_query),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"Testing: {test_name}")
        if test_func():
            passed += 1
        print()
    
    print(f"📊 Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All tests passed! Your PMM Research Agent is ready to use.")
        print("   Run 'streamlit run app.py' to start the web interface.")
    else:
        print("⚠️  Some tests failed. Please check the configuration.")
        sys.exit(1)

if __name__ == "__main__":
    main() 