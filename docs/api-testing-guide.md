# API Testing Guide

This guide provides comprehensive instructions for testing the AI Impostor Game API endpoints using various tools and methods.

## Prerequisites

1. **Backend Server Running**: Ensure the FastAPI server is running on `http://localhost:8000`
2. **API Key**: Valid `CEREBRAS_API_KEY` in your `.env` file
3. **Testing Tool**: Choose from curl, Postman, HTTPie, or browser

## Quick Setup Verification

First, verify your server is running:

```bash
curl http://localhost:8000/health
```

Expected response:
```json
{
  "status": "healthy",
  "api": "agentic-gaming"
}
```

## API Endpoints Testing

### 1. Initialize New Game

**Endpoint**: `POST /impostor-game/init`

#### Using curl:
```bash
curl -X POST http://localhost:8000/impostor-game/init \
  -H "Content-Type: application/json"
```

#### Using HTTPie:
```bash
http POST localhost:8000/impostor-game/init
```

#### Expected Response:
```json
{
  "game_id": "123e4567-e89b-12d3-a456-426614174000",
  "message": "Emergency meeting! New impostor game created.",
  "agents": [
    {
      "id": 0,
      "name": "Red",
      "color": "red",
      "is_impostor": false,
      "is_alive": true,
      "votes_received": 0
    },
    {
      "id": 3,
      "name": "Pink",
      "color": "pink",
      "is_impostor": true,
      "is_alive": true,
      "votes_received": 0
    }
  ],
  "impostor_revealed": "Pink is the impostor!",
  "meeting_trigger": "dead_body",
  "reporter_name": "Blue",
  "meeting_reason": "Blue found Purple's body in Electrical"
}
```

**Save the `game_id` for subsequent requests!**

### 2. Advance Game Step

**Endpoint**: `POST /impostor-game/step/{game_id}`

#### Using curl:
```bash
# Replace {game_id} with actual game ID from init response
curl -X POST http://localhost:8000/impostor-game/step/123e4567-e89b-12d3-a456-426614174000 \
  -H "Content-Type: application/json"
```

#### Using HTTPie:
```bash
http POST localhost:8000/impostor-game/step/123e4567-e89b-12d3-a456-426614174000
```

#### Expected Response:
```json
{
  "game_id": "123e4567-e89b-12d3-a456-426614174000",
  "phase": "active",
  "step_number": 1,
  "max_steps": 30,
  "turns": [
    {
      "agent_id": 0,
      "think": "I need to analyze who seems suspicious based on their behavior...",
      "speak": "I was in Navigation doing my tasks. Where was everyone else?",
      "vote": null
    },
    {
      "agent_id": 1,
      "think": "I should deflect suspicion and blend in with the crewmates...",
      "speak": "I was in Cafeteria. Pink seemed to be acting strange earlier.",
      "vote": 3
    }
  ],
  "eliminated": null,
  "winner": null,
  "game_over": false,
  "message": "Discussion round 1 completed. No elimination this round."
}
```

### 3. Get Game State

**Endpoint**: `GET /impostor-game/game/{game_id}`

#### Using curl:
```bash
curl http://localhost:8000/impostor-game/game/123e4567-e89b-12d3-a456-426614174000
```

#### Using HTTPie:
```bash
http GET localhost:8000/impostor-game/game/123e4567-e89b-12d3-a456-426614174000
```

#### Expected Response:
```json
{
  "game_id": "123e4567-e89b-12d3-a456-426614174000",
  "status": "active",
  "phase": "active",
  "step_number": 1,
  "max_steps": 30,
  "agents": [
    {
      "id": 0,
      "name": "Red",
      "color": "red",
      "is_impostor": false,
      "is_alive": true,
      "votes_received": 0
    }
  ],
  "public_action_history": [
    {
      "agent_id": 0,
      "action_type": "speak",
      "content": "I was in Navigation doing my tasks. Where was everyone else?",
      "target_agent_id": null
    }
  ],
  "current_votes": {
    "3": 1
  },
  "winner": null,
  "alive_count": 8,
  "impostor_alive": true
}
```

### 4. Health Check

**Endpoint**: `GET /impostor-game/health`

#### Using curl:
```bash
curl http://localhost:8000/impostor-game/health
```

Expected response:
```json
{
  "status": "healthy",
  "message": "Impostor game service is running"
}
```

## Complete Game Testing Workflow

### Full Game Test Script (Bash)

```bash
#!/bin/bash

# 1. Initialize game
echo "🚀 Initializing new game..."
RESPONSE=$(curl -s -X POST http://localhost:8000/impostor-game/init)
GAME_ID=$(echo $RESPONSE | jq -r '.game_id')
echo "Game ID: $GAME_ID"
echo "Impostor: $(echo $RESPONSE | jq -r '.impostor_revealed')"
echo "Meeting: $(echo $RESPONSE | jq -r '.meeting_reason')"
echo ""

# 2. Play several rounds
for i in {1..5}; do
    echo "🎮 Step $i..."
    STEP_RESPONSE=$(curl -s -X POST http://localhost:8000/impostor-game/step/$GAME_ID)
    
    ELIMINATED=$(echo $STEP_RESPONSE | jq -r '.eliminated')
    WINNER=$(echo $STEP_RESPONSE | jq -r '.winner')
    GAME_OVER=$(echo $STEP_RESPONSE | jq -r '.game_over')
    
    echo "Message: $(echo $STEP_RESPONSE | jq -r '.message')"
    
    if [ "$ELIMINATED" != "null" ]; then
        echo "❌ Eliminated: $ELIMINATED"
    fi
    
    if [ "$GAME_OVER" = "true" ]; then
        echo "🏆 Game Over! Winner: $WINNER"
        break
    fi
    
    echo ""
    sleep 2
done

# 3. Final game state
echo "📊 Final game state..."
curl -s http://localhost:8000/impostor-game/game/$GAME_ID | jq
```

