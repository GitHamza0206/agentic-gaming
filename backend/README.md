# AI Impostor Game Backend

FastAPI-based backend for an AI-powered impostor game similar to Among Us, where AI agents play as crewmates and impostors.

## Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   Create a `.env` file with:
   ```
   CEREBRAS_API_KEY=your_api_key_here
   PORT=8000
   ```

3. **Run the server:**
   ```bash
   python src/main.py
   ```
   Server runs on `http://localhost:8000`

## API Endpoints

- `POST /impostor-game/init` - Create new game with 8 AI agents
- `POST /impostor-game/step/{game_id}` - Advance game by one step
- `GET /impostor-game/game/{game_id}` - Get current game state
- `GET /impostor-game/health` - Health check

## Game Flow

1. **Initialization**: Creates 7 crewmates + 1 random impostor
2. **Emergency Meeting**: Triggered by discovery or button press
3. **Discussion Phase**: Each agent thinks privately, speaks publicly, votes
4. **Elimination**: Majority vote eliminates an agent
5. **Win Conditions**: Crewmates find impostor OR impostor survives

## Architecture

```
backend/
├── src/
│   ├── main.py              # FastAPI app entry point
│   ├── core/
│   │   └── llm_client.py    # Cerebras LLM client
│   └── features/impostor_game/
│       ├── service.py       # Game logic & state
│       ├── schema.py        # Pydantic models
│       ├── agents.py        # AI agent classes
│       └── routes.py        # API endpoints
└── requirements.txt
```

## Dependencies

- **FastAPI** - Web framework
- **Cerebras Cloud SDK** - LLM inference (Qwen-3-235B model)
- **Pydantic** - Data validation
- **Uvicorn** - ASGI server