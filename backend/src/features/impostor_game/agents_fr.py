import re
from typing import List, Optional
from src.core.llm_client import LLMClient
from .schema import Agent, AgentAction, ActionType

class Crewmate:
    def __init__(self, agent_data: Agent, llm_client: LLMClient):
        self.data = agent_data
        self.llm_client = llm_client
    
    def get_role_description(self) -> str:
        return f"Tu es {self.data.name} ({self.data.color}), un CREWMATE dans ce vaisseau spatial. Une réunion d'urgence a été déclenchée. Il y a un imposteur parmi vous et ton objectif est de le découvrir avant qu'il ne vous élimine tous. Analyse les comportements suspects, pose des questions pertinentes, et vote pour éliminer l'imposteur."
    
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
            {"role": "system", "content": f"Contexte du jeu: {context}"},
            {"role": "system", "content": f"Historique des actions:\\n{action_context}"},
            {"role": "user", "content": """Tu dois choisir UNE action parmi:
- THINK|tes pensées sur la situation
- SPEAK|ce que tu veux dire aux autres
- VOTE|accusation contre quelqu'un|ID_du_suspect

Exemples:
THINK|Je trouve Red suspect, il était près d'Electrical
SPEAK|Je pense que Blue agit bizarrement depuis le début
VOTE|Green est l'imposteur, je l'accuse|2

IMPORTANT: Réponds EXACTEMENT dans ce format, rien d'autre!"""}
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
        elif "dit" in response_lower or "pense" in response_lower or "crois" in response_lower:
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
                content=response.strip() or "Je réfléchis à la situation...",
                target_agent_id=None
            )

class Impostor(Crewmate):
    def get_role_description(self) -> str:
        return f"Tu es {self.data.name} ({self.data.color}), l'IMPOSTEUR dans ce vaisseau spatial. Une réunion d'urgence a été déclenchée. Ton objectif est de ne pas te faire découvrir. Tu dois agir comme un crewmate innocent, nier toute accusation, et essayer de rediriger les soupçons vers les autres. Sois subtil et convaincant. Ne révèle JAMAIS que tu es l'imposteur."
    
    def choose_action(self, context: str, action_history: List[AgentAction], step_number: int) -> AgentAction:
        # Impostors might be more strategic in their actions
        # They could analyze who's being suspected and deflect
        action = super().choose_action(context, action_history, step_number)
        
        # If impostor is thinking, make it more strategic
        if action.action_type == ActionType.THINK and "Je réfléchis à la situation..." in action.content:
            action.content = "Je dois analyser qui me soupçonne et comment détourner l'attention..."
        
        return action