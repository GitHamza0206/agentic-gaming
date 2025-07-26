# AI Impostor Game - Test Suite

Comprehensive test suite for the AI Impostor Game backend, focusing on the enhanced memory system for agents.

## Test Structure

### 🧠 Memory System Tests (`test_memory_system.py`)
- **Agent Memory Creation**: Test agent initialization with empty memory
- **Memory Structure**: Validate `AgentMemory` model fields and types
- **Memory Formatting**: Test memory context formatting for LLM prompts
- **Memory Limits**: Ensure only last 3 steps shown in context
- **Memory Integration**: Test memory parsing from LLM responses
- **Memory Accumulation**: Verify memory persists across game steps
- **Impostor Memory**: Test impostor-specific memory functionality

### 🎮 Game Service Tests (`test_game_service.py`)
- **Game Creation**: Test game initialization with agent memory setup
- **Step Processing**: Test memory creation and storage during game steps
- **Memory Persistence**: Verify memory accumulates across multiple steps
- **Game State**: Test memory inclusion in game state responses
- **Complete Game Flow**: End-to-end testing with memory throughout

### 🌐 API Integration Tests (`test_api_endpoints.py`)
- **Health Endpoint**: Basic API health check
- **Init Endpoint**: Test game creation via API with memory
- **Step Endpoint**: Test step execution via API with memory updates
- **Game State Endpoint**: Test memory retrieval via API
- **Error Handling**: Test invalid game IDs and error responses
- **Memory Accumulation**: Test memory across multiple API calls
- **Role-Specific Memory**: Test impostor vs crewmate memory differences

## Running Tests

### Prerequisites
```bash
# Install test dependencies
pip install -r tests/requirements.txt

# Or install from main requirements (includes testing packages)
pip install -r requirements.txt
```

### Run All Tests
```bash
# From backend directory
cd backend

# Run all tests
pytest tests/

# Run with verbose output
pytest -v tests/

# Run with coverage
pytest --cov=src tests/
```

### Run Specific Test Files
```bash
# Memory system tests only
pytest tests/test_memory_system.py

# Game service tests only
pytest tests/test_game_service.py

# API tests only
pytest tests/test_api_endpoints.py
```

### Run Specific Test Classes
```bash
# Test only agent memory functionality
pytest tests/test_memory_system.py::TestAgentMemory

# Test only memory integration
pytest tests/test_memory_system.py::TestMemoryIntegration

# Test only API endpoints
pytest tests/test_api_endpoints.py::TestAPIEndpoints
```

### Run Specific Test Methods
```bash
# Test specific memory feature
pytest tests/test_memory_system.py::TestAgentMemory::test_memory_structure

# Test specific API endpoint
pytest tests/test_api_endpoints.py::TestAPIEndpoints::test_init_game_endpoint
```

## Test Coverage

The test suite covers:

### ✅ Core Memory Features
- [x] Agent memory initialization
- [x] Memory structure validation
- [x] Memory context formatting
- [x] Memory parsing from LLM responses
- [x] Memory accumulation across steps
- [x] Memory limits and cleanup
- [x] Fallback memory creation

### ✅ Game Integration
- [x] Memory in game creation
- [x] Memory in step processing
- [x] Memory in game state retrieval
- [x] Memory persistence across game lifecycle
- [x] Role-specific memory differences

### ✅ API Integration
- [x] Memory in API responses
- [x] Memory through complete API workflow
- [x] Error handling with memory
- [x] Multi-step memory accumulation via API

### ✅ Edge Cases
- [x] Invalid LLM responses
- [x] Missing memory fields
- [x] Empty memory history
- [x] Invalid game states
- [x] Network/parsing errors

## Mock Strategy

Tests use Python's `unittest.mock` to:
- **Mock LLM Client**: Avoid actual API calls during testing
- **Control Responses**: Test specific memory scenarios
- **Simulate Errors**: Test error handling and fallbacks
- **Isolate Components**: Test memory system independently

## Test Data Patterns

### Memory Test Patterns
```python
# Standard memory structure
memory = AgentMemory(
    step_number=1,
    observations=["Agent acting suspicious"],
    suspicions={2: "near body location"},
    alliances=[1, 3],
    strategy_notes="Focus on agent 2",
    emotion_state="alert"
)

# LLM response with memory
mock_response = '''
{
    "think": "Analyzing the situation",
    "speak": "I saw something suspicious",
    "vote": 2,
    "memory_update": {
        "step_number": 1,
        "observations": ["Test observation"],
        "emotion_state": "suspicious"
    }
}
'''
```

### Game Flow Test Patterns
```python
# Multi-step memory accumulation
for step in range(1, 4):
    mock_responses = create_step_responses(step)
    mock_llm.side_effect = mock_responses
    service.process_step(game_id)
    
# Verify memory growth
assert len(agent.memory_history) == 3
```

## Debugging Tests

### Verbose Output
```bash
# See detailed test output
pytest -v -s tests/

# See print statements in tests
pytest -s tests/test_memory_system.py
```

### Failed Test Analysis
```bash
# Stop on first failure
pytest -x tests/

# Show local variables in traceback
pytest --tb=long tests/

# Run only failed tests from last run
pytest --lf tests/
```

### Coverage Reports
```bash
# Generate coverage report
pytest --cov=src --cov-report=html tests/

# View coverage in browser
open htmlcov/index.html
```

## Continuous Integration

These tests are designed to run in CI/CD pipelines:
- No external dependencies (uses mocks)
- Fast execution (< 30 seconds)
- Comprehensive coverage (>90% target)
- Clear failure messages

## Contributing

When adding new memory features:
1. **Add tests first** (TDD approach)
2. **Test both success and failure cases**
3. **Mock external dependencies**
4. **Update this README** with new test coverage
5. **Ensure >90% coverage** for new code

Example test structure:
```python
def test_new_memory_feature(self):
    """Test description of what this validates"""
    # Arrange
    setup_test_data()
    
    # Act
    result = execute_feature()
    
    # Assert
    assert expected_behavior(result)
```