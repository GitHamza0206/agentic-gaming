# AI Impostor Game - Application Documentation

## Overview

The AI Impostor Game is a sophisticated implementation of an Among Us-style social deduction game where AI agents autonomously play as crewmates and impostors. Built with FastAPI and powered by Cerebras Cloud SDK, this application demonstrates advanced AI agent interactions in a game environment.

## System Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   AI Service    │
│   (Client)      │◄──►│   (FastAPI)     │◄──►│   (Cerebras)    │
│                 │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

### Component Breakdown

#### 1. Backend Services (`backend/src/`)

**Core Infrastructure:**
- `main.py` - FastAPI application with CORS middleware
- `core/llm_client.py` - Cerebras Cloud SDK integration

**Game Engine:**
- `features/impostor_game/service.py` - Game logic and state management
- `features/impostor_game/schema.py` - Data models and validation
- `features/impostor_game/agents.py` - AI agent implementations
- `features/impostor_game/routes.py` - REST API endpoints

## Game Mechanics

### Game Flow

```
Game Initialization
        ↓
Emergency Meeting Called
        ↓
Discussion Phase (Multiple Steps)
        ↓
Voting Phase
        ↓
Elimination/Win Check
        ↓
Game Over or Continue
```

### Agent Behavior System

Each AI agent operates with:

1. **Private Reasoning** - Internal thoughts not visible to other agents
2. **Public Communication** - Statements visible to all agents
3. **Voting Decision** - Choice to eliminate another agent

### Agent Types

#### Crewmate Agent
- **Goal**: Identify and eliminate the impostor
- **Strategy**: Analyze behavior patterns, ask questions, vote suspiciously
- **Prompt Focus**: Logical deduction and social analysis

#### Impostor Agent
- **Goal**: Survive elimination rounds
- **Strategy**: Blend in, deflect suspicion, influence votes
- **Prompt Focus**: Deception and manipulation tactics

## Technical Implementation

### Data Models

#### Core Entities

```python
class Agent:
    id: int
    name: str           # Among Us colors (Red, Blue, Green, etc.)
    color: str
    is_impostor: bool
    is_alive: bool
    votes_received: int

class GameState:
    game_id: str
    status: GameStatus  # waiting, active, finished
    phase: GamePhase    # active, game_over
    step_number: int
    agents: List[Agent]
    public_action_history: List[AgentAction]
    private_thoughts: Dict[int, List[AgentAction]]
    current_votes: Dict[int, int]
    winner: Optional[str]
```

#### Action System

```python
class ActionType(Enum):
    THINK = "think"     # Private reasoning
    SPEAK = "speak"     # Public statement
    VOTE = "vote"       # Elimination vote

class AgentTurn:
    agent_id: int
    think: str          # Always required
    speak: Optional[str] # Optional public statement
    vote: Optional[int]  # Optional vote target
```

### AI Integration

#### LLM Client Configuration
- **Model**: Qwen-3-235B via Cerebras Cloud SDK
- **Temperature**: 0.7 for balanced creativity/consistency
- **Max Tokens**: 200 for concise responses
- **Response Format**: Structured JSON for reliable parsing

#### Prompt Engineering

**Crewmate Prompt Structure:**
```
System: Role definition + goal explanation
Context: Current game situation
History: Public discussion + private thoughts
Task: JSON response with think/speak/vote
```

**Impostor Prompt Structure:**
```
System: Impostor role + deception objectives
Context: Game state + suspicion levels
History: Public actions + strategic thoughts
Task: Survival-focused JSON response
```

## API Specification

### Endpoints

#### `POST /impostor-game/init`
Creates a new game instance with 8 AI agents.

**Response:**
```json
{
  "game_id": "uuid",
  "message": "Game created",
  "agents": [...],
  "impostor_revealed": "Agent name",
  "meeting_trigger": "dead_body|emergency_button",
  "reporter_name": "Agent name",
  "meeting_reason": "Description"
}
```

#### `POST /impostor-game/step/{game_id}`
Advances the game by one discussion step.

**Response:**
```json
{
  "game_id": "uuid",
  "phase": "active|game_over",
  "step_number": 1,
  "turns": [
    {
      "agent_id": 0,
      "think": "Private thoughts",
      "speak": "Public statement",
      "vote": 3
    }
  ],
  "eliminated": "Agent name",
  "winner": "crewmates|impostor",
  "game_over": false,
  "message": "Step summary"
}
```

