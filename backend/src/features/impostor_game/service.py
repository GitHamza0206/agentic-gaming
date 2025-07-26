import random
import uuid
import json
import os
from typing import List, Dict, Optional
from src.core.llm_client import LLMClient
from .schema import (
    Agent, GameState, GameStatus, GamePhase, ActionType, AgentAction, AgentTurn, MeetingTrigger,
    InitGameResponse, StepResponse, GameStateResponse, AgentMemory
)
from .agents import Crewmate, Impostor

class ImpostorGameService:
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        self.llm_client = LLMClient()
        self.game_master_data = self._load_game_master_data()
    
    def _load_game_master_data(self) -> List[Dict]:
        """Load game master data from JSON file"""
        try:
            # Get the path to the backend directory more reliably
            current_file = os.path.abspath(__file__)
            # Go up from: backend/src/features/impostor_game/service.py to backend/
            backend_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(current_file))))
            game_master_path = os.path.join(backend_dir, "data", "game-master.json")
            
            print(f"Attempting to load game-master.json from: {game_master_path}")
            print(f"File exists: {os.path.exists(game_master_path)}")
            
            with open(game_master_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading game-master.json: {e}")
            print(f"Current file: {current_file}")
            print(f"Backend dir: {backend_dir}")
            print(f"Game master path: {game_master_path}")
            return []
    
    def _create_agent(self, agent_data: Agent):
        """Create appropriate agent type based on role"""
        if agent_data.is_impostor:
            return Impostor(agent_data, self.llm_client)
        else:
            return Crewmate(agent_data, self.llm_client)
    
    def create_game(self, num_players: int = 4) -> InitGameResponse:
        game_id = str(uuid.uuid4())
        
        if not self.game_master_data:
            raise FileNotFoundError("game-master.json is required but not available. Cannot create game without scenario data.")
        
        # Create agents based on game-master.json initial state
        first_step = self.game_master_data[0]
        agents = []
        impostor_id = None
        
        for color, agent_data in first_step["agents"].items():
            # Check if this agent is the impostor based on actions containing "pretends" or "fake"
            is_impostor = "pretend" in agent_data["action"].lower() or "fake" in agent_data["action"].lower()
            if is_impostor:
                impostor_id = color
            
            agent = Agent(
                id=color,  # Use color as ID
                name=color.capitalize(),
                color=color,
                is_impostor=is_impostor,
                is_alive=True,
                location=agent_data["location"],
                action=agent_data["action"],
                met=agent_data["met"]
            )
            agents.append(agent)
        
        # Determine meeting details from the last step
        meeting_trigger = MeetingTrigger.DEAD_BODY  # Based on the game-master data ending
        
        # Find who discovered the body (red in the last step)
        reporter_id = "red"
        reporter_agent = next((a for a in agents if a.id == reporter_id), agents[0])
        meeting_reason = f"{reporter_agent.name} found Green's body in Electrical"
        
        # Mark Green as dead based on game-master data
        green_agent = next((a for a in agents if a.id == "green"), None)
        if green_agent is not None:
            green_agent.is_alive = False
            green_agent.action = "DEAD"
        
        game_state = GameState(
            game_id=game_id,
            status=GameStatus.ACTIVE,
            phase=GamePhase.ACTIVE,
            step_number=1,
            max_steps=30,
            agents=agents,
            public_action_history=[],
            private_thoughts={},
            impostor_id=impostor_id if impostor_id is not None else "yellow",
            meeting_trigger=meeting_trigger,
            reporter_id=reporter_id,
            meeting_reason=meeting_reason
        )
        
        self.games[game_id] = game_state
        
        return InitGameResponse(
            game_id=game_id,
            message=f"EMERGENCY MEETING! {meeting_reason}",
            agents=agents,
            impostor_revealed=f"The impostor is: {impostor_id}" if impostor_id is not None else "Unknown impostor",
            meeting_trigger=meeting_trigger,
            reporter_name=reporter_agent.name,
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
            step_number=game.step_number,
            max_steps=game.max_steps,
            agents=game.agents,
            public_action_history=game.public_action_history,
            current_votes=current_votes_str,
            winner=game.winner,
            alive_count=len(alive_agents),
            impostor_alive=any(a.is_impostor for a in alive_agents)
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
                step_number=game.step_number,
                max_steps=game.max_steps,
                turns=[],
                conversation_history=game.public_action_history,
                winner=game.winner,
                game_over=True,
                message="Game over"
            )
        
        # Check if max steps reached
        if game.step_number >= game.max_steps:
            alive_agents = self._get_alive_agents(game)
            impostor_alive = any(a.is_impostor for a in alive_agents)
            
            if impostor_alive:
                game.winner = "Imposteur"
                message = "Time's up! The impostor wins!"
            else:
                game.winner = "Crewmates"
                message = "Time's up! The crewmates win!"
            
            game.status = GameStatus.FINISHED
            game.phase = GamePhase.GAME_OVER
            
            return StepResponse(
                game_id=game_id,
                phase=game.phase,
                step_number=game.step_number,
                max_steps=game.max_steps,
                turns=[],
                conversation_history=game.public_action_history,
                winner=game.winner,
                game_over=True,
                message=message
            )
        
        # All alive agents act in this step
        alive_agents = self._get_alive_agents(game)
        step_turns = []
        
        # Generate turns for all alive agents
        context_base = f"EMERGENCY MEETING! {game.meeting_reason}. Step {game.step_number}/{game.max_steps}. Alive crewmates: {len(alive_agents)}."
        if game.step_number == 1:
            context = f"{context_base} There is an impostor among you!"
        else:
            context = f"{context_base} Find the impostor!"
        
        for agent_data in alive_agents:
            agent = self._create_agent(agent_data)
            
            # Get agent's private thoughts
            private_thoughts = game.private_thoughts.get(agent_data.id, [])
            
            # Add special context for reporter in first step
            agent_context = context
            if game.step_number == 1 and agent_data.id == game.reporter_id:
                agent_context = f"{context} You are the one who called this meeting because: {game.meeting_reason}"
            
            turn = agent.choose_action(agent_context, game.public_action_history, private_thoughts, game.step_number, game.agents)
            step_turns.append(turn)
            
            # Save memory update to persistent agent data (if not already added by agent)
            if turn.memory_update and (not agent_data.memory_history or agent_data.memory_history[-1] != turn.memory_update):
                agent_data.memory_history.append(turn.memory_update)
            
            # Process the turn - store think privately
            if agent_data.id not in game.private_thoughts:
                game.private_thoughts[agent_data.id] = []
            game.private_thoughts[agent_data.id].append(AgentAction(
                agent_id=agent_data.id,
                action_type=ActionType.THINK,
                content=turn.think,
                target_agent_id=None
            ))
        
        # After all agents have generated their turns, randomly select one speaker
        agents_who_want_to_speak = [turn for turn in step_turns if turn.speak is not None]
        if agents_who_want_to_speak:
            chosen_speaker = random.choice(agents_who_want_to_speak)
            game.public_action_history.append(AgentAction(
                agent_id=chosen_speaker.agent_id,
                action_type=ActionType.SPEAK,
                content=chosen_speaker.speak,
                target_agent_id=None
            ))
        
        # Now process all votes
        for turn in step_turns:
            if turn.vote is not None:
                # Find the color of the voted agent
                voted_agent = next((a for a in game.agents if a.id == turn.vote), None)
                voted_color = voted_agent.color if voted_agent else f"unknown{turn.vote}"
                
                game.public_action_history.append(AgentAction(
                    agent_id=turn.agent_id,
                    action_type=ActionType.VOTE,
                    content=f"I vote to eliminate {voted_color}",
                    target_agent_id=turn.vote
                ))
                
                # Count the vote
                if turn.vote in game.current_votes:
                    game.current_votes[turn.vote] += 1
                else:
                    game.current_votes[turn.vote] = 1
        
        # Check for elimination (if someone has majority votes)
        total_alive = len(alive_agents)
        majority_needed = (total_alive // 2) + 1
        
        eliminated_agent = None
        for agent_id, votes in game.current_votes.items():
            if votes >= majority_needed:
                eliminated_agent = next((a for a in game.agents if a.id == agent_id), None)
                break
        
        message = f"Step {game.step_number} completed."
        winner = None
        game_over = False
        
        if eliminated_agent:
            eliminated_agent.is_alive = False
            message += f" {eliminated_agent.name} ({eliminated_agent.color}) eliminated with {game.current_votes[eliminated_agent.id]} votes!"
            
            if eliminated_agent.is_impostor:
                game.winner = "Crewmates"
                game.status = GameStatus.FINISHED
                game.phase = GamePhase.GAME_OVER
                winner = "Crewmates"
                game_over = True
                message += " The impostor was found! Crewmates win!"
            else:
                # Check if imposteur can still win
                remaining_alive = self._get_alive_agents(game)
                if len(remaining_alive) <= 2 and any(a.is_impostor for a in remaining_alive):
                    game.winner = "Imposteur"
                    game.status = GameStatus.FINISHED
                    game.phase = GamePhase.GAME_OVER
                    winner = "Imposteur"
                    game_over = True
                    message += " The impostor wins!"
                else:
                    message += f" {eliminated_agent.name} was innocent!"
            
            # Reset votes after elimination
            game.current_votes = {}
        
        # Increment step
        game.step_number += 1
        
        return StepResponse(
            game_id=game_id,
            phase=game.phase,
            step_number=game.step_number - 1,  # Show the step that just completed
            max_steps=game.max_steps,
            turns=step_turns,
            conversation_history=game.public_action_history,
            eliminated=eliminated_agent.name if eliminated_agent else None,
            winner=winner,
            game_over=game_over,
            message=message
        )
    
    def process_step(self, game_id: str) -> Optional[StepResponse]:
        """Alias for step_game to maintain compatibility with tests"""
        return self.step_game(game_id)
