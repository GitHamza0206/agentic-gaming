# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Development Commands

### Running the Application
```bash
# Start the FastAPI server (from backend/ directory)
cd backend
python src/main.py
# Server runs on port 8000 by default, configurable via PORT env var
```

### Dependencies
```bash
# Install Python dependencies (from backend/ directory)
cd backend
pip install -r requirements.txt
```

### Environment Setup
- Create a `.env` file in the backend directory with required environment variables
- `CEREBRAS_API_KEY` is required for LLM functionality (currently using Cerebras Cloud SDK)

## Architecture Overview

This is an **AI-powered gaming API** built with FastAPI, specifically implementing an "Impostor Game" similar to Among Us but with AI agents.

### Core Components

**Backend Structure:**
- `backend/src/main.py` - FastAPI application entry point with CORS middleware
- `backend/src/core/llm_client.py` - LLM client wrapper using Cerebras Cloud SDK (Qwen-3-235B model)
- `backend/src/features/impostor_game/` - Complete impostor game implementation

**Game Architecture:**
- **Service Layer** (`service.py`) - Game logic, state management, step processing
- **Schema Layer** (`schema.py`) - Pydantic models for game state, agents, actions, and API responses
- **Agent Layer** (`agents.py`) - AI agent implementations (Crewmate and Impostor classes)
- **Routes Layer** (`routes.py`) - FastAPI endpoints for game operations

### Game Flow
1. **Game Initialization** - Creates 8 AI agents (7 crewmates + 1 random impostor)
2. **Emergency Meeting** - Triggered by either dead body discovery or emergency button
3. **Turn-Based Discussion** - Each agent thinks (private), speaks (public), and optionally votes
4. **Elimination System** - Majority votes eliminate an agent
5. **Win Conditions** - Crewmates win by finding impostor, impostor wins by survival/numbers

### Key Technical Details

**AI Agent System:**
- Each agent uses LLM for decision-making with role-specific prompts
- Agents maintain private thoughts and participate in public discussion
- JSON-based response parsing for structured agent actions (think/speak/vote)

**Game State Management:**
- Persistent game states stored in memory (`ImpostorGameService.games`)
- Separate tracking of public actions vs private thoughts
- Vote counting and elimination logic with majority rules

**API Endpoints:**
- `POST /impostor-game/init` - Create new game
- `POST /impostor-game/step/{game_id}` - Advance game by one step
- `GET /impostor-game/game/{game_id}` - Get current game state
- `GET /impostor-game/health` - Health check

### Dependencies Note
- Uses **Cerebras Cloud SDK** for LLM inference (not OpenAI)
- FastAPI with Pydantic for API structure
- Environment variables for configuration