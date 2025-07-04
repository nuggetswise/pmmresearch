#!/usr/bin/env python3
"""
Debug script to check prompt extraction
"""

from prompt_manager import prompt_manager

def debug_prompt_extraction():
    """Debug the prompt extraction for testprompt3"""
    print("🔍 Debugging prompt extraction for testprompt3...")
    
    # Test system prompts
    planner_system = prompt_manager.get_system_prompt("testprompt3", "planner")
    execution_system = prompt_manager.get_system_prompt("testprompt3", "execution")
    publisher_system = prompt_manager.get_system_prompt("testprompt3", "publisher")
    
    print("\n📋 SYSTEM PROMPTS:")
    print("=" * 50)
    print("PLANNER SYSTEM:")
    print(planner_system)
    print("\n" + "=" * 50)
    print("EXECUTION SYSTEM:")
    print(execution_system)
    print("\n" + "=" * 50)
    print("PUBLISHER SYSTEM:")
    print(publisher_system)
    
    # Test user prompts
    planner_user = prompt_manager.get_user_prompt("testprompt3", "planner")
    execution_user = prompt_manager.get_user_prompt("testprompt3", "execution")
    publisher_user = prompt_manager.get_user_prompt("testprompt3", "publisher")
    
    print("\n📋 USER PROMPTS:")
    print("=" * 50)
    print("PLANNER USER:")
    print(planner_user)
    print("\n" + "=" * 50)
    print("EXECUTION USER:")
    print(execution_user)
    print("\n" + "=" * 50)
    print("PUBLISHER USER:")
    print(publisher_user)
    
    # Check if prompts are empty or default
    if not planner_system or planner_system == "You are an AI assistant.":
        print("\n❌ ERROR: Planner system prompt is empty or default!")
    else:
        print("\n✅ Planner system prompt looks good")
    
    if not planner_user:
        print("\n❌ ERROR: Planner user prompt is empty!")
    else:
        print("\n✅ Planner user prompt looks good")

if __name__ == "__main__":
    debug_prompt_extraction() 