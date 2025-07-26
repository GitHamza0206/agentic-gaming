import os
from typing import List, Dict
import anthropic
from dotenv import load_dotenv

class LLMClient:
    def __init__(self):
        # Load environment variables
        load_dotenv()
        
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable is not set")
        self.client = anthropic.Anthropic(api_key=api_key)
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 200,
        temperature: float = 0.7
    ) -> str:
        try:
            # Convert messages format for Anthropic
            system_message = ""
            conversation_messages = []
            
            # Filter out system messages and extract system content
            for msg in messages:
                if msg["role"] == "system":
                    system_message = msg["content"]
                elif msg["role"] in ["user", "assistant"]:
                    conversation_messages.append(msg)
            
            # Anthropic requires at least one message
            if not conversation_messages:
                conversation_messages = [{"role": "user", "content": "Continue the conversation."}]
            
            response = self.client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_message if system_message else None,
                messages=conversation_messages
            )
            
            return response.content[0].text.strip()
        except Exception as e:
            return f"Erreur de génération: {str(e)}"