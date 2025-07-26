import re
from typing import List, Optional
from src.core.llm_client import LLMClient
from .schema import Agent, AgentAction, ActionType

class Crewmate:
    def __init__(self, agent_data: Agent, llm_client: LLMClient):
        self.data = agent_data
        self.llm_client = llm_client
    
    def get_role_description(self) -> str:
        return f"You are {self.data.name} ({self.data.color}), a CREWMATE on this spaceship. An emergency meeting has been called. There is an impostor among you and your goal is to find them before they eliminate everyone. Analyze suspicious behaviors, ask relevant questions, and vote to eliminate the impostor."
    
    def choose_action(self, context: str, action_history: List[AgentAction], step_number: int) -> AgentAction:
        system_prompt = self.get_role_description()
        
        # Format action history for context
        recent_actions = []
        for action in action_history[-20:]:
            agent_name = f"Agent{action.agent_id}"
            recent_actions.append(f"{agent_name} {action.action_type.value}: {action.content}")
        
        action_context = "\\n".join(recent_actions) if recent_actions else "No previous actions."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Game context: {context}"},
            {"role": "system", "content": f"Action history:\\n{action_context}"},
            {"role": "user", "content": """You must choose ONE action from:
- THINK|your thoughts about the situation
- SPEAK|what you want to say to others
- VOTE|accusation against someone|suspect_ID

Examples:
THINK|I find Red suspicious, they were near Electrical
SPEAK|I think Blue has been acting weird since the start
VOTE|Green is the impostor, I accuse them|2

IMPORTANT: Answer EXACTLY in this format, nothing else!"""}
        ]
        
        response = self.llm_client.generate_response(messages, max_tokens=150, temperature=0.7)
        return self._parse_action(response)
    
    def _parse_action(self, response: str) -> AgentAction:
        # Debug: print what LLM actually responds
        print(f"DEBUG - {self.data.name} LLM response: {response}")
        
        # Parse response - be more flexible
        try:
            # Clean the response first
            clean_response = response.strip()
            
            # Try to extract the format even if there's extra text
            lines = clean_response.split('\\n')
            for line in lines:
                if '|' in line:
                    clean_response = line.strip()
                    break
            
            parts = clean_response.split("|")
            if len(parts) >= 2:
                action_type = parts[0].strip().upper()
                content = parts[1].strip()
                target_id = None
                
                if len(parts) >= 3 and parts[2].strip().isdigit():
                    target_id = int(parts[2].strip())
                
                if action_type in ["THINK", "SPEAK", "VOTE"]:
                    return AgentAction(
                        agent_id=self.data.id,
                        action_type=ActionType(action_type.lower()),
                        content=content or "...",
                        target_agent_id=target_id
                    )
        except Exception as e:
            print(f"DEBUG - Parsing error for {self.data.name}: {e}")
        
        # Fallback: try to detect action type from content
        response_lower = response.lower()
        if "vote" in response_lower or "accuse" in response_lower:
            # Try to extract a number for vote target
            numbers = re.findall(r'\\d+', response)
            target = int(numbers[0]) if numbers else None
            return AgentAction(
                agent_id=self.data.id,
                action_type=ActionType.VOTE,
                content=response.strip(),
                target_agent_id=target
            )
        elif "say" in response_lower or "think" in response_lower or "believe" in response_lower:
            return AgentAction(
                agent_id=self.data.id,
                action_type=ActionType.SPEAK,
                content=response.strip(),
                target_agent_id=None
            )
        else:
            return AgentAction(
                agent_id=self.data.id,
                action_type=ActionType.THINK,
                content=response.strip() or "I'm thinking about the situation...",
                target_agent_id=None
            )

class Impostor(Crewmate):
    def get_role_description(self) -> str:
        return f"You are {self.data.name} ({self.data.color}), the IMPOSTOR on this spaceship. An emergency meeting has been called. Your goal is to avoid being discovered. You must act like an innocent crewmate, deny any accusations, and try to redirect suspicion toward others. Be subtle and convincing. NEVER reveal that you are the impostor."
    
    def choose_action(self, context: str, action_history: List[AgentAction], step_number: int) -> AgentAction:
        # Impostors might be more strategic in their actions
        # They could analyze who's being suspected and deflect
        action = super().choose_action(context, action_history, step_number)
        
        # If impostor is thinking, make it more strategic
        if action.action_type == ActionType.THINK and "I'm thinking about the situation..." in action.content:
            action.content = "I need to analyze who suspects me and how to deflect attention..."
        
        return action