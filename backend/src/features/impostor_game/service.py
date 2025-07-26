import random
import uuid
import asyncio
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
    
    def _create_agent(self, agent_data: Agent):
        """Create appropriate agent type based on role"""
        if agent_data.is_impostor:
            return Impostor(agent_data, self.llm_client)
        else:
            return Crewmate(agent_data, self.llm_client)
    
    def create_game(self, num_players: int = 4, max_steps: int = 30) -> InitGameResponse:
        game_id = str(uuid.uuid4())
        
        # Among Us style names and colors
        crewmates_data = [
            ("Red", "red"), ("Blue", "blue"), ("Green", "green"), ("Pink", "pink"),
            ("Orange", "orange"), ("Yellow", "yellow"), ("Black", "black"), ("White", "white")
        ]
        
        # Limit to requested number of players
        selected_data = crewmates_data[:num_players]
        agents = []
        
        for i, (name, color) in enumerate(selected_data):
            agents.append(Agent(id=i, name=name, color=color, is_impostor=False))
        
        impostor_id = random.randint(0, num_players - 1)
        agents[impostor_id].is_impostor = True
        
        # Choose random meeting trigger and reporter
        meeting_trigger = random.choice([MeetingTrigger.DEAD_BODY, MeetingTrigger.EMERGENCY_BUTTON])
        reporter_id = random.randint(0, num_players - 1)
        
        if meeting_trigger == MeetingTrigger.DEAD_BODY:
            dead_colors = ["Purple", "Brown", "Cyan", "Lime"]  # Colors not in game
            dead_color = random.choice(dead_colors)
            meeting_reason = f"{agents[reporter_id].name} found {dead_color}'s body in {'Electrical' if random.random() > 0.5 else 'Medbay'}"
        else:
            meeting_reason = f"{agents[reporter_id].name} pressed the emergency button"
        
        game_state = GameState(
            game_id=game_id,
            status=GameStatus.ACTIVE,
            phase=GamePhase.ACTIVE,
            step_number=1,
            max_steps=max_steps,
            agents=agents,
            public_action_history=[],
            private_thoughts={},
            impostor_id=impostor_id,
            meeting_trigger=meeting_trigger,
            reporter_id=reporter_id,
            meeting_reason=meeting_reason
        )
        
        self.games[game_id] = game_state
        
        return InitGameResponse(
            game_id=game_id,
            message=f"EMERGENCY MEETING! {meeting_reason}",
            agents=agents,
            impostor_revealed=f"The impostor is: {agents[impostor_id].name} ({agents[impostor_id].color})",
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
    
    async def _select_next_speaker(self, candidate_turns: List[AgentTurn], conversation_history: List[AgentAction], alive_agents: List[Agent], step_number: int) -> AgentTurn:
        """Use LLM to intelligently select who should speak next based on conversation flow"""
        if len(candidate_turns) == 1:
            return candidate_turns[0]
        
        # Build context for LLM decision
        recent_speakers = []
        for action in conversation_history[-5:]:  # Last 5 speaking actions
            if action.action_type == ActionType.SPEAK:
                speaker_name = next((agent.name for agent in alive_agents if agent.id == action.agent_id), f"Agent{action.agent_id}")
                recent_speakers.append(f"{speaker_name}: {action.content}")
        
        conversation_context = "\n".join(recent_speakers) if recent_speakers else "No previous conversation."
        
        # Prepare candidate information
        candidates_info = []
        for turn in candidate_turns:
            agent_name = next((agent.name for agent in alive_agents if agent.id == turn.agent_id), f"Agent{turn.agent_id}")
            candidates_info.append(f"- {agent_name} wants to say: \"{turn.speak}\"")
        
        candidates_text = "\n".join(candidates_info)
        
        prompt = f"""You are moderating an emergency meeting in a social deduction game similar to Among Us. Based on the conversation flow, decide who should speak next.

Current step: {step_number}

Recent conversation:
{conversation_context}

Candidates who want to speak:
{candidates_text}

Choose the most logical speaker based on:
1. Natural conversation flow and responses
2. Who hasn't spoken recently
3. Relevance of their message to current discussion
4. Creating engaging dialogue dynamics

Respond with ONLY the agent's name (e.g., "Red", "Blue", etc.) - no explanation needed."""

        try:
            response = await self.llm_client.generate_response(
                messages=[{"role": "user", "content": prompt}],
                max_tokens=50,
                temperature=0.3
            )
            
            # Find matching agent by name
            chosen_name = response.strip().strip('"')
            for turn in candidate_turns:
                agent_name = next((agent.name for agent in alive_agents if agent.id == turn.agent_id), f"Agent{turn.agent_id}")
                if agent_name.lower() == chosen_name.lower():
                    return turn
            
            # Fallback to first candidate if name not found
            return candidate_turns[0]
            
        except Exception:
            # Fallback to random selection if LLM fails
            return random.choice(candidate_turns)
    
    async def step_game(self, game_id: str) -> Optional[StepResponse]:
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
        if game.step_number < 25:  # Normal conversation phase
            context_base = f"Step {game.step_number}/{game.max_steps}. You are doing tasks around the ship with {len(alive_agents)} crewmates."
            if game.step_number == 1:
                context = f"{context_base} You just started your shift. Share your thoughts about the tasks or your fellow crewmates."
            elif game.step_number < 10:
                context = f"{context_base} Continue doing your tasks. You can chat casually with others or share observations."
            elif game.step_number < 20:
                context = f"{context_base} You've been working for a while. Share any suspicions or observations about other crewmates."
            else:
                context = f"{context_base} Something feels off. Be more alert and share any concerns you might have."
        else:  # Emergency meeting phase
            context_base = f"EMERGENCY MEETING! {game.meeting_reason}. Step {game.step_number}/{game.max_steps}. Alive crewmates: {len(alive_agents)}."
            if game.step_number == 25:
                context = f"{context_base} There is an impostor among you! Share what you know and discuss who seems suspicious."
            else:
                context = f"{context_base} Continue the discussion. Find the impostor before it's too late!"
        
        # Create async tasks for all agents to process in parallel
        async def process_agent(agent_data: Agent) -> AgentTurn:
            agent = self._create_agent(agent_data)
            
            # Get agent's private thoughts
            private_thoughts = game.private_thoughts.get(agent_data.id, [])
            
            # Add special context for reporter when emergency meeting starts
            agent_context = context
            if game.step_number == 25 and agent_data.id == game.reporter_id:
                agent_context = f"{context} You are the one who called this meeting because: {game.meeting_reason}"
            
            turn = await agent.choose_action(agent_context, game.public_action_history, private_thoughts, game.step_number, game.agents)
            
            # Save memory update to persistent agent data (if not already added by agent)
            if turn.memory_update and (not agent_data.memory_history or agent_data.memory_history[-1] != turn.memory_update):
                agent_data.memory_history.append(turn.memory_update)
            
            return turn
        
        # Execute all agent turns in parallel
        tasks = [process_agent(agent_data) for agent_data in alive_agents]
        step_turns = await asyncio.gather(*tasks)
        
        # Process all turns - store thinks privately
        for turn in step_turns:
            if turn.agent_id not in game.private_thoughts:
                game.private_thoughts[turn.agent_id] = []
            game.private_thoughts[turn.agent_id].append(AgentAction(
                agent_id=turn.agent_id,
                action_type=ActionType.THINK,
                content=turn.think,
                target_agent_id=None
            ))
        
        # After all agents have generated their turns, use LLM to intelligently select speaker
        agents_who_want_to_speak = [turn for turn in step_turns if turn.speak is not None]
        if agents_who_want_to_speak:
            chosen_speaker = await self._select_next_speaker(agents_who_want_to_speak, game.public_action_history, alive_agents, game.step_number)
            game.public_action_history.append(AgentAction(
                agent_id=chosen_speaker.agent_id,
                action_type=ActionType.SPEAK,
                content=chosen_speaker.speak,
                target_agent_id=None
            ))
        
        # Now process all votes
        for turn in step_turns:
            if turn.vote is not None:
                game.public_action_history.append(AgentAction(
                    agent_id=turn.agent_id,
                    action_type=ActionType.VOTE,
                    content=f"I vote to eliminate Agent{turn.vote}",
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
    
    async def process_step(self, game_id: str) -> Optional[StepResponse]:
        """Alias for step_game to maintain compatibility with tests"""
        return await self.step_game(game_id)
