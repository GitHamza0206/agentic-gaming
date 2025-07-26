from typing import List, Dict, Optional
from enum import Enum
from pydantic import BaseModel

class ActionType(str, Enum):
    THINK = "think"
    SPEAK = "speak"
    VOTE = "vote"

class MeetingPhase(str, Enum):
    INITIAL_STATEMENTS = "initial_statements"
    FOLLOW_UP = "follow_up"
    VOTING = "voting"
    RESULTS = "results"
    IMPOSTER_KILL = "imposter_kill"
    GAME_END = "game_end"

class GamePhase(str, Enum):
    MEETING = "meeting"
    GAME_OVER = "game_over"

class GameStatus(str, Enum):
    WAITING = "waiting"
    ACTIVE = "active"
    FINISHED = "finished"

class MeetingTrigger(str, Enum):
    DEAD_BODY = "dead_body"
    EMERGENCY_BUTTON = "emergency_button"

class Agent(BaseModel):
    id: int
    name: str
    color: str
    is_impostor: bool = False
    is_alive: bool = True
    votes_received: int = 0

class AgentAction(BaseModel):
    agent_id: int
    action_type: ActionType
    content: str
    target_agent_id: Optional[int] = None
    step_number: Optional[int] = None
    is_follow_up: bool = False

class Statement(BaseModel):
    agent_id: int
    agent_name: str
    content: str
    step_number: int
    is_follow_up: bool = False

class Vote(BaseModel):
    voter_id: int
    voter_name: str
    target_id: Optional[int]
    target_name: Optional[str]
    reasoning: str

class MeetingResult(BaseModel):
    ejected_agent_id: Optional[int]
    ejected_agent_name: Optional[str]
    vote_counts: Dict[int, int]
    is_imposter_ejected: bool
    game_continues: bool
    next_kill_target: Optional[int] = None
    dialogue_history: List[Statement] = []

class GameState(BaseModel):
    game_id: str
    status: GameStatus
    phase: GamePhase
    meeting_phase: MeetingPhase = MeetingPhase.INITIAL_STATEMENTS
    step_number: int
    max_steps: int = 15
    agents: List[Agent]
    action_history: List[AgentAction]
    dialogue_history: List[Statement] = []
    current_votes: Dict[int, int] = {}
    winner: Optional[str] = None
    impostor_id: int
    meeting_trigger: MeetingTrigger
    reporter_id: int
    meeting_reason: str
    meeting_result: Optional[MeetingResult] = None

class InitGameResponse(BaseModel):
    game_id: str
    message: str
    agents: List[Agent]
    impostor_revealed: str
    meeting_trigger: MeetingTrigger
    reporter_name: str
    meeting_reason: str

class AgentTurn(BaseModel):
    agent_id: int
    think: Optional[str] = None
    speak: Optional[str] = None
    vote: Optional[str] = None
    action_type: str = "speak"  # "speak", "vote", "think"

class CurrentVoteStatus(BaseModel):
    """Real-time vote tracking during meeting"""
    voter_id: int
    voter_name: str
    target_id: Optional[int] = None  # None for skip
    target_name: str = "Skip"
    vote_time: int  # Step number when vote was cast

class ConversationEntry(BaseModel):
    agent_id: int
    action_type: str  # "speak", "vote", etc.
    content: str
    target_agent_id: Optional[int] = None

class StepResponse(BaseModel):
    game_id: str
    phase: str  # "active", "voting", "ended"
    step_number: int
    max_steps: int
    turns: List[AgentTurn]
    conversation_history: List[ConversationEntry]
    current_votes: List[CurrentVoteStatus] = []  # Real-time vote tracking
    eliminated: Optional[str] = None
    winner: Optional[str] = None
    game_over: bool = False
    message: str

class GameStateResponse(BaseModel):
    game_id: str
    status: GameStatus
    phase: GamePhase
    meeting_phase: MeetingPhase
    step_number: int
    max_steps: int
    agents: List[Agent]
    action_history: List[AgentAction]
    dialogue_history: List[Statement]
    current_votes: Dict[str, int]
    winner: Optional[str] = None
    alive_count: int
    impostor_alive: bool
    meeting_result: Optional[MeetingResult] = None