import os
from typing import List, Dict
from cerebras.cloud.sdk import Cerebras

class LLMClient:
    def __init__(self):
        api_key = os.environ.get("CEREBRAS_API_KEY", "csk-wx8vctr5ytdnjc8wkj94tjp4d6ffxxf6p3ppc4jj68xydpe9")
        self.client = Cerebras(api_key=api_key)
    
    def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        max_tokens: int = 200,
        temperature: float = 0.7
    ) -> str:
        try:
            stream = self.client.chat.completions.create(
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
        except Exception as e:
            return f"Erreur de génération: {str(e)}"