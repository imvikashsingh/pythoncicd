"""Real tools for the agent - Tavily search + URL reading"""

import requests
from typing import Dict, Any, List
import os
from dotenv import load_dotenv

load_dotenv()

class Tools:
    """Available tools for the agent to use"""
    
    def __init__(self):
        self.search_provider = os.getenv("SEARCH_PROVIDER", "tavily")
        self.tavily_api_key = os.getenv("TAVILY_API_KEY")
    
    def web_search(self, query: str, max_results: int = 5) -> Dict[str, Any]:
        """
        Perform a web search using Tavily (optimized for LLMs)
        
        Args:
            query: Search query string
            max_results: Number of results to return
            
        Returns:
            Dict with success status and results or error
        """
        
        if self.search_provider == "tavily" and self.tavily_api_key:
            return self._tavily_search(query, max_results)
        else:
            # Fallback to DuckDuckGo if Tavily not configured
            return self._duckduckgo_search(query, max_results)
    
    def _tavily_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Search using Tavily API (optimized for LLM context)"""
        try:
            from tavily import TavilyClient
            
            client = TavilyClient(api_key=self.tavily_api_key)
            
            # Tavily automatically extracts relevant content
            response = client.search(
                query=query,
                search_depth="basic",  # or "advanced" for more thorough
                max_results=max_results,
                include_answer=True,  # Tavily provides a direct answer
                include_raw_content=False,  # Keep it lean
                include_images=False
            )
            
            formatted = f"Search results for '{query}':\n\n"
            
            # Add Tavily's AI-generated answer if available
            if response.get('answer'):
                formatted += f"📝 AI Summary: {response['answer']}\n\n"
            
            # Add individual results
            for i, result in enumerate(response.get('results', []), 1):
                formatted += f"{i}. {result.get('title', 'No title')}\n"
                formatted += f"   {result.get('content', 'No content')[:300]}\n"
                formatted += f"   Source: {result.get('url', 'No URL')}\n"
                formatted += f"   Score: {result.get('score', 'N/A')}\n\n"
            
            return {
                "success": True,
                "results": response.get('results', []),
                "formatted": formatted,
                "answer": response.get('answer')
            }
            
        except ImportError:
            return {
                "success": False,
                "error": "Tavily package not installed. Run: pip install tavily-python",
                "results": []
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Tavily search failed: {str(e)}",
                "results": []
            }
    
    def _duckduckgo_search(self, query: str, max_results: int) -> Dict[str, Any]:
        """Fallback search using DuckDuckGo"""
        try:
            from duckduckgo_search import DDGS
            
            with DDGS() as ddgs:
                results = []
                for r in ddgs.text(query, max_results=max_results):
                    results.append({
                        "title": r.get("title", ""),
                        "body": r.get("body", "")[:300],
                        "href": r.get("href", "")
                    })
                
                if not results:
                    return {
                        "success": False,
                        "error": f"No results found for '{query}'",
                        "results": []
                    }
                
                formatted = f"Search results for '{query}':\n\n"
                for i, r in enumerate(results, 1):
                    formatted += f"{i}. {r['title']}\n"
                    formatted += f"   {r['body']}\n"
                    formatted += f"   Source: {r['href']}\n\n"
                
                return {
                    "success": True,
                    "results": results,
                    "formatted": formatted
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": f"Search failed: {str(e)}",
                "results": []
            }
    
    def read_url(self, url: str, max_length: int = 2000) -> Dict[str, Any]:
        """Read content from a URL"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(url, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Simple text extraction
            import re
            content = response.text
            text = re.sub(r'<[^>]+>', ' ', content)
            text = re.sub(r'\s+', ' ', text).strip()
            
            # Truncate
            if len(text) > max_length:
                text = text[:max_length] + "..."
            
            return {
                "success": True,
                "content": text,
                "length": len(text)
            }
            
        except requests.RequestException as e:
            return {
                "success": False,
                "error": f"Failed to read URL: {str(e)}",
                "content": None
            }
        except Exception as e:
            return {
                "success": False,
                "error": f"Error: {str(e)}",
                "content": None
            }
