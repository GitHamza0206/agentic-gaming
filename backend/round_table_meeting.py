#!/usr/bin/env python3
"""
Enhanced Round Table Meeting System for Among Us AI Game
完整的圆桌会议系统实现
"""

from typing import List, Dict, Optional, Tuple
from enum import Enum
import random
from dataclasses import dataclass

class MeetingPhase(str, Enum):
    INITIAL_STATEMENTS = "initial_statements"
    FOLLOW_UP = "follow_up"
    VOTING = "voting"
    RESULTS = "results"
    IMPOSTER_KILL = "imposter_kill"
    GAME_END = "game_end"

class VoteResult(str, Enum):
    SKIP = "skip"
    EJECTED = "ejected"
    TIE = "tie"

@dataclass
class Statement:
    agent_id: int
    agent_name: str
    content: str
    step_number: int
    is_follow_up: bool = False

@dataclass
class Vote:
    voter_id: int
    voter_name: str
    target_id: Optional[int]
    target_name: Optional[str]
    reasoning: str

@dataclass
class MeetingResult:
    ejected_agent_id: Optional[int]
    ejected_agent_name: Optional[str]
    vote_counts: Dict[int, int]
    is_imposter_ejected: bool
    game_continues: bool
    next_kill_target: Optional[int] = None

class BaseAgent:
    """Base class for all agents in the game"""
    
    def __init__(self, agent_id: int, name: str, is_imposter: bool = False, is_alive: bool = True):
        self.agent_id = agent_id
        self.name = name
        self.is_imposter = is_imposter
        self.is_alive = is_alive
    
    def generate_statement(self, context: Dict, dialogue_history: List[Statement], is_follow_up: bool = False) -> str:
        """Generate a statement based on context and dialogue history"""
        # Placeholder implementation
        if is_follow_up:
            return f"[{self.name}] Follow-up: I want to add something to my previous statement..."
        else:
            return f"[{self.name}] Initial: Based on what I know, here's my analysis..."
    
    def should_raise_hand(self, dialogue_history: List[Statement]) -> bool:
        """Decide whether to raise hand for follow-up statement"""
        # Placeholder implementation - random chance with some logic
        if self.is_imposter:
            # Impostors might be more strategic about when to speak
            return random.random() < 0.3
        else:
            # Crewmates might speak up if they have suspicions
            return random.random() < 0.4
    
    def vote(self, context: Dict, dialogue_history: List[Statement], alive_agents: List['BaseAgent']) -> Tuple[Optional[int], str]:
        """Vote for a target agent or skip"""
        # Placeholder implementation
        voteable_agents = [a for a in alive_agents if a.agent_id != self.agent_id]
        if voteable_agents and random.random() > 0.2:  # 80% chance to vote
            target = random.choice(voteable_agents)
            return target.agent_id, f"I vote for {target.name} because they seem suspicious."
        else:
            return None, "I skip this vote, need more information."
    
    def select_kill_target(self, context: Dict, alive_agents: List['BaseAgent']) -> Optional[int]:
        """Select next kill target (only for impostors)"""
        if not self.is_imposter:
            return None
        
        # Placeholder implementation
        potential_targets = [a for a in alive_agents if not a.is_imposter and a.is_alive]
        if potential_targets:
            target = random.choice(potential_targets)
            return target.agent_id
        return None

class GameMasterAgent:
    """Provides game context and manages overall game state"""
    
    def __init__(self):
        self.game_context = {}
    
    def get_game_context(self, agents: List[BaseAgent], reporter_id: int, meeting_reason: str) -> Dict:
        """Provide comprehensive game context for the meeting"""
        alive_agents = [a for a in agents if a.is_alive]
        
        return {
            "total_agents": len(agents),
            "alive_agents": alive_agents,
            "alive_count": len(alive_agents),
            "reporter_id": reporter_id,
            "meeting_reason": meeting_reason,
            "imposter_count": sum(1 for a in alive_agents if a.is_imposter),
            "crewmate_count": sum(1 for a in alive_agents if not a.is_imposter)
        }

