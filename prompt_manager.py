import os
from typing import Dict, Optional

class PromptManager:
    def __init__(self, prompts_dir: str = "."):
        self.prompts_dir = prompts_dir
        self.prompts = {}
        self.load_prompts()
    
    def load_prompts(self):
        """Load all prompt files from the prompts directory"""
        try:
            # Load testprompt1
            prompt1_path = os.path.join(self.prompts_dir, "testprompt1")
            if os.path.exists(prompt1_path):
                with open(prompt1_path, 'r', encoding='utf-8') as f:
                    self.prompts["testprompt1"] = f.read().strip()
            
            # Load testprompt2
            prompt2_path = os.path.join(self.prompts_dir, "testprompt2")
            if os.path.exists(prompt2_path):
                with open(prompt2_path, 'r', encoding='utf-8') as f:
                    content = f.read().strip()
                    if content:  # Only add if not empty
                        self.prompts["testprompt2"] = content
            
            # Load testprompt3
            prompt3_path = os.path.join(self.prompts_dir, "testprompt3")
            if os.path.exists(prompt3_path):
                with open(prompt3_path, 'r', encoding='utf-8') as f:
                    self.prompts["testprompt3"] = f.read().strip()
            
            # Set testprompt2 as default if available
            if "testprompt2" in self.prompts:
                self.prompts["default"] = self.prompts["testprompt2"]
            else:
                # Fallback to a minimal default
                self.prompts["default"] = "You are a Principal PMM Strategist. Provide structured analysis with trends, competitors, insights, recommendations, and citations."
            
        except Exception as e:
            print(f"Error loading prompts: {e}")
            # Fallback to minimal default
            self.prompts["default"] = "You are a Principal PMM Strategist. Provide structured analysis with trends, competitors, insights, recommendations, and citations."
    
    def get_prompt(self, prompt_name: str = "default") -> str:
        """Get a specific prompt by name"""
        return self.prompts.get(prompt_name, self.prompts["default"])
    
    def get_system_prompt(self, prompt_name: str, stage: str = None) -> str:
        """Get system prompt for a specific stage (for 3-stage pipeline)"""
        if prompt_name == "testprompt3" and stage:
            return self._extract_system_prompt(stage)
        return self.prompts.get(prompt_name, self.prompts["default"])
    
    def get_user_prompt(self, prompt_name: str, stage: str = None) -> str:
        """Get user prompt for a specific stage (for 3-stage pipeline)"""
        if prompt_name == "testprompt3" and stage:
            return self._extract_user_prompt(stage)
        return self.prompts.get(prompt_name, self.prompts["default"])
    
    def _extract_system_prompt(self, stage: str) -> str:
        """Extract system prompt for specific stage from testprompt3"""
        if "testprompt3" not in self.prompts:
            return "You are an AI assistant."
        
        content = self.prompts["testprompt3"]
        
        if stage == "planner":
            # Extract Stage 1 system prompt
            start = content.find("# ===== STAGE 1: RESEARCH PLANNER =====\n# SYSTEM PROMPT")
            if start != -1:
                start = content.find("\n", start) + 1
                end = content.find("# USER PROMPT", start)
                if end != -1:
                    return content[start:end].strip()
        
        elif stage == "execution":
            # Extract Stage 2 system prompt
            start = content.find("# ===== STAGE 2: EXECUTION AGENT =====\n# SYSTEM PROMPT")
            if start != -1:
                start = content.find("\n", start) + 1
                end = content.find("# USER PROMPT", start)
                if end != -1:
                    return content[start:end].strip()
        
        elif stage == "publisher":
            # Extract Stage 3 system prompt
            start = content.find("# ===== STAGE 3: RESEARCH PUBLISHER =====\n# SYSTEM PROMPT")
            if start != -1:
                start = content.find("\n", start) + 1
                end = content.find("# USER PROMPT", start)
                if end != -1:
                    return content[start:end].strip()
        
        return "You are an AI assistant."
    
    def _extract_user_prompt(self, stage: str) -> str:
        """Extract user prompt for specific stage from testprompt3"""
        if "testprompt3" not in self.prompts:
            return ""
        
        content = self.prompts["testprompt3"]
        
        if stage == "planner":
            # Extract Stage 1 user prompt
            start = content.find("# USER PROMPT\nGiven the query:")
            if start != -1:
                start = content.find("\n", start) + 1
                end = content.find("# ===== STAGE 2:", start)
                if end != -1:
                    return content[start:end].strip()
        
        elif stage == "execution":
            # Extract Stage 2 user prompt
            start = content.find("# USER PROMPT\nResearch the question:")
            if start != -1:
                start = content.find("\n", start) + 1
                end = content.find("# ===== STAGE 3:", start)
                if end != -1:
                    return content[start:end].strip()
        
        elif stage == "publisher":
            # Extract Stage 3 user prompt
            start = content.find("# USER PROMPT\nHere are the sub-questions")
            if start != -1:
                start = content.find("\n", start) + 1
                return content[start:].strip()
        
        return ""
    
    def get_available_prompts(self) -> Dict[str, str]:
        """Get all available prompts with descriptions"""
        return {
            "testprompt1": "Comprehensive PMM research prompt",
            "testprompt2": "Clean 5-section approach", 
            "testprompt3": "3-stage research pipeline prompts"
        }
    
    def reload_prompts(self):
        """Reload prompts from files (useful for A/B testing)"""
        self.load_prompts()

# Global prompt manager instance
prompt_manager = PromptManager() 