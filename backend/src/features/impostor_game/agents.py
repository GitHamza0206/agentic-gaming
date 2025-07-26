import re
import json
from typing import List, Optional
from src.core.llm_client import LLMClient
from .schema import Agent, AgentAction, ActionType, AgentTurn, AgentMemory

class Crewmate:
    def __init__(self, agent_data: Agent, llm_client: LLMClient):
        self.data = agent_data
        self.llm_client = llm_client
    
    def get_role_description(self) -> str:
        return f"You are {self.data.name} ({self.data.color}), a CREWMATE on this spaceship. You are currently in an EMERGENCY MEETING discussing who the impostor is. Someone found a dead body, so now everyone is gathered at the meeting table to debate and vote. Your goal is to find the impostor before they eliminate everyone. Share what you saw, analyze others' stories for inconsistencies, and vote to eliminate the impostor."
    
    async def choose_action(self, context: str, public_action_history: List[AgentAction], private_thoughts: List[AgentAction], step_number: int, all_agents: List[Agent] = None) -> AgentTurn:
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
        
        # Format memory history for better context
        memory_context = self._format_memory_context()
        
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
            {"role": "system", "content": f"Your memory from previous steps:\\n{memory_context} \\n{meeting_info}"},
            {"role": "system", "content": f"Public discussion (everyone can see):\\n{public_context}"},
            {"role": "system", "content": f"Your private thoughts (only you can see):\\n{private_context}"},
            {"role": "user", "content": f"""You are currently in an EMERGENCY MEETING at the meeting table discussing who the impostor is. Respond in JSON format for this discussion turn.

WHAT YOU WERE DOING BEFORE THE MEETING: You were in {self.data.location} doing '{self.data.action}' and you encountered: {', '.join(self.data.met) if self.data.met else 'no one'}

""" + """{
  "think": "your private analysis of the situation and other players (always required)",
  "speak": "what you say to the group about what you observed or your suspicions (optional, null if silent)",
  "vote": agent_ID_number (optional, null if you don't vote),
}

Examples:
{"think": "Red's story doesn't match what I saw - they claim they were alone but I saw them with Blue", "speak": "I was doing navigation tasks and saw Red and Blue together in Electrical", "vote": null}
{"think": "Yellow's timeline is suspicious, they're probably the impostor", "speak": "Yellow, you said you were in Cafeteria but the body was found in Electrical", "vote": 3}

IMPORTANT: 
- This is a DISCUSSION about what happened BEFORE the meeting
- Share what you observed and analyze others' stories for contradictions
- "think" = your private analysis (always required)
- "speak" = what you tell the group (optional)
- "vote" = agent ID to eliminate (optional)
- Respond with valid JSON only!"""}
        ]
        
        response = await self.llm_client.generate_response(messages, max_tokens=300, temperature=0.7)
        return self._parse_turn(response, step_number)
    
    def _format_memory_context(self) -> str:
        """Format agent's memory history for context"""
        if not self.data.memory_history:
            return "No previous memories."
        
        memory_lines = []
        for memory in self.data.memory_history[-5:]:  # Last 5 steps
            lines = [f"Step {memory.step_number}: I was in {memory.location} doing '{memory.action}'"]
            if memory.met:
                lines.append(f"  Met: {', '.join(memory.met)}")
            memory_lines.extend(lines)
        
        return "\\n".join(memory_lines)
    
    def _parse_turn(self, response: str, step_number: int) -> AgentTurn:
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
                
                # Create simple memory update based on current data
                memory_update = AgentMemory(
                    step_number=step_number,
                    location=self.data.location,
                    action=self.data.action,
                    met=self.data.met
                )

                return AgentTurn(
                    agent_id=self.data.id,
                    think=think,
                    speak=speak,
                    vote=vote,
                    memory_update=memory_update
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
        
        # Create fallback memory
        default_memory = AgentMemory(
            step_number=step_number,
            location=self.data.location,
            action=self.data.action,
            met=self.data.met
        )
        
        return AgentTurn(
            agent_id=self.data.id,
            think=think_content,
            speak=speak_content,
            vote=vote_target,
            memory_update=default_memory
        )

class Impostor(Crewmate):
    def get_role_description(self) -> str:
        return f"You are {self.data.name} ({self.data.color}), the IMPOSTOR on this spaceship. You are currently in an EMERGENCY MEETING at the meeting table. Someone found a dead body and now everyone is discussing who the impostor is. Your goal is to avoid being discovered and eliminated. Act like an innocent crewmate, provide believable alibis, deflect suspicion toward others, and never reveal that you are the impostor. Be strategic and convincing."
    
    async def choose_action(self, context: str, public_action_history: List[AgentAction], private_thoughts: List[AgentAction], step_number: int, all_agents: List[Agent] = None) -> AgentTurn:
        # Impostors might be more strategic in their actions
        # They could analyze who's being suspected and deflect
        turn = await super().choose_action(context, public_action_history, private_thoughts, step_number, all_agents)
        
        # Make impostor thoughts more strategic
        if "I'm processing the situation..." in turn.think or "I'm analyzing the situation..." in turn.think:
            turn.think = "I need to analyze who suspects me and how to deflect attention without seeming suspicious..."
        
        return turn