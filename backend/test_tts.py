#!/usr/bin/env python3
"""
Test script for ElevenLabs TTS integration
Run this to verify TTS is working before starting the game
"""

import asyncio
import os
from src.core.tts_service import tts_service

async def test_tts():
    """Test the TTS service with sample agent speech"""
    
    # Set the API key (you can also set this in .env file)
    api_key = "sk_7b6c0905b03564ec1e8c3db93d54f25bfc464c99ad3c7f07"
    tts_service.api_key = api_key
    
    print("Testing ElevenLabs TTS integration...")
    print(f"API Key configured: {'Yes' if tts_service.api_key else 'No'}")
    
    # Test different agent voices
    test_cases = [
        ("Red", "I was in the electrical room fixing the wiring when I heard a scream!"),
        ("Blue", "That's suspicious. Red, can you prove you were really there?"),
        ("Green", "I saw Red near the cafeteria earlier, not electrical."),
        ("Yellow", "Wait, let me think about this carefully before we vote."),
    ]
    
    for agent_color, speech_text in test_cases:
        print(f"\nTesting {agent_color} agent speech...")
        print(f"Text: {speech_text}")
        
        try:
            audio_data = await tts_service.text_to_speech(speech_text, agent_color)
            
            if audio_data:
                print(f"✅ TTS successful for {agent_color}! Audio data length: {len(audio_data)} characters")
                
                # Optionally save to file for testing
                if input(f"Save {agent_color} audio to file? (y/n): ").lower() == 'y':
                    import base64
                    audio_bytes = base64.b64decode(audio_data)
                    filename = f"test_audio_{agent_color.lower()}.mp3"
                    with open(filename, 'wb') as f:
                        f.write(audio_bytes)
                    print(f"Audio saved as {filename}")
            else:
                print(f"❌ TTS failed for {agent_color}")
                
        except Exception as e:
            print(f"❌ Error testing {agent_color}: {e}")
    
    print("\nTTS test completed!")

if __name__ == "__main__":
    asyncio.run(test_tts())
