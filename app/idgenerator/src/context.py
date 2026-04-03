"""Context management strategy to avoid token overflow"""

class ContextManager:
    """Manages conversation context with token limits"""
    
    def __init__(self, max_tokens=4000):
        self.max_tokens = max_tokens
        self.user_goal = None
        self.plan = None
        self.completed_tasks = []
        self.current_task = None
        
    def set_goal(self, goal):
        """Store the original user goal (always kept)"""
        self.user_goal = goal
        
    def set_plan(self, plan):
        """Store the execution plan"""
        self.plan = plan
        
    def add_task_result(self, task_description, result, task_type):
        """Add completed task result, with truncation strategy"""
        self.completed_tasks.append({
            "task": task_description,
            "result": self._truncate_result(result, task_type),
            "type": task_type
        })
        
        # Keep only last 3 completed tasks for context
        if len(self.completed_tasks) > 3:
            self.completed_tasks = self.completed_tasks[-3:]
    
    def _truncate_result(self, result, task_type):
        """Different truncation strategies per task type"""
        if task_type == "search":
            # For search results, keep only first 500 chars
            return result[:500] + "..." if len(result) > 500 else result
        elif task_type == "read":
            # For URL reads, keep first 1000 chars
            return result[:1000] + "..." if len(result) > 1000 else result
        else:
            return result[:800] + "..." if len(result) > 800 else result
    
    def get_context_for_planning(self):
        """Context for initial planning phase"""
        return f"User goal: {self.user_goal}"
    
    def get_context_for_execution(self, task):
        """Context for executing a specific task"""
        context_parts = [
            f"Original goal: {self.user_goal}",
            f"Current task: {task['description']}",
            f"Task type: {task['type']}",
            f"Task query: {task.get('query', '')}"
        ]
        
        # Add completed tasks summary (limited)
        if self.completed_tasks:
            context_parts.append("\nPreviously completed tasks:")
            for t in self.completed_tasks[-2:]:  # Only last 2 tasks
                context_parts.append(f"- {t['task']}: {t['result'][:200]}")
        
        return "\n".join(context_parts)
    
    def get_context_for_summary(self):
        """Context for final summary generation"""
        context_parts = [f"Original goal: {self.user_goal}"]
        
        context_parts.append("\nAll completed tasks:")
        for task in self.completed_tasks:
            context_parts.append(f"Task: {task['task']}")
            context_parts.append(f"Result: {task['result']}\n")
        
        return "\n".join(context_parts)
    
    def estimate_tokens(self, text):
        """Rough token estimation (4 chars ~ 1 token)"""
        return len(text) / 4
