"""Unified LLM interface supporting Ollama (local) and OpenAI"""

import os
import requests
import json
from typing import Optional, List, Dict, Any
from dotenv import load_dotenv

load_dotenv()

class LLMClient:
    """Unified client for multiple LLM providers"""
    
    def __init__(self):
        self.llm_priority = os.getenv("LLM_PRIORITY", "ollama")
        
        # Ollama configuration
        self.ollama_base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.ollama_model = os.getenv("OLLAMA_MODEL", "llama2")
        
        # OpenAI configuration (fallback)
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.openai_model = os.getenv("OPENAI_MODEL", "gpt-3.5-turbo")
        
        # Test connections
        self.ollama_available = self._test_ollama()
        self.openai_available = bool(self.openai_api_key)
        
        # Choose active provider
        self.active_provider = self._choose_provider()
        
        print(f"🤖 LLM Provider: {self.active_provider.upper()}")
        if self.active_provider == "ollama":
            print(f"   Model: {self.ollama_model}")
            print(f"   Endpoint: {self.ollama_base_url}")
        elif self.active_provider == "openai":
            print(f"   Model: {self.openai_model}")
    
    def _test_ollama(self) -> bool:
        """Test if Ollama is running and has the model"""
        try:
            # Check if Ollama server is running
            response = requests.get(f"{self.ollama_base_url}/api/tags", timeout=2)
            if response.status_code == 200:
                models = response.json().get('models', [])
                model_names = [m['name'] for m in models]
                
                # Check if our model exists
                if self.ollama_model not in [m.split(':')[0] for m in model_names]:
                    print(f"⚠️  Warning: Model '{self.ollama_model}' not found in Ollama")
                    print(f"   Available models: {', '.join(model_names)[:100]}")
                    print(f"   Pull it with: ollama pull {self.ollama_model}")
                    return False
                return True
            return False
        except requests.exceptions.ConnectionError:
            return False
        except Exception:
            return False
    
    def _choose_provider(self) -> str:
        """Choose which provider to use based on priority and availability"""
        if self.llm_priority == "ollama" and self.ollama_available:
            return "ollama"
        elif self.llm_priority == "openai" and self.openai_available:
            return "openai"
        elif self.ollama_available:
            return "ollama"
        elif self.openai_available:
            return "openai"
        else:
            print("⚠️  No LLM provider available! Using mock responses.")
            print("   To fix:")
            print("   1. Install and run Ollama: https://ollama.ai")
            print("   2. Pull a model: ollama pull llama2")
            print("   3. OR set OPENAI_API_KEY in .env")
            return "mock"
    
    def chat(self, messages: List[Dict[str, str]], temperature: float = 0.3, max_tokens: int = 1000) -> str:
        """Send chat messages to active LLM provider"""
        
        if self.active_provider == "ollama":
            return self._ollama_chat(messages, temperature, max_tokens)
        elif self.active_provider == "openai":
            return self._openai_chat(messages, temperature, max_tokens)
        else:
            return self._mock_chat(messages)
    
    def _ollama_chat(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        """Call Ollama API"""
        try:
            # Convert messages to Ollama format
            ollama_messages = []
            for msg in messages:
                ollama_messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
            
            response = requests.post(
                f"{self.ollama_base_url}/api/chat",
                json={
                    "model": self.ollama_model,
                    "messages": ollama_messages,
                    "stream": False,
                    "options": {
                        "temperature": temperature,
                        "num_predict": max_tokens
                    }
                },
                timeout=60
            )
            
            if response.status_code == 200:
                return response.json()["message"]["content"]
            else:
                error_msg = f"Ollama error: {response.status_code} - {response.text}"
                print(f"⚠️  {error_msg}")
                return self._mock_chat(messages)
                
        except requests.exceptions.Timeout:
            print("⚠️  Ollama timeout (model might be loading for the first time)")
            return self._mock_chat(messages)
        except Exception as e:
            print(f"⚠️  Ollama error: {str(e)}")
            return self._mock_chat(messages)
    
    def _openai_chat(self, messages: List[Dict[str, str]], temperature: float, max_tokens: int) -> str:
        """Call OpenAI API"""
        try:
            from openai import OpenAI
            
            client = OpenAI(api_key=self.openai_api_key)
            response = client.chat.completions.create(
                model=self.openai_model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            return response.choices[0].message.content
            
        except ImportError:
            print("⚠️  OpenAI package not installed")
            return self._mock_chat(messages)
        except Exception as e:
            print(f"⚠️  OpenAI error: {str(e)}")
            return self._mock_chat(messages)
    
    def _mock_chat(self, messages: List[Dict[str, str]]) -> str:
        """Mock responses for testing without LLM"""
        user_message = messages[-1]["content"].lower()
        
        if "plan" in user_message or "break down" in user_message:
            return json.dumps([
                {
                    "description": "Search for relevant information",
                    "type": "search",
                    "query": "main topic"
                },
                {
                    "description": "Summarize findings",
                    "type": "summarize",
                    "query": "Provide a summary"
                }
            ])
        elif "summarize" in user_message:
            return "Based on the search results, here's a summary of the key findings. [Mock response - please configure Ollama or OpenAI for real results]"
        else:
            return "I understand your request. [Mock response - please configure Ollama or OpenAI for real results]"
