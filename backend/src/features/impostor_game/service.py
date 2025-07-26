import random
import uuid
from typing import List, Dict, Optional, Tuple
from src.core.llm_client import LLMClient
from .schema import (
    Agent, GameState, GameStatus, GamePhase, ActionType, AgentAction, MeetingTrigger,
    InitGameResponse, StepResponse, GameStateResponse
)

class ImpostorAgent:
    def __init__(self, agent_data: Agent, llm_client: LLMClient):
        self.data = agent_data
        self.llm_client = llm_client
    
    def get_role_description(self) -> str:
        if self.data.is_impostor:
            return f"Tu es {self.data.name} ({self.data.color}), l'IMPOSTEUR dans ce vaisseau spatial. Une réunion d'urgence a été déclenchée. Ton objectif est de ne pas te faire découvrir. Tu dois agir comme un crewmate innocent, nier toute accusation, et essayer de rediriger les soupçons vers les autres. Sois subtil et convaincant. Ne révèle JAMAIS que tu es l'imposteur."
        else:
            return f"Tu es {self.data.name} ({self.data.color}), un CREWMATE dans ce vaisseau spatial. Une réunion d'urgence a été déclenchée. Il y a un imposteur parmi vous et ton objectif est de le découvrir avant qu'il ne vous élimine tous. Analyse les comportements suspects, pose des questions pertinentes, et vote pour éliminer l'imposteur."
    
    def choose_action(self, context: str, action_history: List[AgentAction], step_number: int) -> AgentAction:
        system_prompt = self.get_role_description()
        
        # Format action history for context
        recent_actions = []
        for action in action_history[-20:]:
            agent_name = f"Agent{action.agent_id}"
            recent_actions.append(f"{agent_name} {action.action_type.value}: {action.content}")
        
        action_context = "\n".join(recent_actions) if recent_actions else "Aucune action précédente."
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Contexte du jeu: {context}"},
            {"role": "system", "content": f"Historique des actions:\n{action_context}"},
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
        
        # Debug: print what LLM actually responds
        print(f"DEBUG - {self.data.name} LLM response: {response}")
        
        # Parse response - be more flexible
        try:
            # Clean the response first
            clean_response = response.strip()
            
            # Try to extract the format even if there's extra text
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
            import re
            numbers = re.findall(r'\d+', response)
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

    def generate_response(self, context: str, discussion_history: List[str]) -> str:
        system_prompt = self.get_role_description()
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Contexte du jeu: {context}"},
            {"role": "system", "content": "Historique de la discussion:\n" + "\n".join(discussion_history[-10:])},
            {"role": "user", "content": "Réponds en tant que ton personnage. Sois concis (maximum 2-3 phrases). Reste dans le rôle."}
        ]
        
        response = self.llm_client.generate_response(messages, max_tokens=200, temperature=0.7)
        return response if response else "Je ne peux pas répondre pour le moment..."
    
    def vote(self, alive_agents: List[Agent], discussion_history: List[str]) -> Optional[int]:
        if not self.data.is_alive:
            return None
            
        voteable_agents = [a for a in alive_agents if a.id != self.data.id]
        if not voteable_agents:
            return None
        
        system_prompt = self.get_role_description()
        agent_list = ", ".join([f"{a.name} (ID: {a.id})" for a in voteable_agents])
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "system", "content": f"Agents vivants à éliminer: {agent_list}"},
            {"role": "system", "content": "Historique de la discussion:\n" + "\n".join(discussion_history[-15:])},
            {"role": "user", "content": "Choisis l'ID de l'agent que tu veux éliminer. Réponds UNIQUEMENT avec le numéro ID, rien d'autre."}
        ]
        
        response = self.llm_client.generate_response(messages, max_tokens=50, temperature=0.5)
        
        try:
            vote_id = int(response.strip().split()[0])
            if any(a.id == vote_id for a in voteable_agents):
                return vote_id
        except:
            pass
        
        return random.choice(voteable_agents).id if voteable_agents else None