class SupervisorAgent:
    """Enhanced supervisor that manages the complete round table meeting"""
    
    def __init__(self, game_master: GameMasterAgent):
        self.game_master = game_master
        self.step_count = 0
        self.max_steps = 30
        self.current_phase = MeetingPhase.INITIAL_STATEMENTS
        self.dialogue_history: List[Statement] = []
        self.votes: List[Vote] = []
        
    def conduct_full_meeting(self, agents: List[BaseAgent], reporter_id: int, meeting_reason: str) -> MeetingResult:
        """Conduct a complete round table meeting from start to finish"""
        print(f"🎯 EMERGENCY MEETING STARTED!")
        print(f"📢 Reason: {meeting_reason}")
        print(f"👥 Alive players: {', '.join(a.name for a in agents if a.is_alive)}")
        print("=" * 60)
        
        # Reset meeting state
        self.step_count = 0
        self.dialogue_history = []
        self.votes = []
        self.current_phase = MeetingPhase.INITIAL_STATEMENTS
        
        # Get game context
        context = self.game_master.get_game_context(agents, reporter_id, meeting_reason)
        alive_agents = [a for a in agents if a.is_alive]
        
        # Phase 1: Initial Statements
        self._conduct_initial_statements(alive_agents, reporter_id, context)
        
        # Phase 2: Follow-up Phase (if steps remaining)
        if self.step_count < self.max_steps:
            self._conduct_follow_up_phase(alive_agents, context)
        
        # Phase 3: Voting Phase
        self.current_phase = MeetingPhase.VOTING
        self._conduct_voting_phase(alive_agents, context)
        
        # Phase 4: Process Results
        meeting_result = self._process_voting_results(agents)
        
        # Phase 5: Imposter Kill Phase (if game continues)
        if meeting_result.game_continues and not meeting_result.is_imposter_ejected:
            self._conduct_imposter_kill_phase(agents, context, meeting_result)
        
        return meeting_result
    
    def _conduct_initial_statements(self, alive_agents: List[BaseAgent], reporter_id: int, context: Dict):
        """Phase 1: All agents give their initial statements"""
        print(f"\n🗣️  PHASE 1: INITIAL STATEMENTS")
        print("-" * 40)
        
        # Reporter speaks first
        reporter = next(a for a in alive_agents if a.agent_id == reporter_id)
        self._agent_speak(reporter, context, is_follow_up=False)
        
        # Other agents speak in randomized order
        other_agents = [a for a in alive_agents if a.agent_id != reporter_id]
        random.shuffle(other_agents)
        
        for agent in other_agents:
            if self.step_count >= self.max_steps:
                print(f"⏰ Step limit reached! Ending initial statements.")
                break
            self._agent_speak(agent, context, is_follow_up=False)
    
    def _conduct_follow_up_phase(self, alive_agents: List[BaseAgent], context: Dict):
        """Phase 2: Follow-up statements for agents who raise their hand"""
        print(f"\n✋ PHASE 2: FOLLOW-UP STATEMENTS")
        print("-" * 40)
        
        follow_up_rounds = 0
        max_follow_up_rounds = 3  # Prevent infinite loops
        
        while follow_up_rounds < max_follow_up_rounds and self.step_count < self.max_steps:
            # Check who wants to raise their hand
            agents_raising_hand = []
            for agent in alive_agents:
                if agent.should_raise_hand(self.dialogue_history):
                    agents_raising_hand.append(agent)
            
            if not agents_raising_hand:
                print("👥 No agents raised their hand. Moving to voting phase.")
                break
            
            print(f"✋ Round {follow_up_rounds + 1}: {len(agents_raising_hand)} agents raised their hand")
            
            # Randomize order of follow-up speakers
            random.shuffle(agents_raising_hand)
            
            for agent in agents_raising_hand:
                if self.step_count >= self.max_steps:
                    print(f"⏰ Step limit reached! Ending follow-up phase.")
                    return
                self._agent_speak(agent, context, is_follow_up=True)
            
            follow_up_rounds += 1
        
        if follow_up_rounds >= max_follow_up_rounds:
            print(f"🔄 Maximum follow-up rounds reached. Moving to voting.")
    
    def _conduct_voting_phase(self, alive_agents: List[BaseAgent], context: Dict):
        """Phase 3: All agents vote"""
        print(f"\n🗳️  PHASE 3: VOTING")
        print("-" * 40)
        
        self.votes = []
        
        # Randomize voting order
        voting_order = alive_agents.copy()
        random.shuffle(voting_order)
        
        for agent in voting_order:
            target_id, reasoning = agent.vote(context, self.dialogue_history, alive_agents)
            
            target_name = None
            if target_id is not None:
                target_agent = next((a for a in alive_agents if a.agent_id == target_id), None)
                target_name = target_agent.name if target_agent else f"Agent{target_id}"
            
            vote = Vote(
                voter_id=agent.agent_id,
                voter_name=agent.name,
                target_id=target_id,
                target_name=target_name,
                reasoning=reasoning
            )
            
            self.votes.append(vote)
            
            if target_name:
                print(f"🗳️  {agent.name} votes for {target_name}: {reasoning}")
            else:
                print(f"⏭️  {agent.name} skips: {reasoning}")
    
    def _process_voting_results(self, all_agents: List[BaseAgent]) -> MeetingResult:
        """Phase 4: Process voting results and determine ejection"""
        print(f"\n📊 PHASE 4: VOTING RESULTS")
        print("-" * 40)
        
        # Count votes
        vote_counts = {}
        skip_count = 0
        
        for vote in self.votes:
            if vote.target_id is not None:
                vote_counts[vote.target_id] = vote_counts.get(vote.target_id, 0) + 1
            else:
                skip_count += 1
        
        print(f"📊 Vote Distribution:")
        for agent_id, count in vote_counts.items():
            agent_name = next(a.name for a in all_agents if a.agent_id == agent_id)
            print(f"   {agent_name}: {count} votes")
        if skip_count > 0:
            print(f"   Skip: {skip_count} votes")
        
        # Determine result
        if not vote_counts:
            print(f"⏭️  No votes cast. No one ejected.")
            return MeetingResult(
                ejected_agent_id=None,
                ejected_agent_name=None,
                vote_counts=vote_counts,
                is_imposter_ejected=False,
                game_continues=True
            )
        
        max_votes = max(vote_counts.values())
        agents_with_max_votes = [agent_id for agent_id, votes in vote_counts.items() if votes == max_votes]
        
        if len(agents_with_max_votes) > 1:
            print(f"🤝 Tie vote! No one ejected.")
            return MeetingResult(
                ejected_agent_id=None,
                ejected_agent_name=None,
                vote_counts=vote_counts,
                is_imposter_ejected=False,
                game_continues=True
            )
        
        # Someone is ejected
        ejected_id = agents_with_max_votes[0]
        ejected_agent = next(a for a in all_agents if a.agent_id == ejected_id)
        ejected_agent.is_alive = False
        
        is_imposter_ejected = ejected_agent.is_imposter
        
        print(f"❌ {ejected_agent.name} was ejected with {max_votes} votes!")
        if is_imposter_ejected:
            print(f"🎉 {ejected_agent.name} was the Imposter! Crewmates win!")
        else:
            print(f"😔 {ejected_agent.name} was not the Imposter.")
        
        # Check win conditions
        alive_agents = [a for a in all_agents if a.is_alive]
        alive_impostors = [a for a in alive_agents if a.is_imposter]
        alive_crewmates = [a for a in alive_agents if not a.is_imposter]
        
        game_continues = True
        if is_imposter_ejected or len(alive_impostors) == 0:
            print(f"🏆 CREWMATES WIN! All impostors eliminated.")
            game_continues = False
        elif len(alive_impostors) >= len(alive_crewmates):
            print(f"🏆 IMPOSTORS WIN! They equal or outnumber crewmates.")
            game_continues = False
        
        return MeetingResult(
            ejected_agent_id=ejected_id,
            ejected_agent_name=ejected_agent.name,
            vote_counts=vote_counts,
            is_imposter_ejected=is_imposter_ejected,
            game_continues=game_continues
        )
    
    def _conduct_imposter_kill_phase(self, all_agents: List[BaseAgent], context: Dict, meeting_result: MeetingResult):
        """Phase 5: Imposter selects next kill target"""
        print(f"\n🔪 PHASE 5: IMPOSTER KILL SELECTION")
        print("-" * 40)
        
        alive_agents = [a for a in all_agents if a.is_alive]
        alive_impostors = [a for a in alive_agents if a.is_imposter]
        
        if not alive_impostors:
            return
        
        # For simplicity, use the first alive impostor
        imposter = alive_impostors[0]
        kill_target_id = imposter.select_kill_target(context, alive_agents)
        
        if kill_target_id is not None:
            target_agent = next((a for a in alive_agents if a.agent_id == kill_target_id), None)
            if target_agent and not target_agent.is_imposter:
                target_agent.is_alive = False
                meeting_result.next_kill_target = kill_target_id
                print(f"🔪 {imposter.name} selected {target_agent.name} as the next kill target.")
                
                # Check win condition after kill
                remaining_alive = [a for a in all_agents if a.is_alive]
                remaining_impostors = [a for a in remaining_alive if a.is_imposter]
                remaining_crewmates = [a for a in remaining_alive if not a.is_imposter]
                
                if len(remaining_impostors) >= len(remaining_crewmates):
                    print(f"🏆 IMPOSTORS WIN! They now equal or outnumber crewmates.")
                    meeting_result.game_continues = False
            else:
                print(f"🚫 {imposter.name} could not select a valid kill target.")
        else:
            print(f"🤔 {imposter.name} chose not to kill anyone this round.")
    
    def _agent_speak(self, agent: BaseAgent, context: Dict, is_follow_up: bool = False):
        """Have an agent make a statement"""
        if self.step_count >= self.max_steps:
            return
        
        self.step_count += 1
        statement_content = agent.generate_statement(context, self.dialogue_history, is_follow_up)
        
        statement = Statement(
            agent_id=agent.agent_id,
            agent_name=agent.name,
            content=statement_content,
            step_number=self.step_count,
            is_follow_up=is_follow_up
        )
        
        self.dialogue_history.append(statement)
        
        follow_up_indicator = " (Follow-up)" if is_follow_up else ""
        print(f"Step {self.step_count:2d}: {agent.name}{follow_up_indicator}")
        print(f"        {statement_content}")
        print()

