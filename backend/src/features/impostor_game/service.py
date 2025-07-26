import random
import uuid
from typing import List, Dict, Optional
from src.core.llm_client import LLMClient
from .schema import (
    GameState, Agent, AgentAction, ActionType, GamePhase, GameStatus, MeetingPhase,
    InitGameResponse, StepResponse, GameStateResponse, MeetingTrigger, Statement, Vote, MeetingResult,
    AgentTurn, ConversationEntry
)
from .agents import Crewmate, Impostor, SupervisorAgent

class ImpostorGameService:
    def __init__(self, llm_client: Optional[LLMClient] = None):
        self.games: Dict[str, GameState] = {}
        self.llm_client = llm_client or LLMClient()
        self.supervisor = SupervisorAgent(self.llm_client)
    
    def _create_agent(self, agent_data: Agent):
        """Create appropriate agent type based on role"""
        if agent_data.is_impostor:
            return Impostor(agent_data, self.llm_client)
        else:
            return Crewmate(agent_data, self.llm_client)
    
    def create_game(self) -> InitGameResponse:
        game_id = str(uuid.uuid4())
        
        # Among Us style names and colors - 8 total players (7 crewmates + 1 impostor)
        crewmates_data = [
            ("Red", "red"), ("Blue", "blue"), ("Green", "green"), ("Pink", "pink"),
            ("Orange", "orange"), ("Yellow", "yellow"), ("Black", "black"), ("White", "white")
        ]
        agents = []
        
        # Create 8 agents, all initially as crewmates
        for i, (name, color) in enumerate(crewmates_data):
            agents.append(Agent(id=i, name=name, color=color, is_impostor=False))
        
        # Randomly select 1 impostor from the 8 players (leaving 7 crewmates)
        impostor_id = random.randint(0, 7)
        agents[impostor_id].is_impostor = True
        
        # Choose random meeting trigger and reporter
        meeting_trigger = random.choice([MeetingTrigger.DEAD_BODY, MeetingTrigger.EMERGENCY_BUTTON])
        reporter_id = random.randint(0, 7)
        
        if meeting_trigger == MeetingTrigger.DEAD_BODY:
            dead_colors = ["Purple", "Brown", "Cyan", "Lime"]  # Colors not in game
            dead_color = random.choice(dead_colors)
            meeting_reason = f"{agents[reporter_id].name} found {dead_color}'s body in {'Electrical' if random.random() > 0.5 else 'Medbay'}"
        else:
            meeting_reason = f"{agents[reporter_id].name} pressed the emergency button"
        
        game_state = GameState(
            game_id=game_id,
            status=GameStatus.ACTIVE,
            phase=GamePhase.MEETING,
            meeting_phase=MeetingPhase.INITIAL_STATEMENTS,
            step_number=0,
            agents=agents,
            action_history=[],
            dialogue_history=[],
            impostor_id=impostor_id,
            meeting_trigger=meeting_trigger,
            reporter_id=reporter_id,
            meeting_reason=meeting_reason
        )
        
        self.games[game_id] = game_state
        
        # Count final composition for verification
        crewmate_count = sum(1 for a in agents if not a.is_impostor)
        impostor_count = sum(1 for a in agents if a.is_impostor)
        
        return InitGameResponse(
            game_id=game_id,
            message=f"EMERGENCY MEETING! {meeting_reason} | Players: {crewmate_count} Crewmates + {impostor_count} Impostor",
            agents=agents,
            impostor_revealed=f"The impostor is: {agents[impostor_id].name} ({agents[impostor_id].color}) | Game has {crewmate_count} crewmates and {impostor_count} impostor",
            meeting_trigger=meeting_trigger,
            reporter_name=agents[reporter_id].name,
            meeting_reason=meeting_reason
        )
    
    def get_game(self, game_id: str) -> Optional[GameState]:
        return self.games.get(game_id)
    
    def get_game_state_response(self, game_id: str) -> Optional[GameStateResponse]:
        game = self.get_game(game_id)
        if not game:
            return None
        
        alive_agents = [a for a in game.agents if a.is_alive]
        # Convert current votes to string keys
        current_votes_str = {str(k): v for k, v in game.current_votes.items()}
        
        return GameStateResponse(
            game_id=game.game_id,
            status=game.status,
            phase=game.phase,
            meeting_phase=game.meeting_phase,
            step_number=game.step_number,
            max_steps=game.max_steps,
            agents=game.agents,
            action_history=game.action_history,
            dialogue_history=game.dialogue_history,
            current_votes=current_votes_str,
            winner=game.winner,
            alive_count=len(alive_agents),
            impostor_alive=any(a.is_impostor for a in alive_agents),
            meeting_result=game.meeting_result
        )
    
    def _get_alive_agents(self, game: GameState) -> List[Agent]:
        return [agent for agent in game.agents if agent.is_alive]
    
    def step_game(self, game_id: str) -> Optional[StepResponse]:
        game = self.get_game(game_id)
        if not game:
            return None
        
        if game.status == GameStatus.FINISHED:
            return StepResponse(
                game_id=game_id,
                phase=game.phase,
                meeting_phase=game.meeting_phase,
                step_number=game.step_number,
                max_steps=game.max_steps,
                actions=[],
                winner=game.winner,
                game_over=True,
                message="Game over"
            )
        
        # Use SupervisorAgent to conduct the full round table meeting
        alive_agents = [a for a in game.agents if a.is_alive]
        
        # Create agent instances for the meeting
        agent_instances = []
        for agent_data in alive_agents:
            if agent_data.is_impostor:
                agent_instances.append(Impostor(agent_data, self.llm_client))
            else:
                agent_instances.append(Crewmate(agent_data, self.llm_client))
        
        # Conduct the full meeting using SupervisorAgent
        meeting_result = self.supervisor.conduct_full_meeting(
            agent_instances, 
            game.reporter_id, 
            game.meeting_reason
        )
        
        # Update game state with meeting results
        game.meeting_result = meeting_result
        game.dialogue_history = meeting_result.dialogue_history
        
        # Handle elimination if someone was ejected
        eliminated_name = None
        if meeting_result.ejected_agent_id is not None:
            for agent in game.agents:
                if agent.id == meeting_result.ejected_agent_id:
                    agent.is_alive = False
                    eliminated_name = agent.name
                    break
        
        # Handle impostor kill if game continues and impostor wasn't ejected
        if meeting_result.game_continues and not meeting_result.is_imposter_ejected and meeting_result.next_kill_target:
            for agent in game.agents:
                if agent.id == meeting_result.next_kill_target:
                    agent.is_alive = False
                    break
        
        # Check win conditions
        alive_agents_after = [a for a in game.agents if a.is_alive]
        impostor_alive = any(a.is_impostor for a in alive_agents_after)
        crewmates_alive = len([a for a in alive_agents_after if not a.is_impostor])
        
        game_over = False
        winner = None
        message = ""
        
        if not impostor_alive:
            # Crewmates win - impostor eliminated
            game_over = True
            winner = "Crewmates"
            message = "Crewmates win! The impostor has been eliminated."
        elif crewmates_alive <= 1:
            # Impostor wins - equal or outnumbers crewmates
            game_over = True
            winner = "Impostor"
            message = "Impostor wins! The crew has been eliminated."
        elif not meeting_result.game_continues:
            # Game ended for other reasons
            game_over = True
            winner = "Draw"
            message = "Game ended in a draw."
        else:
            message = f"Meeting concluded. {len(alive_agents_after)} players remain alive."
        
        if game_over:
            game.status = GameStatus.FINISHED
            game.phase = GamePhase.GAME_OVER
            game.winner = winner
        
        game.step_number += 1
        
        # Create turns for each agent
        turns = []
        for agent_data in alive_agents:
            agent_turn = AgentTurn(
                agent_id=agent_data.id,
                think=None,  # Will be populated with agent thoughts
                speak=None,  # Will be populated with agent speech
                vote=None    # Will be populated with agent votes
            )
            
            # Find agent's statements in dialogue history
            agent_statements = [s for s in meeting_result.dialogue_history if s.agent_id == agent_data.id]
            if agent_statements:
                # Use the first statement as the main speech
                agent_turn.speak = agent_statements[0].content
                agent_turn.think = f"I need to participate in this emergency meeting about {game.meeting_reason}"
            
            # Find agent's vote if any
            if hasattr(meeting_result, 'vote_counts') and meeting_result.vote_counts:
                # This is a simplified vote representation
                agent_turn.vote = None  # Will be set if agent voted
            
            turns.append(agent_turn)
        
        # Create conversation history from dialogue
        conversation_history = []
        for statement in meeting_result.dialogue_history:
            conversation_entry = ConversationEntry(
                agent_id=statement.agent_id,
                action_type="speak",
                content=statement.content,
                target_agent_id=None
            )
            conversation_history.append(conversation_entry)
        
        # Determine phase string
        phase_str = "active"
        if game_over:
            phase_str = "ended"
        elif game.meeting_phase == MeetingPhase.VOTING:
            phase_str = "voting"
        
        return StepResponse(
            game_id=game_id,
            phase=phase_str,
            step_number=game.step_number,
            max_steps=game.max_steps,
            turns=turns,
            conversation_history=conversation_history,
            eliminated=eliminated_name,
            winner=winner,
            game_over=game_over,
            message=message
        )