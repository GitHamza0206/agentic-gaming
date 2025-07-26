import re
import random
from typing import List, Optional, Dict
from src.core.llm_client import LLMClient
from .schema import Agent, AgentAction, ActionType, GameState, Statement, Vote, MeetingResult, MeetingPhase

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
            
            # Handle HTML-like tag format (e.g., <think>content</think>)
            if clean_response.startswith('<'):
                if clean_response.startswith('<think>'):
                    content = clean_response.replace('<think>', '').replace('</think>', '').strip()
                    return AgentAction(
                        agent_id=self.data.id,
                        action_type=ActionType.THINK,
                        content=content or "I'm thinking about the situation...",
                        target_agent_id=None
                    )
                elif clean_response.startswith('<speak>'):
                    content = clean_response.replace('<speak>', '').replace('</speak>', '').strip()
                    return AgentAction(
                        agent_id=self.data.id,
                        action_type=ActionType.SPEAK,
                        content=content or "...",
                        target_agent_id=None
                    )
                elif clean_response.startswith('<vote>'):
                    content = clean_response.replace('<vote>', '').replace('</vote>', '').strip()
                    # Try to extract target ID from content
                    numbers = re.findall(r'\d+', content)
                    target_id = int(numbers[0]) if numbers else None
                    return AgentAction(
                        agent_id=self.data.id,
                        action_type=ActionType.VOTE,
                        content=content,
                        target_agent_id=target_id
                    )
            
            # Try to extract the pipe-separated format
            lines = clean_response.split('\n')
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
    
    def generate_statement(self, context: Dict, dialogue_history: List[Statement], is_follow_up: bool = False) -> str:
        """Generate a statement for round table meeting"""
        role_desc = self.get_role_description()
        
        # Build context for statement generation
        recent_statements = dialogue_history[-10:] if dialogue_history else []
        statement_context = "\n".join([f"{s.agent_name}: {s.content}" for s in recent_statements])
        
        statement_type = "follow-up statement" if is_follow_up else "initial statement"
        
        messages = [
            {"role": "system", "content": role_desc},
            {"role": "system", "content": f"Meeting context: {context.get('meeting_reason', 'Emergency meeting')}. Alive players: {context.get('alive_count', 8)}"},
            {"role": "system", "content": f"Recent statements:\n{statement_context}" if statement_context else "No previous statements."},
            {"role": "user", "content": f"Give your {statement_type}. Be concise (2-3 sentences). Stay in character."}
        ]
        
        response = self.llm_client.generate_response(messages, max_tokens=150, temperature=0.7)
        return response if response else f"I need to think about this situation..."
    
    def decide_action(self, dialogue_history: List[Statement], current_votes: List, alive_agents: List[Agent]) -> str:
        """Decide whether to speak or vote at this moment"""
        role_desc = self.get_role_description()
        
        # Build context from recent dialogue and current votes
        recent_statements = dialogue_history[-8:] if dialogue_history else []
        dialogue_context = "\n".join([f"{s.agent_name}: {s.content}" for s in recent_statements])
        
        # Build vote context
        vote_context = ""
        if current_votes:
            vote_summary = {}
            for vote in current_votes:
                target = vote.target_name
                if target in vote_summary:
                    vote_summary[target] += 1
                else:
                    vote_summary[target] = 1
            vote_context = f"\nCurrent votes: {', '.join([f'{target}: {count}' for target, count in vote_summary.items()])}"
        
        # Check if this agent has already voted
        has_voted = any(vote.voter_id == self.data.id for vote in current_votes)
        if has_voted:
            return "speak"  # If already voted, can only speak
        
        # Check if mentioned or under suspicion
        mentioned_recently = any(self.data.name.lower() in s.content.lower() for s in recent_statements)
        
        messages = [
            {"role": "system", "content": role_desc},
            {"role": "system", "content": f"Recent discussion:\n{dialogue_context}" if dialogue_context else "No previous discussion."},
            {"role": "system", "content": f"Current voting situation:{vote_context}" if vote_context else "No votes cast yet."},
            {"role": "user", "content": "You can either SPEAK (share thoughts/defend/accuse) or VOTE (cast your vote now). What do you want to do? Answer only 'SPEAK' or 'VOTE' followed by a brief reason (max 8 words)."}
        ]
        
        try:
            response = self.llm_client.generate_response(messages, max_tokens=25, temperature=0.6)
            response_upper = response.upper().strip()
            if response_upper.startswith('VOTE'):
                return "vote"
            elif response_upper.startswith('SPEAK'):
                return "speak"
            else:
                # Fallback: if mentioned recently or many votes cast, tend to speak; otherwise vote
                if mentioned_recently or len(current_votes) >= len(alive_agents) // 2:
                    return "speak"
                else:
                    return "vote" if random.random() < 0.4 else "speak"
        except Exception as e:
            print(f"LLM error in decide_action for {self.data.name}: {e}")
            # Fallback logic
            if mentioned_recently:
                return "speak"
            elif len(current_votes) >= len(alive_agents) // 2:
                return "vote"  # Many people voted, time to vote
            else:
                return "speak"  # Default to speaking early in meeting

    def should_raise_hand(self, dialogue_history: List[Statement]) -> bool:
        """Use LLM to decide whether to raise hand for follow-up statement"""
        role_desc = self.get_role_description()
        
        # Build context from recent dialogue
        recent_statements = dialogue_history[-8:] if dialogue_history else []
        dialogue_context = "\n".join([f"{s.agent_name}: {s.content}" for s in recent_statements])
        
        # Check if this agent has been mentioned recently
        mentioned_recently = any(self.data.name.lower() in s.content.lower() for s in recent_statements)
        mention_context = f"\nNote: You have been mentioned in recent discussion." if mentioned_recently else ""
        
        messages = [
            {"role": "system", "content": role_desc},
            {"role": "system", "content": f"Recent discussion:\n{dialogue_context}" if dialogue_context else "No previous discussion."},
            {"role": "system", "content": f"You are deciding whether to raise your hand to speak again in this emergency meeting.{mention_context}"},
            {"role": "user", "content": "Do you want to raise your hand to speak again? Consider: 1) Do you have new information to share? 2) Do you need to defend yourself? 3) Do you want to question someone? Answer only 'YES' or 'NO' followed by a brief reason (max 10 words)."}
        ]
        
        try:
            response = self.llm_client.generate_response(messages, max_tokens=30, temperature=0.6)
            # Parse response - look for YES/NO at the beginning
            response_upper = response.upper().strip()
            if response_upper.startswith('YES'):
                return True
            elif response_upper.startswith('NO'):
                return False
            else:
                # Fallback: if response is unclear, use simple heuristic
                return mentioned_recently or (len(dialogue_history) > 5 and random.random() < 0.3)
        except Exception as e:
            print(f"LLM error in should_raise_hand for {self.data.name}: {e}")
            # Fallback to simple logic if LLM fails
            mentioned_recently = any(self.data.name.lower() in s.content.lower() for s in recent_statements)
            return mentioned_recently or (len(dialogue_history) > 5 and random.random() < 0.3)
    
    def vote_in_meeting(self, context: Dict, dialogue_history: List[Statement], alive_agents: List[Agent]) -> tuple[Optional[int], str]:
        """Vote for a target agent or skip in round table meeting"""
        role_desc = self.get_role_description()
        
        # Build voting context
        recent_statements = dialogue_history[-15:] if dialogue_history else []
        statement_context = "\n".join([f"{s.agent_name}: {s.content}" for s in recent_statements])
        
        voteable_agents = [a for a in alive_agents if a.id != self.data.id]
        agent_list = ", ".join([f"{a.name} (ID: {a.id})" for a in voteable_agents])
        
        messages = [
            {"role": "system", "content": role_desc},
            {"role": "system", "content": f"Meeting discussion:\n{statement_context}" if statement_context else "No discussion yet."},
            {"role": "system", "content": f"Voteable agents: {agent_list}"},
            {"role": "user", "content": "Vote for who you think is the impostor, or skip. Format: 'VOTE|agent_id|reason' or 'SKIP|reason'. Be decisive based on the discussion."}
        ]
        
        response = self.llm_client.generate_response(messages, max_tokens=100, temperature=0.6)
        
        # Parse voting response
        try:
            if response.upper().startswith('SKIP'):
                reason = response.split('|', 1)[1] if '|' in response else "Need more information"
                return None, reason
            elif response.upper().startswith('VOTE'):
                parts = response.split('|')
                if len(parts) >= 3:
                    target_id = int(parts[1].strip())
                    reason = parts[2].strip()
                    if any(a.id == target_id for a in voteable_agents):
                        return target_id, reason
        except:
            pass
        
        # Fallback: random vote or skip
        if voteable_agents and random.random() > 0.2:
            target = random.choice(voteable_agents)
            return target.id, f"I suspect {target.name} based on their behavior."
        else:
            return None, "I need more information to make a decision."
    
    def select_kill_target(self, context: Dict, alive_agents: List[Agent]) -> Optional[int]:
        """Select next kill target (only for impostors)"""
        return None  # Crewmates don't kill

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
    
    def should_raise_hand(self, dialogue_history: List[Statement]) -> bool:
        """Impostors use LLM to make strategic decisions about when to speak"""
        role_desc = self.get_role_description()
        
        # Build context from recent dialogue
        recent_statements = dialogue_history[-8:] if dialogue_history else []
        dialogue_context = "\n".join([f"{s.agent_name}: {s.content}" for s in recent_statements])
        
        # Check if under suspicion (mentioned with suspicious keywords)
        suspicion_keywords = ['suspect', 'suspicious', 'impostor', 'vote', 'guilty', 'lying']
        under_suspicion = any(self.data.name.lower() in s.content.lower() and 
                             any(word in s.content.lower() for word in suspicion_keywords) 
                             for s in recent_statements)
        
        # Check if simply mentioned
        mentioned_recently = any(self.data.name.lower() in s.content.lower() for s in recent_statements)
        
        suspicion_context = ""
        if under_suspicion:
            suspicion_context = "\nIMPORTANT: You are under suspicion! You may need to defend yourself carefully."
        elif mentioned_recently:
            suspicion_context = "\nNote: You have been mentioned in recent discussion."
        
        messages = [
            {"role": "system", "content": role_desc},
            {"role": "system", "content": f"Recent discussion:\n{dialogue_context}" if dialogue_context else "No previous discussion."},
            {"role": "system", "content": f"You are deciding whether to raise your hand to speak again. As the impostor, be strategic: defend when necessary, but don't draw unnecessary attention.{suspicion_context}"},
            {"role": "user", "content": "Do you want to raise your hand to speak again? Consider: 1) Are you under suspicion and need to defend? 2) Can you deflect suspicion to others? 3) Should you stay quiet to avoid attention? Answer only 'YES' or 'NO' followed by a brief strategic reason (max 10 words)."}
        ]
        
        try:
            response = self.llm_client.generate_response(messages, max_tokens=30, temperature=0.6)
            # Parse response - look for YES/NO at the beginning
            response_upper = response.upper().strip()
            if response_upper.startswith('YES'):
                return True
            elif response_upper.startswith('NO'):
                return False
            else:
                # Fallback: strategic heuristic for impostors
                if under_suspicion:
                    return random.random() < 0.7  # Likely to defend when under suspicion
                elif mentioned_recently:
                    return random.random() < 0.4  # Moderate response when mentioned
                else:
                    return random.random() < 0.2  # Stay quiet when flying under radar
        except Exception as e:
            print(f"LLM error in should_raise_hand for {self.data.name}: {e}")
            # Fallback to strategic logic if LLM fails
            if under_suspicion:
                return random.random() < 0.7
            elif mentioned_recently:
                return random.random() < 0.4
            else:
                return random.random() < 0.2
    
    def select_kill_target(self, context: Dict, alive_agents: List[Agent]) -> Optional[int]:
        """Select next kill target strategically"""
        potential_targets = [a for a in alive_agents if not a.is_impostor and a.is_alive and a.id != self.data.id]
        
        if not potential_targets:
            return None
        
        # Strategy: target someone who hasn't been very vocal (less suspicious)
        # For now, random selection
        target = random.choice(potential_targets)
        return target.id


