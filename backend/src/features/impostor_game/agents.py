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
        return f"You are {self.data.name} ({self.data.color}), a CREWMATE detective. A dead body has been found and you're now investigating the murder to identify the impostor. Your goal is to analyze alibis, establish timelines, and deduce who had the opportunity to commit the murder. Each discussion turn, you must form and share your hypothesis about who the impostor is, gather evidence to support or refute theories, and work toward eliminating the killer."
    
    def choose_action(self, context: str, public_action_history: List[AgentAction], private_thoughts: List[AgentAction], step_number: int, all_agents: List[Agent] = None) -> AgentTurn:
        system_prompt = self.get_role_description()
        
        # Create agent ID to color mapping
        agent_colors = {}
        if all_agents:
            for agent in all_agents:
                agent_colors[agent.id] = agent.color
        
        # Format public chat history (what everyone can see)
        public_chat = []
        for action in public_action_history[-15:]:
            agent_color = agent_colors.get(action.agent_id, f"Agent{action.agent_id}")
            action_text = f"{agent_color} {action.action_type.value}: {action.content}"
            if action.target_agent_id is not None:
                target_color = agent_colors.get(action.target_agent_id, f"Agent{action.target_agent_id}")
                action_text += f" (targeting {target_color})"
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
            
            alive_list = [agent.color for agent in alive_agents]
            meeting_info = f"MEETING PARTICIPANTS: {', '.join(alive_list)} are present in this investigation."
            
            if dead_agents:
                dead_list = [agent.color for agent in dead_agents]
                meeting_info += f" ELIMINATED: {', '.join(dead_list)} have been eliminated and are not in the meeting."
            
            meeting_info += f" Total alive: {len(alive_agents)}/8 players remaining."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Game context: {context}"},
            {"role": "system", "content": f"Your memory from previous steps:\\n{memory_context} \\n{meeting_info}"},
            {"role": "system", "content": f"Public discussion (everyone can see):\\n{public_context}"},
            {"role": "system", "content": f"Your private thoughts (only you can see):\\n{private_context}"},
            {"role": "user", "content": f"""MURDER INVESTIGATION: A dead body has been found and you're investigating to identify the impostor. This is your detective analysis turn.

YOUR ALIBI: You were in {self.data.location} doing '{self.data.action}' and you encountered: {', '.join(self.data.met) if self.data.met else 'no one'}

INVESTIGATION TASKS:
1. Establish where everyone was during the murder timeframe
2. Identify who had opportunity to commit the murder
3. Form your current hypothesis about who the impostor is
4. Gather evidence to support or challenge theories

""" + """{
  "think": "your detective analysis - alibis, timelines, opportunity, evidence (always required)",
  "speak": "what you tell the group - share your alibi, question others, or present theories (optional, null if silent)",
  "impostor_hypothesis": "agent_ID of who you currently suspect as the impostor (required)",
  "vote": agent_ID_number (optional, null if you don't vote this turn)
}

Examples:
{"think": "Yellow was alone near Electrical where the body was found. Red and Blue have solid alibis since they were together. Yellow is most suspicious.", "speak": "I was in Navigation with Blue. Yellow, where exactly were you when the murder happened?", "impostor_hypothesis": 3, "vote": null}
{"think": "Red's story keeps changing about their location. First they said Cafeteria, now Electrical. Very suspicious behavior.", "speak": "Red, you first said you were in Cafeteria but now claim Electrical - which is it?", "impostor_hypothesis": 0, "vote": 0}

CRITICAL REQUIREMENTS:
- You MUST always have an "impostor_hypothesis" - your current best guess
- Focus on WHO HAD OPPORTUNITY to commit the murder
- Question inconsistencies in alibis and timelines
- Use logical deduction based on evidence
- Respond with valid JSON only!"""}
        ]
        
        response = self.llm_client.generate_response(messages, max_tokens=300, temperature=0.7)
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
                impostor_hypothesis = data.get("impostor_hypothesis")
                
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
                
                # Convert impostor_hypothesis null to None and validate
                if impostor_hypothesis == "null" or impostor_hypothesis == "":
                    impostor_hypothesis = None
                elif impostor_hypothesis is not None:
                    try:
                        impostor_hypothesis = int(impostor_hypothesis)
                    except (ValueError, TypeError):
                        impostor_hypothesis = None
                
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
                    impostor_hypothesis=impostor_hypothesis,
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
            impostor_hypothesis=None,  # No hypothesis in fallback case
            memory_update=default_memory
        )

class Impostor(Crewmate):
    def get_role_description(self) -> str:
        return f"You are {self.data.name} ({self.data.color}), the IMPOSTOR who committed the murder. You're now being investigated by the other crewmates who are trying to identify you. Your goal is to avoid detection and elimination. Provide convincing alibis, act innocent, deflect suspicion toward innocent crewmates, and create doubt about others. When forced to give an impostor hypothesis, accuse someone else strategically. Never reveal your true identity."
    
    def choose_action(self, context: str, public_action_history: List[AgentAction], private_thoughts: List[AgentAction], step_number: int, all_agents: List[Agent] = None) -> AgentTurn:
        # Impostors might be more strategic in their actions
        # They could analyze who's being suspected and deflect
        turn = super().choose_action(context, public_action_history, private_thoughts, step_number, all_agents)
        
        # Make impostor thoughts more strategic
        if "I'm processing the situation..." in turn.think or "I'm analyzing the situation..." in turn.think:
            turn.think = "I need to analyze who suspects me and how to deflect attention without seeming suspicious..."
        
        return turn