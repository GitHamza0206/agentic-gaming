from typing import List, Dict, Optional, TYPE_CHECKING
from enum import Enum
from pydantic import BaseModel

if TYPE_CHECKING:
    from typing import ForwardRef

class ActionType(str, Enum):
    THINK = "think"
    SPEAK = "speak"
    VOTE = "vote"

class GamePhase(str, Enum):
    ACTIVE = "active"
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
    memory_history: List['AgentMemory'] = []  # Agent's memory across all steps
    location: str = ""  # Current location from game-master.json
    action: str = ""  # Current action from game-master.json
    met: List[str] = []  # Agents met in current step

class AgentAction(BaseModel):
    agent_id: int
    action_type: ActionType
    content: str
    target_agent_id: Optional[int] = None

class AgentMemory(BaseModel):
    step_number: int
    location: str  # Where they were
    action: str  # What they were doing
    met: List[str] = []  # Who they met (agent colors/names)
    
class AgentTurn(BaseModel):
    agent_id: int
    think: str  # Always required - agent's private thoughts
    speak: Optional[str] = None  # Optional - public statement
    vote: Optional[int] = None  # Optional - vote target agent_id
    memory_update: Optional['AgentMemory'] = None  # Memory from this step

class GameState(BaseModel):
    game_id: str
    status: GameStatus
    phase: GamePhase
    step_number: int
    max_steps: int = 30
    agents: List[Agent]
    public_action_history: List[AgentAction]  # Only SPEAK and VOTE actions
    private_thoughts: Dict[int, List[AgentAction]] = {}  # THINK actions per agent
    current_votes: Dict[int, int] = {}
    winner: Optional[str] = None
    impostor_id: int
    meeting_trigger: MeetingTrigger
    reporter_id: int
    meeting_reason: str

class InitGameResponse(BaseModel):
    game_id: str
    message: str
    agents: List[Agent]
    impostor_revealed: str
    meeting_trigger: MeetingTrigger
    reporter_name: str
    meeting_reason: str

class StepResponse(BaseModel):
    game_id: str
    phase: GamePhase
    step_number: int
    max_steps: int
    turns: List[AgentTurn]  # Each agent's turn with think/speak/vote
    conversation_history: List[AgentAction]  # Public conversation history (SPEAK and VOTE actions)
    eliminated: Optional[str] = None
    winner: Optional[str] = None
    game_over: bool = False
    message: str

class GameStateResponse(BaseModel):
    game_id: str
    status: GameStatus
    phase: GamePhase
    step_number: int
    max_steps: int
    agents: List[Agent]
    public_action_history: List[AgentAction]  # Only public actions (SPEAK/VOTE)
    current_votes: Dict[str, int]
    winner: Optional[str] = None
    alive_count: int
    impostor_alive: bool

# Update forward references
Agent.model_rebuild()
AgentTurn.model_rebuild()