class ContextManager:
    """Manages personalized context for different agent types"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
    
    def get_agent_context(self, agent: Agent, game_state: GameState) -> Dict[str, any]:
        """Get personalized context for an agent based on their role"""
        base_context = {
            "game_id": game_state.game_id,
            "step_number": game_state.step_number,
            "max_steps": game_state.max_steps,
            "meeting_reason": game_state.meeting_reason,
            "alive_agents": [a for a in game_state.agents if a.is_alive],
            "recent_actions": game_state.action_history[-10:] if game_state.action_history else []
        }
        
        if agent.is_impostor:
            return self._get_impostor_context(agent, game_state, base_context)
        else:
            return self._get_crewmate_context(agent, game_state, base_context)
    
    def _get_impostor_context(self, agent: Agent, game_state: GameState, base_context: Dict) -> Dict:
        """Enhanced context for impostor with strategic information"""
        alive_agents = [a for a in game_state.agents if a.is_alive and a.id != agent.id]
        
        # Analyze who might be suspicious of the impostor
        suspicion_analysis = self._analyze_suspicion_towards_agent(agent, game_state.action_history)
        
        # Find potential scapegoats (agents being accused by others)
        scapegoat_opportunities = self._find_scapegoat_opportunities(game_state.action_history, alive_agents)
        
        impostor_context = base_context.copy()
        impostor_context.update({
            "role_type": "impostor",
            "suspicion_level": suspicion_analysis,
            "potential_targets": [a.name for a in alive_agents],
            "scapegoat_opportunities": scapegoat_opportunities,
            "strategy_hint": self._get_impostor_strategy_hint(game_state, suspicion_analysis)
        })
        
        return impostor_context
    
    def _get_crewmate_context(self, agent: Agent, game_state: GameState, base_context: Dict) -> Dict:
        """Enhanced context for crewmate with deduction information"""
        alive_agents = [a for a in game_state.agents if a.is_alive]
        
        # Analyze suspicious behaviors from action history
        suspicious_behaviors = self._analyze_suspicious_behaviors(game_state.action_history, alive_agents)
        
        # Find logical deductions based on voting patterns
        voting_analysis = self._analyze_voting_patterns(game_state.action_history, game_state.current_votes)
        
        crewmate_context = base_context.copy()
        crewmate_context.update({
            "role_type": "crewmate",
            "suspicious_behaviors": suspicious_behaviors,
            "voting_analysis": voting_analysis,
            "deduction_hints": self._get_crewmate_deduction_hints(suspicious_behaviors, voting_analysis)
        })
        
        return crewmate_context
    
    def _analyze_suspicion_towards_agent(self, target_agent: Agent, action_history: List[AgentAction]) -> str:
        """Analyze how much suspicion is directed towards a specific agent"""
        accusations = 0
        mentions = 0
        
        for action in action_history[-15:]:  # Look at recent actions
            if action.action_type == ActionType.VOTE and action.target_agent_id == target_agent.id:
                accusations += 1
            elif action.action_type == ActionType.SPEAK and target_agent.name.lower() in action.content.lower():
                mentions += 1
        
        if accusations >= 2:
            return "high"
        elif accusations >= 1 or mentions >= 3:
            return "medium"
        else:
            return "low"
    
    def _find_scapegoat_opportunities(self, action_history: List[AgentAction], alive_agents: List[Agent]) -> List[str]:
        """Find agents who are already being accused by others"""
        accusation_counts = {}
        
        for action in action_history[-10:]:
            if action.action_type == ActionType.VOTE and action.target_agent_id:
                target_name = next((a.name for a in alive_agents if a.id == action.target_agent_id), None)
                if target_name:
                    accusation_counts[target_name] = accusation_counts.get(target_name, 0) + 1
        
        # Return agents with multiple accusations as potential scapegoats
        return [name for name, count in accusation_counts.items() if count >= 2]
    
    def _analyze_suspicious_behaviors(self, action_history: List[AgentAction], alive_agents: List[Agent]) -> Dict[str, List[str]]:
        """Analyze suspicious behaviors for crewmates to notice"""
        behaviors = {}
        
        for agent in alive_agents:
            agent_behaviors = []
            agent_actions = [a for a in action_history if a.agent_id == agent.id]
            
            # Check for defensive behavior
            defensive_count = sum(1 for a in agent_actions if a.action_type == ActionType.SPEAK and 
                                any(word in a.content.lower() for word in ['not me', 'innocent', 'trust me', 'believe me']))
            
            if defensive_count >= 2:
                agent_behaviors.append("overly defensive")
            
            # Check for deflection attempts
            vote_actions = [a for a in agent_actions if a.action_type == ActionType.VOTE]
            if len(vote_actions) >= 2:
                agent_behaviors.append("quick to accuse others")
            
            # Check for inconsistent statements
            speak_actions = [a for a in agent_actions if a.action_type == ActionType.SPEAK]
            if len(speak_actions) >= 3:
                agent_behaviors.append("talks a lot (possibly deflecting)")
            
            if agent_behaviors:
                behaviors[agent.name] = agent_behaviors
        
        return behaviors
    
    def _analyze_voting_patterns(self, action_history: List[AgentAction], current_votes: Dict[int, int]) -> Dict[str, any]:
        """Analyze voting patterns for logical deductions"""
        vote_actions = [a for a in action_history if a.action_type == ActionType.VOTE]
        
        return {
            "total_votes_cast": len(vote_actions),
            "current_vote_distribution": current_votes,
            "bandwagon_effect": len(current_votes) > 0 and max(current_votes.values()) >= 3
        }
    
    def _get_impostor_strategy_hint(self, game_state: GameState, suspicion_level: str) -> str:
        """Provide strategic hints for impostors"""
        if suspicion_level == "high":
            return "You're under heavy suspicion. Focus on defending yourself and redirecting blame."
        elif suspicion_level == "medium":
            return "Some suspicion on you. Be careful and try to blend in while subtly accusing others."
        else:
            return "You're flying under the radar. Consider making strategic accusations to eliminate threats."
    
    def _get_crewmate_deduction_hints(self, suspicious_behaviors: Dict, voting_analysis: Dict) -> List[str]:
        """Provide deduction hints for crewmates"""
        hints = []
        
        if suspicious_behaviors:
            most_suspicious = max(suspicious_behaviors.keys(), key=lambda x: len(suspicious_behaviors[x]))
            hints.append(f"{most_suspicious} shows the most suspicious behavior patterns")
        
        if voting_analysis.get("bandwagon_effect"):
            hints.append("Be careful of bandwagon voting - the impostor might be leading it")
        
        if voting_analysis.get("total_votes_cast", 0) < 3:
            hints.append("Not many votes yet - gather more information before deciding")
        
        return hints


class SupervisorAgent:
    """Orchestrates meeting discussions and manages turn-based dialogue"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm_client = llm_client
        self.context_manager = ContextManager(llm_client)
    
    def orchestrate_meeting_step(self, game_state: GameState, agents: List[Agent]) -> List[AgentAction]:
        """Orchestrate one step of the meeting with structured turn-taking"""
        alive_agents = [a for a in agents if a.is_alive]
        
        # Determine speaking order for this step
        speaking_order = self._determine_speaking_order(alive_agents, game_state)
        
        step_actions = []
        
        for agent_data in speaking_order:
            # Get personalized context for this agent
            context = self.context_manager.get_agent_context(agent_data, game_state)
            
            # Create agent instance
            if agent_data.is_impostor:
                agent = Impostor(agent_data, self.llm_client)
            else:
                agent = Crewmate(agent_data, self.llm_client)
            
            # Generate action with enhanced context
            action = self._generate_supervised_action(agent, context, game_state)
            step_actions.append(action)
        
        return step_actions
    
    def _determine_speaking_order(self, alive_agents: List[Agent], game_state: GameState) -> List[Agent]:
        """Determine the order in which agents should speak this step"""
        # Strategy: Mix random order with priority-based selection
        
        # Priority factors:
        # 1. Agents who haven't spoken recently get priority
        # 2. Reporter gets priority in early steps
        # 3. Add some randomness for natural flow
        
        recent_speakers = set()
        if len(game_state.action_history) >= 5:
            recent_actions = game_state.action_history[-5:]
            recent_speakers = {a.agent_id for a in recent_actions if a.action_type == ActionType.SPEAK}
        
        # Separate agents into priority groups
        high_priority = []
        normal_priority = []
        
        for agent in alive_agents:
            # Reporter gets high priority in first few steps
            if agent.id == game_state.reporter_id and game_state.step_number <= 3:
                high_priority.append(agent)
            # Agents who haven't spoken recently get priority
            elif agent.id not in recent_speakers:
                high_priority.append(agent)
            else:
                normal_priority.append(agent)
        
        # Shuffle within priority groups
        random.shuffle(high_priority)
        random.shuffle(normal_priority)
        
        # Limit speakers per step to avoid overwhelming output
        max_speakers_per_step = min(4, len(alive_agents))
        selected_speakers = (high_priority + normal_priority)[:max_speakers_per_step]
        
        return selected_speakers
    
    def _generate_supervised_action(self, agent, context: Dict, game_state: GameState) -> AgentAction:
        """Generate an action with supervisor guidance and enhanced context"""
        # Build enhanced prompt with personalized context
        context_str = self._build_context_string(context, game_state)
        
        # Use the agent's existing choose_action method but with enhanced context
        action = agent.choose_action(context_str, game_state.action_history, game_state.step_number)
        
        # Add supervisor validation/enhancement
        enhanced_action = self._enhance_action_with_supervision(action, context, game_state)
        
        return enhanced_action
    
    def conduct_realtime_meeting(self, agents: List, reporter_id: int, meeting_reason: str) -> MeetingResult:
        """Conduct a meeting where agents can vote at any time during discussion"""
        print(f"\n=== REAL-TIME MEETING STARTED ===")
        print(f"Reason: {meeting_reason}")
        print(f"Participants: {[a.data.name for a in agents]}")
        
        dialogue_history = []
        current_votes = []  # Track votes as they come in
        step_count = 0
        max_steps = 15
        
        # Phase 1: Reporter's initial statement
        print(f"\n--- INITIAL REPORT ---")
        reporter = next((a for a in agents if a.data.id == reporter_id), None)
        if reporter:
            context = {
                'meeting_reason': meeting_reason,
                'alive_count': len(agents),
                'is_reporter': True
            }
            statement_content = reporter.generate_statement(context, [], False)
            statement = Statement(
                agent_id=reporter.data.id,
                agent_name=reporter.data.name,
                content=statement_content,
                step_number=step_count,
                is_follow_up=False
            )
            dialogue_history.append(statement)
            print(f"  {reporter.data.name}: {statement_content}")
            step_count += 1
        
        # Phase 2: Real-time discussion and voting
        print(f"\n--- REAL-TIME DISCUSSION & VOTING ---")
        
        while step_count < max_steps:
            # Check if everyone has voted
            voted_agents = {vote.voter_id for vote in current_votes}
            if len(voted_agents) >= len(agents):
                print(f"\n  All agents have voted. Proceeding to results...")
                break
            
            # Select agents who can still participate
            available_agents = [a for a in agents if a.data.id not in voted_agents or 
                              any(a.data.name.lower() in s.content.lower() for s in dialogue_history[-3:])]
            
            if not available_agents:
                print(f"\n  No more agents can participate. Proceeding to results...")
                break
            
            # Each available agent decides: speak or vote?
            random.shuffle(available_agents)
            
            for agent in available_agents[:3]:  # Limit to 3 agents per step
                if step_count >= max_steps:
                    break
                
                # Agent decides action based on current context
                action_type = agent.decide_action(dialogue_history, current_votes, [a.data for a in agents])
                
                if action_type == "vote":
                    # Agent votes
                    target_id, reasoning = agent.vote_in_meeting(
                        {'meeting_reason': meeting_reason, 'alive_count': len(agents)},
                        dialogue_history,
                        [a.data for a in agents]
                    )
                    
                    target_name = "Skip"
                    if target_id is not None:
                        target_agent = next((a for a in agents if a.data.id == target_id), None)
                        if target_agent:
                            target_name = target_agent.data.name
                    
                    vote = type('Vote', (), {
                        'voter_id': agent.data.id,
                        'voter_name': agent.data.name,
                        'target_id': target_id,
                        'target_name': target_name,
                        'vote_time': step_count
                    })()
                    
                    current_votes.append(vote)
                    print(f"  {agent.data.name} votes for: {target_name} - {reasoning}")
                    
                    # Add vote to conversation history as well
                    vote_statement = Statement(
                        agent_id=agent.data.id,
                        agent_name=agent.data.name,
                        content=f"VOTES FOR {target_name}: {reasoning}",
                        step_number=step_count,
                        is_follow_up=True
                    )
                    dialogue_history.append(vote_statement)
                    
                elif action_type == "speak":
                    # Agent speaks
                    context = {
                        'meeting_reason': meeting_reason,
                        'alive_count': len(agents),
                        'current_votes': current_votes
                    }
                    statement_content = agent.generate_statement(context, dialogue_history, True)
                    statement = Statement(
                        agent_id=agent.data.id,
                        agent_name=agent.data.name,
                        content=statement_content,
                        step_number=step_count,
                        is_follow_up=True
                    )
                    dialogue_history.append(statement)
                    print(f"  {agent.data.name} (speak): {statement_content}")
                
                step_count += 1
            
            # Show current vote tally
            if current_votes:
                vote_summary = {}
                for vote in current_votes:
                    target = vote.target_name
                    vote_summary[target] = vote_summary.get(target, 0) + 1
                print(f"\n  Current votes: {', '.join([f'{target}: {count}' for target, count in vote_summary.items()])}")
        
        # Phase 3: Ensure everyone votes (if not already)
        print(f"\n--- FINAL VOTING ---")
        voted_agents = {vote.voter_id for vote in current_votes}
        for agent in agents:
            if agent.data.id not in voted_agents:
                target_id, reasoning = agent.vote_in_meeting(
                    {'meeting_reason': meeting_reason, 'alive_count': len(agents)},
                    dialogue_history,
                    [a.data for a in agents]
                )
                
                target_name = "Skip"
                if target_id is not None:
                    target_agent = next((a for a in agents if a.data.id == target_id), None)
                    if target_agent:
                        target_name = target_agent.data.name
                
                vote = type('Vote', (), {
                    'voter_id': agent.data.id,
                    'voter_name': agent.data.name,
                    'target_id': target_id,
                    'target_name': target_name,
                    'vote_time': step_count
                })()
                
                current_votes.append(vote)
                print(f"  {agent.data.name} votes for: {target_name} - {reasoning}")
        
        # Phase 4: Process Results
        print(f"\n--- PROCESSING RESULTS ---")
        meeting_result = self._process_realtime_voting_results(agents, current_votes, dialogue_history)
        
        # Phase 5: Impostor Kill (if applicable)
        if meeting_result.game_continues and not meeting_result.is_imposter_ejected:
            print(f"\n--- IMPOSTOR KILL ---")
            meeting_result = self._conduct_imposter_kill_phase(agents, meeting_result)
        
        print(f"\n=== MEETING CONCLUDED ===")
        print(f"Total dialogue exchanges: {len(dialogue_history)}")
        print(f"Ejected: {meeting_result.ejected_agent_name or 'None'}")
        print(f"Game continues: {meeting_result.game_continues}")
        
        return meeting_result
    
    def _conduct_initial_statements(self, agents: List, reporter_id: int, meeting_reason: str, step_count: int) -> List[Statement]:
        """Phase 1: Each agent gives an initial statement"""
        statements = []
        
        # Reporter speaks first
        reporter = next((a for a in agents if a.data.id == reporter_id), None)
        if reporter:
            context = {
                'meeting_reason': meeting_reason,
                'alive_count': len(agents),
                'is_reporter': True
            }
            statement_content = reporter.generate_statement(context, [], False)
            statement = Statement(
                agent_id=reporter.data.id,
                agent_name=reporter.data.name,
                content=statement_content,
                step_number=step_count,
                is_follow_up=False
            )
            statements.append(statement)
            print(f"  {reporter.data.name}: {statement_content}")
        
        # All other agents speak in random order
        other_agents = [a for a in agents if a.data.id != reporter_id]
        random.shuffle(other_agents)
        
        for i, agent in enumerate(other_agents):
            context = {
                'meeting_reason': meeting_reason,
                'alive_count': len(agents),
                'is_reporter': False
            }
            statement_content = agent.generate_statement(context, statements, False)
            statement = Statement(
                agent_id=agent.data.id,
                agent_name=agent.data.name,
                content=statement_content,
                step_number=step_count + i + 1,
                is_follow_up=False
            )
            statements.append(statement)
            print(f"  {agent.data.name}: {statement_content}")
        
        return statements
    
    def _conduct_follow_up_phase(self, agents: List, dialogue_history: List[Statement], step_count: int, max_steps: int) -> List[Statement]:
        """Phase 2: Follow-up discussion with raise hand mechanic"""
        follow_up_statements = []
        current_step = step_count
        
        while current_step < max_steps:
            # Ask all agents if they want to raise their hand
            speakers = []
            for agent in agents:
                if agent.should_raise_hand(dialogue_history + follow_up_statements):
                    speakers.append(agent)
            
            if not speakers:
                print("  No one raised their hand. Moving to voting.")
                break
            
            # Limit speakers per round
            if len(speakers) > 3:
                speakers = random.sample(speakers, 3)
            
            # Let selected agents speak
            for agent in speakers:
                if current_step >= max_steps:
                    break
                
                context = {
                    'meeting_reason': 'Follow-up discussion',
                    'alive_count': len(agents)
                }
                statement_content = agent.generate_statement(context, dialogue_history + follow_up_statements, True)
                statement = Statement(
                    agent_id=agent.data.id,
                    agent_name=agent.data.name,
                    content=statement_content,
                    step_number=current_step,
                    is_follow_up=True
                )
                follow_up_statements.append(statement)
                print(f"  {agent.data.name} (follow-up): {statement_content}")
                current_step += 1
            
            # Prevent infinite loops
            if len(follow_up_statements) > 15:
                print("  Maximum follow-up statements reached. Moving to voting.")
                break
        
        return follow_up_statements
    
    def _conduct_voting_phase(self, agents: List, dialogue_history: List[Statement]) -> List[tuple]:
        """Phase 3: Voting phase"""
        votes = []
        alive_agent_data = [a.data for a in agents]
        
        for agent in agents:
            context = {
                'meeting_reason': 'Voting phase',
                'alive_count': len(agents)
            }
            target_id, reasoning = agent.vote_in_meeting(context, dialogue_history, alive_agent_data)
            votes.append((agent.data.id, target_id, reasoning))
            
            target_name = "Skip" if target_id is None else next((a.data.name for a in agents if a.data.id == target_id), "Unknown")
            print(f"  {agent.data.name} votes for: {target_name} - {reasoning}")
        
        return votes
    
    def _process_voting_results(self, agents: List, votes: List[tuple], dialogue_history: List[Statement]) -> MeetingResult:
        """Phase 4: Process voting results and determine elimination"""
        # Count votes
        vote_counts = {}
        for voter_id, target_id, reasoning in votes:
            if target_id is not None:  # Skip votes don't count
                vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
        
        # Handle skip votes
        skip_count = sum(1 for _, target_id, _ in votes if target_id is None)
        if skip_count > 0:
            vote_counts[-1] = skip_count  # -1 represents skip votes
        
        print(f"  Vote tally: {vote_counts}")
        
        # Determine elimination
        ejected_agent_id = None
        ejected_agent_name = None
        is_imposter_ejected = False
        
        if vote_counts and max(vote_counts.values()) > len(agents) // 2:
            # Someone has majority
            ejected_agent_id = max(vote_counts.keys(), key=lambda x: vote_counts.get(x, 0))
            if ejected_agent_id != -1:  # Not a skip vote
                ejected_agent = next((a for a in agents if a.data.id == ejected_agent_id), None)
                if ejected_agent:
                    ejected_agent_name = ejected_agent.data.name
                    is_imposter_ejected = ejected_agent.data.is_impostor
                    print(f"  {ejected_agent_name} is ejected with {vote_counts[ejected_agent_id]} votes!")
                    if is_imposter_ejected:
                        print(f"  {ejected_agent_name} was the impostor!")
                    else:
                        print(f"  {ejected_agent_name} was innocent.")
        else:
            print("  No majority reached. No one is ejected.")
        
        # Determine if game continues
        game_continues = True
        if is_imposter_ejected:
            game_continues = False  # Crewmates win
        elif ejected_agent_id is not None and ejected_agent_id != -1:
            # Check remaining players
            remaining_crewmates = len([a for a in agents if not a.data.is_impostor and a.data.id != ejected_agent_id])
            if remaining_crewmates <= 1:
                game_continues = False  # Impostor wins
        
        return MeetingResult(
            ejected_agent_id=ejected_agent_id if ejected_agent_id != -1 else None,
            ejected_agent_name=ejected_agent_name,
            vote_counts=vote_counts,
            is_imposter_ejected=is_imposter_ejected,
            game_continues=game_continues,
            dialogue_history=dialogue_history
        )
    
    def _conduct_imposter_kill_phase(self, agents: List, meeting_result: MeetingResult) -> MeetingResult:
        """Phase 5: Impostor selects next kill target"""
        impostor = next((a for a in agents if a.data.is_impostor), None)
        if not impostor:
            return meeting_result
        
        alive_agent_data = [a.data for a in agents if a.data.is_alive and a.data.id != meeting_result.ejected_agent_id]
        context = {
            'meeting_reason': 'Post-meeting kill phase',
            'alive_count': len(alive_agent_data)
        }
        
        kill_target_id = impostor.select_kill_target(context, alive_agent_data)
        if kill_target_id:
            target_name = next((a.data.name for a in agents if a.data.id == kill_target_id), "Unknown")
            print(f"  Impostor selects {target_name} as next kill target.")
            meeting_result.next_kill_target = kill_target_id
            
            # Check if this would end the game
            remaining_crewmates = len([a for a in alive_agent_data if not a.is_impostor and a.id != kill_target_id])
            if remaining_crewmates <= 1:
                meeting_result.game_continues = False
        
        return meeting_result
    
    def _process_realtime_voting_results(self, agents: List, current_votes: List, dialogue_history: List[Statement]) -> MeetingResult:
        """Process voting results from real-time voting"""
        # Count votes
        vote_counts = {}
        for vote in current_votes:
            target_id = vote.target_id if vote.target_id is not None else -1  # -1 for skip
            vote_counts[target_id] = vote_counts.get(target_id, 0) + 1
        
        print(f"  Vote tally: {vote_counts}")
        
        # Find the agent with the most votes
        if not vote_counts:
            # No votes cast (shouldn't happen with real-time voting)
            return MeetingResult(
                ejected_agent_id=None,
                ejected_agent_name=None,
                is_imposter_ejected=False,
                game_continues=True,
                dialogue_history=dialogue_history,
                vote_counts=vote_counts
            )
        
        # Get the target with the most votes
        max_votes = max(vote_counts.values())
        targets_with_max_votes = [target_id for target_id, count in vote_counts.items() if count == max_votes]
        
        # Check for majority (more than half of voters)
        total_voters = len(current_votes)
        majority_threshold = total_voters // 2 + 1
        
        if max_votes >= majority_threshold and len(targets_with_max_votes) == 1:
            # Clear majority for one target
            ejected_id = targets_with_max_votes[0]
            
            if ejected_id == -1:  # Skip vote won
                print(f"  Majority voted to skip. No one is ejected.")
                return MeetingResult(
                    ejected_agent_id=None,
                    ejected_agent_name=None,
                    is_imposter_ejected=False,
                    game_continues=True,
                    dialogue_history=dialogue_history,
                    vote_counts=vote_counts
                )
            else:
                # Someone is ejected
                ejected_agent = next((a for a in agents if a.data.id == ejected_id), None)
                if ejected_agent:
                    is_imposter = ejected_agent.data.is_impostor
                    print(f"  {ejected_agent.data.name} is ejected! {'They were the impostor!' if is_imposter else 'They were innocent.'}")
                    
                    return MeetingResult(
                        ejected_agent_id=ejected_id,
                        ejected_agent_name=ejected_agent.data.name,
                        is_imposter_ejected=is_imposter,
                        game_continues=not is_imposter,  # Game ends if impostor ejected
                        dialogue_history=dialogue_history,
                        vote_counts=vote_counts
                    )
        
        # No majority reached
        print(f"  No majority reached. No one is ejected.")
        return MeetingResult(
            ejected_agent_id=None,
            ejected_agent_name=None,
            is_imposter_ejected=False,
            game_continues=True,
            dialogue_history=dialogue_history,
            vote_counts=vote_counts
        )
    
    def _build_context_string(self, context: Dict, game_state: GameState) -> str:
        """Build a comprehensive context string from the context dictionary"""
        base_info = f"EMERGENCY MEETING! {context['meeting_reason']}. Step {context['step_number']}/{context['max_steps']}."
        
        alive_count = len(context['alive_agents'])
        base_info += f" {alive_count} players alive. There is 1 impostor among you!"
        
        # Add role-specific context
        if context['role_type'] == 'impostor':
            if context.get('suspicion_level') == 'high':
                base_info += " [You're under suspicion - be defensive but not too obvious]"
            if context.get('scapegoat_opportunities'):
                scapegoats = ', '.join(context['scapegoat_opportunities'])
                base_info += f" [Others are already suspicious of: {scapegoats}]"
        else:  # crewmate
            if context.get('suspicious_behaviors'):
                suspicious = ', '.join(context['suspicious_behaviors'].keys())
                base_info += f" [Suspicious behaviors noticed from: {suspicious}]"
            if context.get('deduction_hints'):
                hints = '; '.join(context['deduction_hints'])
                base_info += f" [Hints: {hints}]"
        
        return base_info
    
    def _enhance_action_with_supervision(self, action: AgentAction, context: Dict, game_state: GameState) -> AgentAction:
        """Enhance or validate the action based on supervisor logic"""
        # Add supervisor enhancements here if needed
        # For now, return the action as-is, but this could include:
        # - Preventing duplicate votes
        # - Encouraging more strategic thinking
        # - Balancing discussion vs voting actions
        
        # Prevent voting for dead agents
        if action.action_type == ActionType.VOTE and action.target_agent_id:
            target_agent = next((a for a in game_state.agents if a.id == action.target_agent_id), None)
            if target_agent and not target_agent.is_alive:
                # Convert to a speak action instead
                action = AgentAction(
                    agent_id=action.agent_id,
                    action_type=ActionType.SPEAK,
                    content=f"I wanted to vote for {target_agent.name} but they're already eliminated!",
                    target_agent_id=None
                )
        
        return action