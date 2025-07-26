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
        
        # Format public chat history (what everyone can see)
        public_chat = []
        print(f"DEBUG - {self.data.color} sees {len(public_action_history)} conversation messages")
        for action in public_action_history[-15:]:
            # agent_id is now the color directly
            agent_color = action.agent_id
            action_text = f"{agent_color} {action.action_type.value}: {action.content}"
            if action.target_agent_id is not None:
                action_text += f" (targeting {action.target_agent_id})"
            public_chat.append(action_text)
            print(f"DEBUG - Conversation: {action_text}")
        
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
            {"role": "system", "content": f"RECENT CONVERSATION (READ CAREFULLY - others may have asked you questions!):\\n{public_context}"},
            {"role": "system", "content": f"Your private thoughts (only you can see):\\n{private_context}"},
            {"role": "user", "content": f"""MURDER INVESTIGATION: A dead body has been found and you're investigating to identify the impostor. This is your detective analysis turn.

YOU ARE: {self.data.color} ({self.data.name})
YOUR ALIBI: You were in {self.data.location} doing '{self.data.action}' and you encountered: {', '.join(self.data.met) if self.data.met else 'no one'}

CONVERSATION ANALYSIS (CRITICAL - READ THE RECENT CONVERSATION ABOVE):
- Scan the RECENT CONVERSATION for your color name ({self.data.color}) - were you directly questioned?
- Did someone say "{self.data.color}, [question]" or accuse you of something?
- If YES: Your response MUST address that question/accusation first
- If NO direct questions: Then share your alibi or ask new questions

INVESTIGATION PRIORITIES:
1. FIRST: Answer any direct questions asked to you by name/color
2. THEN: Share your alibi and observations  
3. THEN: Question others about suspicious behavior
4. ALWAYS: State who you currently suspect and why

IMPORTANT: 
- Remember you are {self.data.color} - don't question yourself!
- Be responsive to the conversation - answer before asking new questions
- If accused, defend yourself with facts about your alibi

""" + """{
  "think": "your detective analysis - alibis, timelines, opportunity, evidence (always required)",
  "speak": "what you tell the group - share your alibi, question others, or present theories (optional, null if silent)",
  "impostor_hypothesis": "color of agent you currently suspect as the impostor (red, blue, green, or yellow)",
  "vote": "color of agent to eliminate (red, blue, green, yellow) or null if you don't vote this turn"
}

Examples:
{"think": "Someone just asked me about my card swipe task. I need to explain that I was actually doing it properly and wasn't faking it.", "speak": "Blue, you asked about my card swipe - I was having trouble with the reader, that's why it took multiple attempts. I can confirm I was in Cafeteria the whole time with you, red, and green.", "impostor_hypothesis": "yellow", "vote": null}
{"think": "No one questioned me directly, so I can share my observations. Yellow's behavior seemed suspicious when they were near the exit.", "speak": "I was doing wires in Cafeteria with everyone. Yellow, I noticed you near the exit several times - did you leave at any point?", "impostor_hypothesis": "yellow", "vote": null}

CRITICAL REQUIREMENTS:
- CHECK: Did someone ask YOU a direct question? Answer it first!
- CHECK: Were YOU accused of something? Defend yourself with your alibi!
- You MUST always have an "impostor_hypothesis" - your current best guess
- Build on the conversation - don't ignore what others just said
- Focus on WHO HAD OPPORTUNITY to commit the murder
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
                    
                # Convert vote null to None and validate color
                if vote == "null" or vote == "":
                    vote = None
                elif vote is not None:
                    # Validate it's a valid color
                    valid_colors = ["red", "blue", "green", "yellow"]
                    if isinstance(vote, str) and vote.lower() in valid_colors:
                        vote = vote.lower()
                    else:
                        vote = None
                
                # Convert impostor_hypothesis null to None and validate color
                if impostor_hypothesis == "null" or impostor_hypothesis == "":
                    impostor_hypothesis = None
                elif impostor_hypothesis is not None:
                    # Validate it's a valid color
                    valid_colors = ["red", "blue", "green", "yellow"]
                    if isinstance(impostor_hypothesis, str) and impostor_hypothesis.lower() in valid_colors:
                        impostor_hypothesis = impostor_hypothesis.lower()
                    else:
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
            # Look for color names in the response
            valid_colors = ["red", "blue", "green", "yellow"]
            found_color = None
            for color in valid_colors:
                if color in response_lower:
                    found_color = color
                    vote_target = color
                    break
            
            if found_color:
                speak_content = f"I vote for {found_color}"
            else:
                # Fallback: no clear color found
                speak_content = "I'm still analyzing the evidence"
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