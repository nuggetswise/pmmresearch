#!/usr/bin/env python3
"""
Test script for prompt manager A/B testing functionality
"""

from prompt_manager import prompt_manager

def test_prompt_loading():
    """Test that prompts are loaded correctly"""
    print("🧪 Testing Prompt Manager...\n")
    
    # Test available prompts
    available_prompts = prompt_manager.get_available_prompts()
    print("📋 Available Prompts:")
    for name, description in available_prompts.items():
        print(f"   {name}: {description}")
    
    print("\n📄 Prompt Contents:")
    for prompt_name in available_prompts.keys():
        prompt_content = prompt_manager.get_prompt(prompt_name)
        print(f"\n--- {prompt_name.upper()} ---")
        print(prompt_content[:200] + "..." if len(prompt_content) > 200 else prompt_content)
    
    # Test reload functionality
    print("\n🔄 Testing prompt reload...")
    prompt_manager.reload_prompts()
    print("✅ Prompts reloaded successfully")
    
    print("\n🎉 Prompt manager is working correctly!")
    print("   You can now edit testprompt1 and testprompt2 files")
    print("   and use the 'Reload Prompts' button in the app for A/B testing")

if __name__ == "__main__":
    test_prompt_loading() 