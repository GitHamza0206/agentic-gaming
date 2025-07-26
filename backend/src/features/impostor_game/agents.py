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
    
    def choose_action(self, context: str, public_action_history: List[AgentAction], private_thoughts: List[AgentAction], step_number: int, all_agents: List[Agent] = None) -> AgentTurn:
        system_prompt = self.get_role_description()
        
        # Create agent ID to name mapping
        agent_names = {}
        if all_agents:
            for agent in all_agents:
                agent_names[agent.id] = agent.name
        
        # Format public chat history (what everyone can see)
        public_chat = []
        for action in public_action_history[-15:]:
            agent_name = agent_names.get(action.agent_id, f"Agent{action.agent_id}")
            action_text = f"{agent_name} {action.action_type.value}: {action.content}"
            if action.target_agent_id is not None:
                target_name = agent_names.get(action.target_agent_id, f"Agent{action.target_agent_id}")
                action_text += f" (targeting {target_name})"
            public_chat.append(action_text)
        
        # Format private thoughts (only this agent's thoughts)
        private_chat = []
        for thought in private_thoughts[-10:]:
            private_chat.append(f"You thought: {thought.content}")
        
        public_context = "\\n".join(public_chat) if public_chat else "No public discussion yet."
        private_context = "\\n".join(private_chat) if private_chat else "No private thoughts yet."
        
        # Add detailed meeting participants information
        meeting_info = ""
        if all_agents:
            alive_agents = [agent for agent in all_agents if agent.is_alive]
            dead_agents = [agent for agent in all_agents if not agent.is_alive]
            
            alive_list = [f"{agent.name} ({agent.color})" for agent in alive_agents]
            meeting_info = f"MEETING PARTICIPANTS: {', '.join(alive_list)} are present in this emergency meeting."
            
            if dead_agents:
                dead_list = [f"{agent.name} ({agent.color})" for agent in dead_agents]
                meeting_info += f" ELIMINATED: {', '.join(dead_list)} have been eliminated and are not in the meeting."
            
            meeting_info += f" Total alive: {len(alive_agents)}/8 players remaining."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Game context: {context}"},
            {"role": "system", "content": meeting_info},
            {"role": "system", "content": f"Public discussion (everyone can see):\\n{public_context}"},
            {"role": "system", "content": f"Your private thoughts (only you can see):\\n{private_context}"},
            {"role": "user", "content": """RESPOND ONLY WITH VALID JSON! No XML tags, no explanations, just JSON:

{
  "think": "your private thoughts and analysis (always required, detailed)",
  "speak": "short public statement to other crewmates (optional, null if you don't speak)",
  "vote": agent_ID_number (optional, null if you don't vote)
}

Examples of CORRECT JSON format:
{"think": "Red seems suspicious based on their defensive behavior and contradictory statements about their location. I should observe more before making accusations.", "speak": null, "vote": null}
{"think": "Blue's story about being in electrical doesn't match what Green said earlier, they might be lying or confused.", "speak": "Blue, where exactly were you when the body was found?", "vote": null}
{"think": "I've analyzed all the evidence and I'm convinced Green is the impostor based on their voting pattern and deflection tactics.", "speak": "I vote Green - they've been too defensive", "vote": 2}

CRITICAL: 
- NO XML TAGS like <think> or <speak>
- ONLY JSON format like {"think": "...", "speak": null, "vote": null}
- Start your response with { and end with }
- Use null for empty values, not empty strings"""}
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
                
                # Convert speak null to None and validate it's not thinking content
                if speak == "null" or speak == "":
                    speak = None
                elif speak and len(speak) > 100:  # Too long for speaking
                    speak = None
                elif speak and any(word in speak.lower() for word in ['analysis', 'analyzing', 'i think that', 'seems like', 'based on', 'considering']):
                    speak = None  # This looks like thinking, not speaking
                    
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
        
        # Fallback: try to extract content from XML or malformed response
        response_lower = response.lower()
        think_content = "I need to analyze this situation more carefully..."
        speak_content = None
        vote_target = None
        
        # Try to extract from XML tags if present
        if "<think>" in response_lower:
            think_match = re.search(r'<think>(.*?)</think>', response, re.DOTALL | re.IGNORECASE)
            if think_match:
                think_content = think_match.group(1).strip()
        
        if "<speak>" in response_lower:
            speak_match = re.search(r'<speak>(.*?)</speak>', response, re.DOTALL | re.IGNORECASE)
            if speak_match:
                speak_content = speak_match.group(1).strip()
                if speak_content.lower() in ["null", "none", ""]:
                    speak_content = None
        
        if "<vote>" in response_lower:
            vote_match = re.search(r'<vote>(.*?)</vote>', response, re.DOTALL | re.IGNORECASE)
            if vote_match:
                vote_text = vote_match.group(1).strip()
                if vote_text.lower() not in ["null", "none", ""]:
                    try:
                        vote_target = int(vote_text)
                    except ValueError:
                        vote_target = None
        
        # If no XML found, try to extract from plain text
        if think_content == "I need to analyze this situation more carefully..." and len(response.strip()) > 10:
            think_content = response.strip()[:150]  # Use first part as thinking
        
        return AgentTurn(
            agent_id=self.data.id,
            think=think_content,
            speak=speak_content,
            vote=vote_target
        )

class Impostor(Crewmate):
    def get_role_description(self) -> str:
        return f"You are {self.data.name} ({self.data.color}), the IMPOSTOR on this spaceship. An emergency meeting has been called. Your goal is to avoid being discovered. You must act like an innocent crewmate, deny any accusations, and try to redirect suspicion toward others. Be subtle and convincing. NEVER reveal that you are the impostor."
    
    def choose_action(self, context: str, public_action_history: List[AgentAction], private_thoughts: List[AgentAction], step_number: int, all_agents: List[Agent] = None) -> AgentTurn:
        # Impostors might be more strategic in their actions
        # They could analyze who's being suspected and deflect
        turn = super().choose_action(context, public_action_history, private_thoughts, step_number, all_agents)
        
        # Make impostor thoughts more strategic
        if "I'm processing the situation..." in turn.think or "I'm analyzing the situation..." in turn.think:
            turn.think = "I need to analyze who suspects me and how to deflect attention without seeming suspicious..."
        
        return turn