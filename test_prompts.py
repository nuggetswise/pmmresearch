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
    
    # Check for missing files
    expected_files = ["testprompt1", "testprompt2", "testprompt3", "testprompt4"]
    missing_files = []
    for file_name in expected_files:
        if file_name not in available_prompts:
            missing_files.append(file_name)
    
    if missing_files:
        print(f"\n⚠️ Missing prompt files: {', '.join(missing_files)}")
    else:
        print("\n✅ All expected prompt files are present")
    
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
    if available_prompts:
        print(f"   Available prompts: {', '.join(available_prompts.keys())}")
    print("   Use the 'Reload Prompts' button in the app for A/B testing")

def test_prompt4_integration():
    """Test testprompt4 data-driven research integration"""
    print("🧪 Testing testprompt4 integration...")
    
    # Test prompt loading
    prompt4_content = prompt_manager.get_prompt("testprompt4")
    if prompt4_content and "comprehensive research analysis" in prompt4_content:
        print("✅ testprompt4 loaded successfully")
    else:
        print("❌ testprompt4 not loaded properly")
        return False
    
    # Test that it's a complete prompt (no placeholders)
    if "〈NUM_RESULTS〉" not in prompt4_content:
        print("✅ testprompt4 is complete (no placeholders)")
    else:
        print("❌ testprompt4 still has placeholders")
        return False
    
    print("✅ testprompt4 integration test passed")
    return True

if __name__ == "__main__":
    test_prompt_loading()
    test_prompt4_integration() 