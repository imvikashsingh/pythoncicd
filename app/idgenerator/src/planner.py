"""Planning module - converts user goals into structured TODO plans"""

import json
from agent.llm import LLMClient

class Planner:
    """Creates structured plans from user goals"""
    
    def __init__(self):
        self.llm = LLMClient()
    
    def create_plan(self, user_goal: str) -> list:
        """
        Convert user goal into a structured TODO plan
        
        Returns:
            List of tasks, each with: description, type, query
        """
        prompt = self._build_planning_prompt(user_goal)
        
        try:
            response = self.llm.chat(
                messages=[
                    {"role": "system", "content": "You are a planning assistant. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=1000
            )
            
            # Extract JSON from response
            plan_text = self._extract_json(response)
            plan = json.loads(plan_text)
            
            # Validate plan structure
            if not isinstance(plan, list):
                raise ValueError("Plan must be a list")
            
            # Ensure each task has required fields
            for task in plan:
                if "description" not in task:
                    task["description"] = "Unknown task"
                if "type" not in task:
                    task["type"] = "search"
                if "query" not in task and task["type"] in ["search", "read"]:
                    task["query"] = task["description"]
            
            return plan
            
        except json.JSONDecodeError as e:
            print(f"Failed to parse plan as JSON: {e}")
            print(f"Raw response: {plan_text}")
            return self._fallback_plan(user_goal)
        except Exception as e:
            print(f"Planning failed: {e}")
            return self._fallback_plan(user_goal)
    
    def _build_planning_prompt(self, user_goal: str) -> str:
        """Build the planning prompt with clear instructions"""
        return f"""Break down this user goal into a sequence of 2-5 concrete tasks.

User goal: "{user_goal}"

Available task types:
- "search": For finding information online (needs a search query)
- "read": For reading content from a specific URL (needs URL)
- "summarize": For synthesizing information from previous tasks
- "ask_user": For requesting clarification or confirmation

Output format: JSON array of tasks, each with:
{{
    "description": "Clear description of what to do",
    "type": "search|read|summarize|ask_user",
    "query": "search query or URL or what to summarize"
}}

Example for "research Python vs JavaScript":
[
    {{
        "description": "Find main differences between Python and JavaScript",
        "type": "search",
        "query": "Python vs JavaScript differences comparison"
    }},
    {{
        "description": "Research learning curve for each language",
        "type": "search", 
        "query": "Python vs JavaScript learning curve for beginners"
    }},
    {{
        "description": "Summarize findings with recommendation",
        "type": "summarize",
        "query": "Compare Python and JavaScript based on search results"
    }}
]

Generate a plan for the user's goal. Output ONLY the JSON array, no other text."""
    
    def _extract_json(self, text: str) -> str:
        """Extract JSON from text that might have markdown wrapping"""
        # Remove markdown code blocks
        if "```json" in text:
            text = text.split("```json")[1].split("```")[0]
        elif "```" in text:
            text = text.split("```")[1].split("```")[0]
        return text.strip()
    
    def _fallback_plan(self, user_goal: str) -> list:
        """Fallback plan when LLM fails"""
        return [
            {
                "description": f"Search for information about: {user_goal[:50]}",
                "type": "search",
                "query": user_goal
            },
            {
                "description": "Summarize findings",
                "type": "summarize",
                "query": "Provide a summary of the research"
            }
        ]
