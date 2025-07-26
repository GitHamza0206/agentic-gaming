import os
import requests
import base64
from typing import Optional
import logging

logger = logging.getLogger(__name__)

class ElevenLabsTTSService:
    """ElevenLabs Text-to-Speech service for converting agent speech to audio."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Default voice IDs for different agent personalities
        # These are some popular ElevenLabs voices
        self.voice_mapping = {
            "Red": "21m00Tcm4TlvDq8ikWAM",      # Rachel - confident female
            "Blue": "AZnzlk1XvdvUeBnXmlld",     # Domi - strong male  
            "Green": "EXAVITQu4vr4xnSDxMaL",    # Bella - soft female
            "Yellow": "ErXwobaYiN019PkySvjV",   # Antoni - warm male
            "Orange": "MF3mGyEYCl7XYWbV9V6O",  # Elli - young female
            "Pink": "TxGEqnHWrfWFTfGW9XjX",    # Josh - deep male
            "Purple": "VR6AewLTigWG4xSOukaG",  # Arnold - mature male
            "Cyan": "pNInz6obpgDQGcFmaJgB",    # Adam - clear male
        }
        
        # Fallback voice if agent color not found
        self.default_voice = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    
    def get_voice_for_agent(self, agent_color: str) -> str:
        """Get the appropriate voice ID for an agent based on their color."""
        return self.voice_mapping.get(agent_color, self.default_voice)
    
    async def text_to_speech(self, text: str, agent_color: str) -> Optional[str]:
        """
        Convert text to speech using ElevenLabs API.
        
        Args:
            text: The text to convert to speech
            agent_color: The agent's color to determine voice
            
        Returns:
            Base64 encoded audio data or None if failed
        """
        if not self.api_key:
            logger.warning("ElevenLabs API key not found. TTS disabled.")
            return None
            
        if not text or not text.strip():
            return None
            
        voice_id = self.get_voice_for_agent(agent_color)
        url = f"{self.base_url}/text-to-speech/{voice_id}"
        
        headers = {
            "Accept": "audio/mpeg",
            "Content-Type": "application/json",
            "xi-api-key": self.api_key
        }
        
        data = {
            "text": text.strip(),
            "model_id": "eleven_monolingual_v1",
            "voice_settings": {
                "stability": 0.5,
                "similarity_boost": 0.5
            }
        }
        
        try:
            response = requests.post(url, json=data, headers=headers, timeout=30)
            
            if response.status_code == 200:
                # Convert audio to base64 for easy transmission
                audio_base64 = base64.b64encode(response.content).decode('utf-8')
                logger.info(f"Successfully generated TTS for {agent_color} agent")
                return audio_base64
            else:
                logger.error(f"ElevenLabs API error: {response.status_code} - {response.text}")
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for TTS: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in TTS: {e}")
            return None

# Global TTS service instance
tts_service = ElevenLabsTTSService()
