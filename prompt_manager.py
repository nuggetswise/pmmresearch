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
            
            # Load testprompt4
            prompt4_path = os.path.join(self.prompts_dir, "testprompt4")
            if os.path.exists(prompt4_path):
                with open(prompt4_path, 'r', encoding='utf-8') as f:
                    self.prompts["testprompt4"] = f.read().strip()
            
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
        if stage and self._is_3stage_prompt(prompt_name):
            return self._extract_system_prompt(prompt_name, stage)
        return self.prompts.get(prompt_name, self.prompts["default"])
    
    def get_user_prompt(self, prompt_name: str, stage: str = None) -> str:
        """Get user prompt for a specific stage (for 3-stage pipeline)"""
        if stage and self._is_3stage_prompt(prompt_name):
            return self._extract_user_prompt(prompt_name, stage)
        return self.prompts.get(prompt_name, self.prompts["default"])
    
    def _is_3stage_prompt(self, prompt_name: str) -> bool:
        """Check if a prompt is a 3-stage pipeline prompt"""
        if prompt_name not in self.prompts:
            return False
        
        content = self.prompts[prompt_name]
        # Check if it contains 3-stage structure markers
        return ("STAGE 1:" in content and "STAGE 2:" in content and "STAGE 3:" in content)
    
    def _extract_system_prompt(self, prompt_name: str, stage: str) -> str:
        """Extract system prompt for specific stage from any 3-stage prompt, robust to whitespace."""
        if prompt_name not in self.prompts:
            return "You are an AI assistant."
        content = self.prompts[prompt_name]
        
        stage_headers = {
            "planner": "# ===== STAGE 1: RESEARCH PLANNER =====",
            "execution": "# ===== STAGE 2: EXECUTION AGENT =====",
            "publisher": "# ===== STAGE 3: RESEARCH PUBLISHER ====="
        }
        header = stage_headers.get(stage)
        if not header:
            return "You are an AI assistant."
        start = content.find(header)
        if start == -1:
            return "You are an AI assistant."
        # Find the next '### System Prompt' after the header
        sys_marker = content.find("### System Prompt", start)
        if sys_marker == -1:
            return "You are an AI assistant."
        sys_start = content.find("\n", sys_marker) + 1
        user_marker = content.find("### User Prompt", sys_start)
        if user_marker == -1:
            return "You are an AI assistant."
        return content[sys_start:user_marker].strip()
    
    def _extract_user_prompt(self, prompt_name: str, stage: str) -> str:
        """Extract user prompt for specific stage from any 3-stage prompt, robust to whitespace."""
        if prompt_name not in self.prompts:
            return ""
        content = self.prompts[prompt_name]
        stage_headers = {
            "planner": "# ===== STAGE 1: RESEARCH PLANNER =====",
            "execution": "# ===== STAGE 2: EXECUTION AGENT =====",
            "publisher": "# ===== STAGE 3: RESEARCH PUBLISHER ====="
        }
        header = stage_headers.get(stage)
        if not header:
            return ""
        start = content.find(header)
        if start == -1:
            return ""
        user_marker = content.find("### User Prompt", start)
        if user_marker == -1:
            return ""
        user_start = content.find("\n", user_marker) + 1
        # End at next '---' or end of file
        end = content.find("---", user_start)
        if end == -1:
            return content[user_start:].strip()
        return content[user_start:end].strip()
    
    def get_available_prompts(self) -> Dict[str, str]:
        """Get all available prompts with descriptions"""
        available_prompts = {}
        
        # Only include prompts that actually exist
        if "testprompt1" in self.prompts:
            available_prompts["testprompt1"] = "Basic research (fast, simple analysis)"
        
        if "testprompt2" in self.prompts:
            available_prompts["testprompt2"] = "Clean 5-section approach"
        
        if "testprompt3" in self.prompts:
            available_prompts["testprompt3"] = "Advanced 3-stage research (deep analysis)"
        
        if "testprompt4" in self.prompts:
            available_prompts["testprompt4"] = "Data-driven reports (web sources + insights)"
        
        return available_prompts
    
    def reload_prompts(self):
        """Reload prompts from files (useful for A/B testing)"""
        self.load_prompts()

# Global prompt manager instance
prompt_manager = PromptManager() 