### Python Test Script

```python
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_complete_game():
    # 1. Initialize game
    print("🚀 Initializing new game...")
    response = requests.post(f"{BASE_URL}/impostor-game/init")
    game_data = response.json()
    
    game_id = game_data["game_id"]
    print(f"Game ID: {game_id}")
    print(f"Impostor: {game_data['impostor_revealed']}")
    print(f"Meeting: {game_data['meeting_reason']}")
    print()
    
    # 2. Play game steps
    for step in range(1, 11):
        print(f"🎮 Step {step}...")
        response = requests.post(f"{BASE_URL}/impostor-game/step/{game_id}")
        step_data = response.json()
        
        print(f"Message: {step_data['message']}")
        
        if step_data.get('eliminated'):
            print(f"❌ Eliminated: {step_data['eliminated']}")
        
        if step_data['game_over']:
            print(f"🏆 Game Over! Winner: {step_data['winner']}")
            break
        
        print()
        time.sleep(1)
    
    # 3. Final state
    print("📊 Final game state...")
    response = requests.get(f"{BASE_URL}/impostor-game/game/{game_id}")
    final_state = response.json()
    print(json.dumps(final_state, indent=2))

if __name__ == "__main__":
    test_complete_game()
```

## Testing with Postman

### Collection Setup

1. **Create Collection**: "AI Impostor Game"
2. **Add Environment Variables**:
   - `base_url`: `http://localhost:8000`
   - `game_id`: (will be set from init response)

### Request Configuration

#### 1. Init Game
- **Method**: POST
- **URL**: `{{base_url}}/impostor-game/init`
- **Headers**: `Content-Type: application/json`
- **Test Script**:
```javascript
pm.test("Game initialized", function () {
    pm.response.to.have.status(200);
    var jsonData = pm.response.json();
    pm.expect(jsonData).to.have.property('game_id');
    pm.environment.set("game_id", jsonData.game_id);
});
```

#### 2. Step Game
- **Method**: POST
- **URL**: `{{base_url}}/impostor-game/step/{{game_id}}`
- **Headers**: `Content-Type: application/json`

#### 3. Get State
- **Method**: GET
- **URL**: `{{base_url}}/impostor-game/game/{{game_id}}`

## Browser Testing

### Using FastAPI Docs

1. **Navigate to**: `http://localhost:8000/docs`
2. **Interactive API**: Test all endpoints with built-in Swagger UI
3. **Real-time Testing**: Execute requests and see responses immediately

### Manual Browser Testing

Access endpoints directly:
- Health: `http://localhost:8000/impostor-game/health`
- Root: `http://localhost:8000/`

## Common Error Scenarios

### Error Responses to Test

#### 1. Invalid Game ID
```bash
curl http://localhost:8000/impostor-game/game/invalid-id
```

Expected: `404 Not Found`

#### 2. Game Already Finished
```bash
# After game ends, try to advance step
curl -X POST http://localhost:8000/impostor-game/step/{finished_game_id}
```

Expected: `400 Bad Request`

#### 3. Missing API Key
Remove `CEREBRAS_API_KEY` from environment and restart server.

Expected: AI responses will show error messages.

## Performance Testing

### Load Testing with curl

```bash
# Test multiple concurrent games
for i in {1..10}; do
    curl -X POST http://localhost:8000/impostor-game/init &
done
wait
```

### Response Time Monitoring

```bash
# Measure response times
time curl -X POST http://localhost:8000/impostor-game/init
```

## Debugging Tips

### Verbose Output
```bash
# Add -v flag for detailed request/response info
curl -v -X POST http://localhost:8000/impostor-game/init
```

### JSON Pretty Printing
```bash
# Use jq for formatted JSON output
curl http://localhost:8000/impostor-game/health | jq
```

### Save Responses
```bash
# Save response to file for analysis
curl http://localhost:8000/impostor-game/init > game_response.json
```

## Test Data Examples

### Expected Agent Behaviors

**Crewmate Speech Patterns**:
- Ask questions about locations
- Share alibis
- Analyze suspicious behavior
- Vote based on logic

**Impostor Speech Patterns**:
- Deflect suspicion
- Blend in with group
- Provide false alibis
- Strategic voting

### Game Progression Patterns

1. **Early Game**: Information gathering, cautious statements
2. **Mid Game**: Accusations, vote clustering
3. **Late Game**: Decisive voting, elimination pressure

This comprehensive testing guide ensures thorough validation of all API functionality and game mechanics.