#### `GET /impostor-game/game/{game_id}`
Retrieves current game state.

**Response:**
```json
{
  "game_id": "uuid",
  "status": "waiting|active|finished",
  "phase": "active|game_over",
  "step_number": 1,
  "agents": [...],
  "public_action_history": [...],
  "current_votes": {},
  "winner": null,
  "alive_count": 8,
  "impostor_alive": true
}
```

## Game Logic Details

### Initialization Process

1. **Agent Creation**: 8 agents with Among Us colors (Red, Blue, Green, Pink, Orange, Yellow, Black, White)
2. **Impostor Assignment**: Random selection of one agent as impostor
3. **Meeting Setup**: Random trigger (dead body discovery or emergency button press)
4. **Context Generation**: Backstory for the emergency meeting

### Step Processing

1. **Turn Execution**: Each alive agent takes a turn (think → speak → vote)
2. **Vote Collection**: Aggregate all voting decisions
3. **Elimination Logic**: Agent with most votes is eliminated (ties result in no elimination)
4. **Win Condition Check**: Game ends if impostor eliminated or equals/outnumbers crewmates

### Win Conditions

**Crewmates Win:**
- Impostor is eliminated through voting
- All tasks completed (future feature)

**Impostor Wins:**
- Survives until equal/outnumber crewmates
- Successfully eliminates all crewmates

## Configuration

### Environment Variables

```bash
CEREBRAS_API_KEY=your_api_key_here  # Required for AI functionality
PORT=8000                           # Server port (default: 8000)
```

### Dependencies

**Core Framework:**
- `fastapi` - Web framework
- `uvicorn` - ASGI server
- `pydantic` - Data validation

**AI Integration:**
- `cerebras-cloud-sdk` - LLM inference
- `python-dotenv` - Environment management

**Development:**
- `python-multipart` - Form data handling
- `requests` - HTTP client

## Development Workflow

### Local Setup

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure environment
cp .env.example .env  # Add your CEREBRAS_API_KEY

# 3. Run development server
PYTHONPATH=. python src/main.py
```

### Testing Game Flow

```bash
# 1. Initialize new game
curl -X POST http://localhost:8000/impostor-game/init

# 2. Advance game step
curl -X POST http://localhost:8000/impostor-game/step/{game_id}

# 3. Check game state
curl -X GET http://localhost:8000/impostor-game/game/{game_id}
```

## Future Enhancements

### Planned Features

1. **Task System**: Implement crewmate tasks and progress tracking
2. **Map Integration**: Add spatial awareness and movement mechanics
3. **Multiple Impostors**: Support for 2-3 impostor games
4. **Spectator Mode**: Real-time game observation
5. **Game Analytics**: Statistical analysis of agent behaviors
6. **Custom Agent Personalities**: Configurable agent archetypes

### Technical Improvements

1. **Database Persistence**: Replace in-memory storage with PostgreSQL
2. **WebSocket Support**: Real-time updates for live games
3. **Agent Memory**: Long-term memory across multiple games
4. **Performance Optimization**: Caching and response time improvements
5. **Error Handling**: Robust error recovery and logging

## Security Considerations

### API Security
- CORS configuration for cross-origin requests
- Input validation via Pydantic models
- API key management for LLM service

### Data Privacy
- No persistent user data storage
- Temporary game state in memory
- AI service interactions logged for debugging

### Rate Limiting
- Consider implementing rate limiting for production deployment
- Monitor API usage and costs

## Monitoring and Observability

### Logging Strategy
- Game state transitions
- AI response times and failures
- API endpoint usage metrics

### Health Checks
- `/health` endpoint for service monitoring
- LLM service availability checks
- Game state consistency validation

## Conclusion

The AI Impostor Game represents a sophisticated implementation of AI-driven social deduction gaming. By combining FastAPI's robust web framework with advanced language models, it creates an engaging and autonomous gaming experience that showcases the potential of AI agents in interactive entertainment.

The modular architecture enables easy extension and modification, making it suitable for both research purposes and commercial game development. The comprehensive API design ensures smooth integration with various frontend technologies and third-party services.