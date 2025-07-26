import os
from typing import List, Dict
from cerebras.cloud.sdk import Cerebras
import openai
import time

class LLMClient:
    def __init__(self):
        # Cerebras setup
        cerebras_api_key = os.environ.get("CEREBRAS_API_KEY", "csk-wx8vctr5ytdnjc8wkj94tjp4d6ffxxf6p3ppc4jj68xydpe9")
        self.cerebras_client = Cerebras(api_key=cerebras_api_key)
        
        # OpenAI setup as fallback
        self.openai_api_key = "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"
        self.openai_client = openai.OpenAI(api_key=self.openai_api_key)
        
        # Track usage for debugging
        self.cerebras_calls = 0
        self.openai_calls = 0
        self.rate_limit_hits = 0
    
    def _convert_messages_for_api(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Convert system messages to user messages to avoid API errors"""
        converted = []
        system_content = []
        
        for msg in messages:
            if msg["role"] == "system":
                system_content.append(msg["content"])
            else:
                converted.append(msg)
        
        # If we have system content, prepend it to the first user message
        if system_content and converted:
            first_user_msg = None
            for i, msg in enumerate(converted):
                if msg["role"] == "user":
                    first_user_msg = i
                    break
            
            if first_user_msg is not None:
                system_prefix = "\n\n".join(system_content) + "\n\n"
                converted[first_user_msg]["content"] = system_prefix + converted[first_user_msg]["content"]
        
        return converted if converted else [{"role": "user", "content": "\n\n".join(system_content)}]

    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 200,
        temperature: float = 0.7
    ) -> str:
        # Convert system messages to avoid API errors
        converted_messages = self._convert_messages_for_api(messages)
        
        # First try Cerebras
        try:
            return self._generate_with_cerebras(converted_messages, max_tokens, temperature)
        except Exception as e:
            error_str = str(e)
            
            # Check if it's a rate limit error (429)
            if "429" in error_str or "rate limit" in error_str.lower() or "quota" in error_str.lower():
                print(f"⚠️ Cerebras rate limit hit, falling back to OpenAI...")
                self.rate_limit_hits += 1
                return self._generate_with_openai(converted_messages, max_tokens, temperature)
            else:
                # For other errors, also try OpenAI as fallback
                print(f"⚠️ Cerebras error ({error_str[:100]}...), trying OpenAI fallback...")
                return self._generate_with_openai(converted_messages, max_tokens, temperature)
    
    def _generate_with_cerebras(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using Cerebras API"""
        self.cerebras_calls += 1
        
        stream = self.cerebras_client.chat.completions.create(
            messages=messages,
            model="qwen-3-235b-a22b",
            stream=True,
            max_completion_tokens=max_tokens,
            temperature=temperature,
            top_p=0.95
        )
        
        response = ""
        for chunk in stream:
            if chunk.choices[0].delta.content:
                response += chunk.choices[0].delta.content
        
        return response.strip()
    
    def _generate_with_openai(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int,
        temperature: float
    ) -> str:
        """Generate response using OpenAI API as fallback"""
        self.openai_calls += 1
        
        try:
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=max_tokens,
                temperature=temperature
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            # If both APIs fail, return a fallback message
            print(f"❌ Both Cerebras and OpenAI failed: {str(e)}")
            return f"I need to think about this situation... (API Error: {str(e)[:50]})"
    
    def get_usage_stats(self) -> Dict[str, int]:
        """Get API usage statistics"""
        return {
            "cerebras_calls": self.cerebras_calls,
            "openai_calls": self.openai_calls,
            "rate_limit_hits": self.rate_limit_hits,
            "total_calls": self.cerebras_calls + self.openai_calls
        }