# Example usage and testing
def demo_round_table_meeting():
    """Demonstrate the round table meeting system"""
    print("🎮 Among Us Round Table Meeting Demo")
    print("=" * 60)
    
    # Create agents
    agents = [
        BaseAgent(0, "Red", is_imposter=False),
        BaseAgent(1, "Blue", is_imposter=False),
        BaseAgent(2, "Green", is_imposter=True),  # Imposter
        BaseAgent(3, "Pink", is_imposter=False),
        BaseAgent(4, "Orange", is_imposter=False),
        BaseAgent(5, "Yellow", is_imposter=False),
        BaseAgent(6, "Black", is_imposter=False),
        BaseAgent(7, "White", is_imposter=False),
    ]
    
    # Create game master and supervisor
    game_master = GameMasterAgent()
    supervisor = SupervisorAgent(game_master)
    
    # Conduct meeting
    reporter_id = 4  # Orange reports
    meeting_reason = "Orange found Cyan's body in Electrical"
    
    result = supervisor.conduct_full_meeting(agents, reporter_id, meeting_reason)
    
    print(f"\n🏁 MEETING CONCLUDED")
    print("=" * 60)
    print(f"Game continues: {result.game_continues}")
    if result.ejected_agent_name:
        print(f"Ejected: {result.ejected_agent_name}")
        print(f"Was imposter: {result.is_imposter_ejected}")
    if result.next_kill_target:
        killed_agent = next(a for a in agents if a.agent_id == result.next_kill_target)
        print(f"Next kill: {killed_agent.name}")
    
    print(f"Remaining alive: {', '.join(a.name for a in agents if a.is_alive)}")

if __name__ == "__main__":
    demo_round_table_meeting()
