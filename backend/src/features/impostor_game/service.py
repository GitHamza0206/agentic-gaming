import random
import uuid
from typing import List, Dict, Optional, Tuple
from src.core.llm_client import LLMClient
from .schema import (
    Agent, GameState, GameStatus, GamePhase, 
    InitGameResponse, StepResponse, GameStateResponse
)

class ImpostorAgent:
    def __init__(self, agent_data: Agent, llm_client: LLMClient):
        self.data = agent_data
        self.llm_client = llm_client
    
    def get_role_description(self) -> str:
        if self.data.is_impostor:
            return f"Tu es {self.data.name}, l'IMPOSTEUR dans ce groupe de 8 agents. Ton objectif est de ne pas te faire découvrir. Tu dois agir comme un agent innocent tout en essayant subtilement de semer le doute sur les autres. Ne révèle JAMAIS que tu es l'imposteur."
        else:
            return f"Tu es {self.data.name}, un agent INNOCENT dans ce groupe de 8 agents. Il y a un imposteur parmi vous et ton objectif est de le découvrir. Analyse les comportements suspects et pose des questions pertinentes."
    
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
        
        agent_names = ["Alice", "Bob", "Charlie", "Diana", "Eve", "Frank", "Grace", "Henry"]
        agents = []
        
        for i, name in enumerate(agent_names):
            agents.append(Agent(id=i, name=name, is_impostor=False))
        
        impostor_id = random.randint(0, 7)
        agents[impostor_id].is_impostor = True
        
        game_state = GameState(
            game_id=game_id,
            status=GameStatus.ACTIVE,
            phase=GamePhase.DISCUSSION,
            round_number=1,
            agents=agents,
            discussion_history=[],
            impostor_id=impostor_id
        )
        
        self.games[game_id] = game_state
        
        return InitGameResponse(
            game_id=game_id,
            message=f"Jeu initialisé avec 8 agents. Round 1 - Phase de discussion.",
            agents=agents,
            impostor_revealed=f"L'imposteur est: {agents[impostor_id].name} (ID: {impostor_id})"
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
        
        return GameStateResponse(
            game_id=game.game_id,
            status=game.status,
            phase=game.phase,
            round_number=game.round_number,
            agents=game.agents,
            discussion_history=game.discussion_history,
            current_speaker=current_speaker_name,
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
                round_number=game.round_number,
                winner=game.winner,
                game_over=True,
                next_action="Jeu terminé"
            )
        
        if game.phase == GamePhase.DISCUSSION:
            return self._handle_discussion_phase(game)
        elif game.phase == GamePhase.VOTING:
            return self._handle_voting_phase(game)
        
        return None