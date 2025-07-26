import re
import json
from typing import List, Optional
from src.core.llm_client import LLMClient
from .schema import Agent, AgentAction, ActionType, AgentTurn

class Crewmate:
    def __init__(self, agent_data: Agent, llm_client: LLMClient):
        self.data = agent_data
        self.llm_client = llm_client
    
    def get_role_description(self) -> str:
        return f"You are {self.data.name} ({self.data.color}), a CREWMATE on this spaceship. An emergency meeting has been called. There is an impostor among you and your goal is to find them before they eliminate everyone. Analyze suspicious behaviors, ask relevant questions, and vote to eliminate the impostor."
    
    def choose_action(self, context: str, public_action_history: List[AgentAction], private_thoughts: List[AgentAction], step_number: int) -> AgentTurn:
        system_prompt = self.get_role_description()
        
        # Format public chat history (what everyone can see)
        public_chat = []
        for action in public_action_history[-15:]:
            agent_name = f"Agent{action.agent_id}"
            action_text = f"{agent_name} {action.action_type.value}: {action.content}"
            if action.target_agent_id is not None:
                action_text += f" (targeting Agent{action.target_agent_id})"
            public_chat.append(action_text)
        
        # Format private thoughts (only this agent's thoughts)
        private_chat = []
        for thought in private_thoughts[-10:]:
            private_chat.append(f"You thought: {thought.content}")
        
        public_context = "\\n".join(public_chat) if public_chat else "No public discussion yet."
        private_context = "\\n".join(private_chat) if private_chat else "No private thoughts yet."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Game context: {context}"},
            {"role": "system", "content": f"Public discussion (everyone can see):\\n{public_context}"},
            {"role": "system", "content": f"Your private thoughts (only you can see):\\n{private_context}"},
            {"role": "user", "content": """You must respond in JSON format with your turn. You ALWAYS think privately, and can optionally speak publicly or vote:

{
  "think": "your private thoughts and analysis (always required, detailed)",
  "speak": "short public statement to other crewmates (optional, null if you don't speak)",
  "vote": agent_ID_number (optional, null if you don't vote)
}

Examples:
{"think": "Red seems suspicious based on their defensive behavior and contradictory statements about their location", "speak": null, "vote": null}
{"think": "Blue's story about being in electrical doesn't match what Green said earlier, they might be lying", "speak": "Blue, you said you were in electrical but Green saw someone else there", "vote": null}
{"think": "I've analyzed all the evidence and I'm convinced Green is the impostor based on their voting pattern", "speak": "Green has been deflecting suspicion all game, I think they're the impostor", "vote": 2}

IMPORTANT: 
- "think" = your private thoughts and detailed analysis (always required, only you can see this)
- "speak" = what you say out loud to everyone (optional, short public statement, set to null if you stay silent)
- "vote" = agent ID to eliminate (optional, only when you're confident, set to null otherwise)
- Keep "speak" SHORT and direct, different from your private thoughts
- Respond with valid JSON only!"""}
        ]
        
        response = self.llm_client.generate_response(messages, max_tokens=200, temperature=0.7)
        return self._parse_turn(response)
    
    def _parse_turn(self, response: str) -> AgentTurn:
        # Debug: print what LLM actually responds
        print(f"DEBUG - {self.data.name} LLM response: {response}")
        
        # Try to parse JSON response with new format
        try:
            # Clean the response - look for JSON object
            clean_response = response.strip()
            
            # Find JSON object in response (in case there's extra text)
            start_idx = clean_response.find('{')
            end_idx = clean_response.rfind('}')
            
            if start_idx != -1 and end_idx != -1 and end_idx > start_idx:
                json_str = clean_response[start_idx:end_idx + 1]
                data = json.loads(json_str)
                
                think = data.get("think", "")
                speak = data.get("speak")
                vote = data.get("vote")
                
                # Ensure think is not empty
                if not think:
                    think = "I'm processing the situation..."
                
                # Convert speak null to None
                if speak == "null" or speak == "":
                    speak = None
                    
                # Convert vote null to None and validate
                if vote == "null" or vote == "":
                    vote = None
                elif vote is not None:
                    try:
                        vote = int(vote)
                    except (ValueError, TypeError):
                        vote = None
                
                return AgentTurn(
                    agent_id=self.data.id,
                    think=think,
                    speak=speak,
                    vote=vote
                )
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"DEBUG - JSON parsing error for {self.data.name}: {e}")
        
        # Fallback: try to extract meaningful content
        response_lower = response.lower()
        think_content = f"I'm analyzing the situation... {response.strip()[:100]}"  # Use part of response as thinking
        speak_content = None
        vote_target = None
        
        # Look for voting patterns
        if "vote" in response_lower or "accuse" in response_lower:
            numbers = re.findall(r'\\d+', response)
            if numbers:
                vote_target = int(numbers[0])
                # Extract a short statement for speaking
                speak_content = f"I vote for Agent{numbers[0]}"
        elif "say" in response_lower or "speak" in response_lower or "tell" in response_lower:
            # Extract a short speaking statement
            speak_content = response.strip()[:80] + "..." if len(response.strip()) > 80 else response.strip()
        
        return AgentTurn(
            agent_id=self.data.id,
            think=think_content,
            speak=speak_content,
            vote=vote_target
        )

class Impostor(Crewmate):
    def get_role_description(self) -> str:
        return f"You are {self.data.name} ({self.data.color}), the IMPOSTOR on this spaceship. An emergency meeting has been called. Your goal is to avoid being discovered. You must act like an innocent crewmate, deny any accusations, and try to redirect suspicion toward others. Be subtle and convincing. NEVER reveal that you are the impostor."
    
    def choose_action(self, context: str, public_action_history: List[AgentAction], private_thoughts: List[AgentAction], step_number: int) -> AgentTurn:
        # Impostors might be more strategic in their actions
        # They could analyze who's being suspected and deflect
        turn = super().choose_action(context, public_action_history, private_thoughts, step_number)
        
        # Make impostor thoughts more strategic
        if "I'm processing the situation..." in turn.think or "I'm analyzing the situation..." in turn.think:
            turn.think = "I need to analyze who suspects me and how to deflect attention without seeming suspicious..."
        
        return turn