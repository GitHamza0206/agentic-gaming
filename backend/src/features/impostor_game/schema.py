from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel

class GamePhase(str, Enum):
    DISCUSSION = "discussion"
    VOTING = "voting"
    GAME_OVER = "game_over"

class GameStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"

class Agent(BaseModel):
    id: int
    name: str
    is_impostor: bool = False
    is_alive: bool = True
    votes_received: int = 0

class GameState(BaseModel):
    game_id: str
    status: GameStatus
    phase: GamePhase
    round_number: int
    agents: List[Agent]
    discussion_history: List[str]
    current_speaker: Optional[int] = None
    votes: Dict[int, int] = {}
    winner: Optional[str] = None
    impostor_id: int

class InitGameResponse(BaseModel):
    game_id: str
    message: str
    agents: List[Agent]
    impostor_revealed: str

class StepResponse(BaseModel):
    game_id: str
    phase: GamePhase
    round_number: int
    current_speaker: Optional[str] = None
    message: Optional[str] = None
    response: Optional[str] = None
    votes: Optional[Dict[str, int]] = None
    eliminated: Optional[str] = None
    winner: Optional[str] = None
    game_over: bool = False
    next_action: str

class GameStateResponse(BaseModel):
    game_id: str
    status: GameStatus
    phase: GamePhase
    round_number: int
    agents: List[Agent]
    discussion_history: List[str]
    current_speaker: Optional[str] = None
    winner: Optional[str] = None
    alive_count: int
    impostor_alive: bool