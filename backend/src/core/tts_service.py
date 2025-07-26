import os
import requests
import base64
from typing import Optional
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

logger = logging.getLogger(__name__)

class ElevenLabsTTSService:
    """ElevenLabs Text-to-Speech service for converting agent speech to audio."""
    
    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.getenv("ELEVENLABS_API_KEY")
        print(f"DEBUG - TTS Service init - ELEVENLABS_API_KEY: {self.api_key[:20] if self.api_key else 'NOT FOUND'}...")
        self.base_url = "https://api.elevenlabs.io/v1"
        
        # Default voice IDs for different agent personalities
        # These are some popular ElevenLabs voices with character-appropriate selections
        self.voice_mapping = {
            "Red": "21m00Tcm4TlvDq8ikWAM",      # Rachel - confident, assertive female
            "Blue": "AZnzlk1XvdvUeBnXmlld",     # Domi - strong, authoritative male  
            "Green": "EXAVITQu4vr4xnSDxMaL",    # Bella - calm, analytical female
            "Yellow": "ErXwobaYiN019PkySvjV",   # Antoni - warm, friendly male
            "Orange": "MF3mGyEYCl7XYWbV9V6O",  # Elli - energetic young female
            "Pink": "TxGEqnHWrfWFTfGW9XjX",    # Josh - deep, suspicious male
            "Purple": "VR6AewLTigWG4xSOukaG",  # Arnold - mature, wise male
            "Cyan": "pNInz6obpgDQGcFmaJgB",    # Adam - clear, logical male
            "Black": "29vD33N1CtxCmqQRPOHJ",   # Drew - serious, investigative male
            "White": "ThT5KcBeYPX3keUQqHPh",   # Dorothy - sweet, innocent female
            
            # Support lowercase variations for robustness
            "red": "21m00Tcm4TlvDq8ikWAM",
            "blue": "AZnzlk1XvdvUeBnXmlld", 
            "green": "EXAVITQu4vr4xnSDxMaL",
            "yellow": "ErXwobaYiN019PkySvjV",
            "orange": "MF3mGyEYCl7XYWbV9V6O",
            "pink": "TxGEqnHWrfWFTfGW9XjX",
            "purple": "VR6AewLTigWG4xSOukaG",
            "cyan": "pNInz6obpgDQGcFmaJgB",
            "black": "29vD33N1CtxCmqQRPOHJ",
            "white": "ThT5KcBeYPX3keUQqHPh",
        }
        
        # Fallback voice if agent color not found
        self.default_voice = "21m00Tcm4TlvDq8ikWAM"  # Rachel
    
    def get_voice_for_agent(self, agent_color: str) -> str:
        """Get the appropriate voice ID for an agent based on their color."""
        # Normalize color name (handle both uppercase and lowercase)
        normalized_color = agent_color.strip() if agent_color else ""
        
        # First try exact match
        voice_id = self.voice_mapping.get(normalized_color)
        if voice_id:
            return voice_id
            
        # Try capitalized version
        voice_id = self.voice_mapping.get(normalized_color.capitalize())
        if voice_id:
            return voice_id
            
        # Try lowercase version
        voice_id = self.voice_mapping.get(normalized_color.lower())
        if voice_id:
            return voice_id
            
        # Fallback to default
        logger.warning(f"No voice mapping found for agent color '{agent_color}', using default voice")
        return self.default_voice
    
    async def text_to_speech(self, text: str, agent_color: str, is_impostor: bool = False) -> Optional[str]:
        """
        Convert text to speech using ElevenLabs API.
        
        Args:
            text: The text to convert to speech
            agent_color: The agent's color to determine voice
            is_impostor: Whether the agent is an impostor (affects voice settings)
            
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
        
        # Adjust voice settings based on agent role for personality
        voice_settings = {
            "stability": 0.6 if is_impostor else 0.5,  # Impostors slightly more stable (calculated)
            "similarity_boost": 0.4 if is_impostor else 0.5,  # Impostors slightly less similar (deceptive)
            "style": 0.2 if is_impostor else 0.1,  # Impostors slightly more styled (dramatic)
            "use_speaker_boost": True
        }
        
        data = {
            "text": text.strip(),
            "model_id": "eleven_monolingual_v1",
            "voice_settings": voice_settings
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