class ImpostorGameService:
    def __init__(self):
        self.games: Dict[str, GameState] = {}
        self.llm_client = LLMClient()
    
    def create_game(self) -> InitGameResponse:
        game_id = str(uuid.uuid4())
        
        # Among Us style names and colors
        crewmates_data = [
            ("Red", "red"), ("Blue", "blue"), ("Green", "green"), ("Pink", "pink"),
            ("Orange", "orange"), ("Yellow", "yellow"), ("Black", "black"), ("White", "white")
        ]
        agents = []
        
        for i, (name, color) in enumerate(crewmates_data):
            agents.append(Agent(id=i, name=name, color=color, is_impostor=False))
        
        impostor_id = random.randint(0, 7)
        agents[impostor_id].is_impostor = True
        
        # Choose random meeting trigger and reporter
        meeting_trigger = random.choice([MeetingTrigger.DEAD_BODY, MeetingTrigger.EMERGENCY_BUTTON])
        reporter_id = random.randint(0, 7)
        
        if meeting_trigger == MeetingTrigger.DEAD_BODY:
            dead_colors = ["Purple", "Brown", "Cyan", "Lime"]  # Colors not in game
            dead_color = random.choice(dead_colors)
            meeting_reason = f"{agents[reporter_id].name} a trouvé le corps de {dead_color} dans {'Electrical' if random.random() > 0.5 else 'Medbay'}"
        else:
            meeting_reason = f"{agents[reporter_id].name} a appuyé sur le bouton d'urgence"
        
        game_state = GameState(
            game_id=game_id,
            status=GameStatus.ACTIVE,
            phase=GamePhase.ACTIVE,
            step_number=1,
            max_steps=30,
            agents=agents,
            action_history=[],
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
            impostor_revealed=f"L'imposteur est: {agents[impostor_id].name} ({agents[impostor_id].color})",
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
        current_speaker_name = None
        if game.current_speaker is not None:
            current_speaker_name = next(
                (a.name for a in game.agents if a.id == game.current_speaker), 
                None
            )
        
        # Convert current votes to string keys
        current_votes_str = {str(k): v for k, v in game.current_votes.items()}
        
        return GameStateResponse(
            game_id=game.game_id,
            status=game.status,
            phase=game.phase,
            step_number=game.step_number,
            max_steps=game.max_steps,
            agents=game.agents,
            action_history=game.action_history,
            current_votes=current_votes_str,
            winner=game.winner,
            alive_count=len(alive_agents),
            impostor_alive=any(a.is_impostor for a in alive_agents)
        )
    
    def _get_alive_agents(self, game: GameState) -> List[Agent]:
        return [agent for agent in game.agents if agent.is_alive]
    
    def _handle_discussion_phase(self, game: GameState) -> StepResponse:
        alive_agents = self._get_alive_agents(game)
        
        if game.current_speaker is None:
            alive_ids = [a.id for a in alive_agents]
            random.shuffle(alive_ids)
            game.current_speaker = alive_ids[0]
        
        current_agent_data = next(a for a in game.agents if a.id == game.current_speaker)
        agent = ImpostorAgent(current_agent_data, self.llm_client)
        
        context = f"Round {game.round_number}. Agents vivants: {len(alive_agents)}. Vous devez trouver l'imposteur."
        response = agent.generate_response(context, game.discussion_history)
        
        full_message = f"{current_agent_data.name}: {response}"
        game.discussion_history.append(full_message)
        
        remaining_speakers = [a.id for a in alive_agents if a.id != game.current_speaker]
        
        if remaining_speakers:
            game.current_speaker = random.choice(remaining_speakers)
            next_speaker_name = next(a.name for a in game.agents if a.id == game.current_speaker)
            next_action = f"Prochain: {next_speaker_name}"
        else:
            game.phase = GamePhase.VOTING
            game.current_speaker = None
            game.votes = {a.id: 0 for a in alive_agents}
            next_action = "Phase de vote"
        
        return StepResponse(
            game_id=game.game_id,
            phase=game.phase,
            round_number=game.round_number,
            current_speaker=current_agent_data.name,
            response=response,
            game_over=False,
            next_action=next_action
        )
    
    def _handle_voting_phase(self, game: GameState) -> StepResponse:
        alive_agents = self._get_alive_agents(game)
        votes_cast = {}
        
        for agent_data in alive_agents:
            agent = ImpostorAgent(agent_data, self.llm_client)
            vote_id = agent.vote(alive_agents, game.discussion_history)
            if vote_id is not None:
                votes_cast[agent_data.name] = next(a.name for a in game.agents if a.id == vote_id)
                game.votes[vote_id] += 1
        
        if not game.votes or max(game.votes.values()) == 0:
            game.phase = GamePhase.DISCUSSION
            game.round_number += 1
            return StepResponse(
                game_id=game.game_id,
                phase=GamePhase.DISCUSSION,
                round_number=game.round_number,
                message="Aucun vote valide. Nouveau round.",
                game_over=False,
                next_action="Nouvelle discussion"
            )
        
        eliminated_id = max(game.votes, key=game.votes.get)
        eliminated_agent = next(a for a in game.agents if a.id == eliminated_id)
        eliminated_agent.is_alive = False
        
        message = f"{eliminated_agent.name} éliminé avec {game.votes[eliminated_id]} votes"
        
        if eliminated_agent.is_impostor:
            game.winner = "Innocents"
            game.status = GameStatus.FINISHED
            game.phase = GamePhase.GAME_OVER
            return StepResponse(
                game_id=game.game_id,
                phase=game.phase,
                round_number=game.round_number,
                votes=votes_cast,
                eliminated=eliminated_agent.name,
                winner="Innocents",
                message="L'imposteur a été trouvé! Les innocents gagnent!",
                game_over=True,
                next_action="Jeu terminé"
            )
        
        alive_agents = self._get_alive_agents(game)
        
        if len(alive_agents) <= 2:
            impostor_alive = any(a.is_impostor for a in alive_agents)
            if impostor_alive:
                game.winner = "Imposteur"
                message += " - L'imposteur survit et gagne!"
            else:
                game.winner = "Innocents"
                message += " - Les innocents gagnent!"
            
            game.status = GameStatus.FINISHED
            game.phase = GamePhase.GAME_OVER
            return StepResponse(
                game_id=game.game_id,
                phase=game.phase,
                round_number=game.round_number,
                votes=votes_cast,
                eliminated=eliminated_agent.name,
                winner=game.winner,
                message=message,
                game_over=True,
                next_action="Jeu terminé"
            )
        
        game.phase = GamePhase.DISCUSSION
        game.round_number += 1
        game.votes = {}
        
        return StepResponse(
            game_id=game.game_id,
            phase=game.phase,
            round_number=game.round_number,
            votes=votes_cast,
            eliminated=eliminated_agent.name,
            message=f"{message} - Nouveau round",
            game_over=False,
            next_action="Nouvelle discussion"
        )
    
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
                actions=[],
                winner=game.winner,
                game_over=True,
                message="Jeu terminé"
            )
        
        # Check if max steps reached
        if game.step_number >= game.max_steps:
            alive_agents = self._get_alive_agents(game)
            impostor_alive = any(a.is_impostor for a in alive_agents)
            
            if impostor_alive:
                game.winner = "Imposteur"
                message = "Temps écoulé! L'imposteur gagne!"
            else:
                game.winner = "Innocents"
                message = "Temps écoulé! Les innocents gagnent!"
            
            game.status = GameStatus.FINISHED
            game.phase = GamePhase.GAME_OVER
            
            return StepResponse(
                game_id=game_id,
                phase=game.phase,
                step_number=game.step_number,
                max_steps=game.max_steps,
                actions=[],
                winner=game.winner,
                game_over=True,
                message=message
            )
        
        # All alive agents act in this step
        alive_agents = self._get_alive_agents(game)
        step_actions = []
        
        # Special context for the first step where reporter speaks first
        if game.step_number == 1:
            reporter = next(a for a in game.agents if a.id == game.reporter_id)
            if reporter.is_alive:
                # Reporter starts the conversation
                agent = ImpostorAgent(reporter, self.llm_client)
                action = AgentAction(
                    agent_id=reporter.id,
                    action_type=ActionType.SPEAK,
                    content=f"EMERGENCY MEETING! {game.meeting_reason}. Nous devons discuter de cette situation!",
                    target_agent_id=None
                )
                step_actions.append(action)
                game.action_history.append(action)
                
                # Other agents act
                for agent_data in alive_agents:
                    if agent_data.id != reporter.id:  # Skip reporter as they already acted
                        agent = ImpostorAgent(agent_data, self.llm_client)
                        context = f"EMERGENCY MEETING! {game.meeting_reason}. Step {game.step_number}/{game.max_steps}. Crewmates vivants: {len(alive_agents)}. Il y a un imposteur parmi vous!"
                        action = agent.choose_action(context, game.action_history, game.step_number)
                        step_actions.append(action)
                        game.action_history.append(action)
                        
                        # Handle vote actions
                        if action.action_type == ActionType.VOTE and action.target_agent_id is not None:
                            if action.target_agent_id in game.current_votes:
                                game.current_votes[action.target_agent_id] += 1
                            else:
                                game.current_votes[action.target_agent_id] = 1
        else:
            # Normal step - all agents act
            context = f"EMERGENCY MEETING en cours. Step {game.step_number}/{game.max_steps}. Crewmates vivants: {len(alive_agents)}. Trouvez l'imposteur!"
            
            for agent_data in alive_agents:
                agent = ImpostorAgent(agent_data, self.llm_client)
                action = agent.choose_action(context, game.action_history, game.step_number)
                step_actions.append(action)
                game.action_history.append(action)
                
                # Handle vote actions
                if action.action_type == ActionType.VOTE and action.target_agent_id is not None:
                    if action.target_agent_id in game.current_votes:
                        game.current_votes[action.target_agent_id] += 1
                    else:
                        game.current_votes[action.target_agent_id] = 1
        
        # Check for elimination (if someone has majority votes)
        total_alive = len(alive_agents)
        majority_needed = (total_alive // 2) + 1
        
        eliminated_agent = None
        for agent_id, votes in game.current_votes.items():
            if votes >= majority_needed:
                eliminated_agent = next((a for a in game.agents if a.id == agent_id), None)
                break
        
        message = f"Step {game.step_number} terminé."
        winner = None
        game_over = False
        
        if eliminated_agent:
            eliminated_agent.is_alive = False
            message += f" {eliminated_agent.name} ({eliminated_agent.color}) éliminé avec {game.current_votes[eliminated_agent.id]} votes!"
            
            if eliminated_agent.is_impostor:
                game.winner = "Crewmates"
                game.status = GameStatus.FINISHED
                game.phase = GamePhase.GAME_OVER
                winner = "Crewmates"
                game_over = True
                message += " L'imposteur a été trouvé! Les crewmates gagnent!"
            else:
                # Check if imposteur can still win
                remaining_alive = self._get_alive_agents(game)
                if len(remaining_alive) <= 2 and any(a.is_impostor for a in remaining_alive):
                    game.winner = "Imposteur"
                    game.status = GameStatus.FINISHED
                    game.phase = GamePhase.GAME_OVER
                    winner = "Imposteur"
                    game_over = True
                    message += " L'imposteur gagne!"
                else:
                    message += f" {eliminated_agent.name} était innocent!"
            
            # Reset votes after elimination
            game.current_votes = {}
        
        # Increment step
        game.step_number += 1
        
        return StepResponse(
            game_id=game_id,
            phase=game.phase,
            step_number=game.step_number - 1,  # Show the step that just completed
            max_steps=game.max_steps,
            actions=step_actions,
            eliminated=eliminated_agent.name if eliminated_agent else None,
            winner=winner,
            game_over=game_over,
            message=message
        )