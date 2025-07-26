import pytest
import sys
import os
from fastapi.testclient import TestClient

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from main import app
from unittest.mock import patch

class TestAPIEndpoints:
    """Test API endpoints with memory functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    def test_health_endpoint(self):
        """Test health check endpoint"""
        response = self.client.get("/impostor-game/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
    
    def test_init_game_endpoint(self):
        """Test game initialization endpoint"""
        response = self.client.post("/impostor-game/init")
        assert response.status_code == 200
        
        data = response.json()
        assert "game_id" in data
        assert "agents" in data
        assert len(data["agents"]) == 8
        assert "impostor_revealed" in data
        
        # Check that agents have empty memory initially
        for agent in data["agents"]:
            assert "memory_history" in agent
            assert len(agent["memory_history"]) == 0
    
    @patch('src.core.llm_client.LLMClient.generate_response')
    def test_step_endpoint_with_memory(self, mock_llm):
        """Test step endpoint creates and returns memory"""
        # First create a game
        init_response = self.client.post("/impostor-game/init")
        game_id = init_response.json()["game_id"]
        
        # Mock LLM responses with memory
        mock_responses = []
        for i in range(8):
            mock_responses.append(f'''
            {{
                "think": "Agent {i} analyzing the situation",
                "speak": "Agent {i} speaking publicly",
                "memory_update": {{
                    "step_number": 1,
                    "observations": ["Observation from agent {i}"],
                    "strategy_notes": "Strategy for agent {i}",
                    "emotion_state": "alert"
                }}
            }}
            ''')
        
        mock_llm.side_effect = mock_responses
        
        # Execute step
        response = self.client.post(f"/impostor-game/step/{game_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["step_number"] == 1
        assert "turns" in data
        assert len(data["turns"]) == 8
        
        # Check that turns include memory updates
        for turn in data["turns"]:
            assert "memory_update" in turn
            if turn["memory_update"]:
                memory = turn["memory_update"]
                assert memory["step_number"] == 1
                assert len(memory["observations"]) > 0
                assert memory["emotion_state"] == "alert"
    
    @patch('src.core.llm_client.LLMClient.generate_response')
    def test_game_state_endpoint_with_memory(self, mock_llm):
        """Test game state endpoint returns agent memory"""
        # Create game and execute one step
        init_response = self.client.post("/impostor-game/init")
        game_id = init_response.json()["game_id"]
        
        # Mock responses
        mock_responses = [f'''
        {{
            "think": "Thinking step 1",
            "memory_update": {{
                "step_number": 1,
                "observations": ["Test observation {i}"],
                "emotion_state": "neutral"
            }}
        }}
        ''' for i in range(8)]
        
        mock_llm.side_effect = mock_responses
        
        # Execute step
        self.client.post(f"/impostor-game/step/{game_id}")
        
        # Get game state
        response = self.client.get(f"/impostor-game/game/{game_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert "agents" in data
        
        # Check that agents have memory
        print(f"Total agents: {len(data['agents'])}")
        agents_with_memory = 0
        for agent in data["agents"]:
            print(f"Agent {agent['name']} (ID {agent['id']}): memory_length={len(agent.get('memory_history', []))}")
            if agent.get('memory_history') and len(agent['memory_history']) > 0:
                agents_with_memory += 1
                
        print(f"Agents with memory: {agents_with_memory}")
        
        # Check that all agents have memory (including reporter)
        for agent in data["agents"]:
            assert "memory_history" in agent
            if len(agent["memory_history"]) > 0:
                memory = agent["memory_history"][0]
                assert memory["step_number"] == 1
                assert len(memory["observations"]) > 0
                assert memory["emotion_state"] == "neutral"
        
        # Should have 8 agents with memory (all agents including reporter)
        assert agents_with_memory == 8
    
    def test_invalid_game_id(self):
        """Test endpoints with invalid game ID"""
        invalid_id = "invalid-game-id"
        
        # Test step endpoint
        response = self.client.post(f"/impostor-game/step/{invalid_id}")
        assert response.status_code == 404
        
        # Test game state endpoint
        response = self.client.get(f"/impostor-game/game/{invalid_id}")
        assert response.status_code == 404
    
    @patch('src.core.llm_client.LLMClient.generate_response')
    def test_multiple_steps_memory_accumulation(self, mock_llm):
        """Test that memory accumulates across multiple API calls"""
        # Create game
        init_response = self.client.post("/impostor-game/init")
        game_id = init_response.json()["game_id"]
        
        # Mock responses for 2 steps
        step1_responses = [f'''
        {{
            "think": "Step 1 thinking",
            "memory_update": {{
                "step_number": 1,
                "observations": ["Step 1 observation {i}"],
                "emotion_state": "neutral"
            }}
        }}
        ''' for i in range(8)]
        
        step2_responses = [f'''
        {{
            "think": "Step 2 thinking",
            "memory_update": {{
                "step_number": 2,
                "observations": ["Step 2 observation {i}"],
                "emotion_state": "suspicious"
            }}
        }}
        ''' for i in range(8)]
        
        mock_llm.side_effect = step1_responses + step2_responses
        
        # Execute two steps
        step1_response = self.client.post(f"/impostor-game/step/{game_id}")
        step2_response = self.client.post(f"/impostor-game/step/{game_id}")
        
        assert step1_response.json()["step_number"] == 1
        assert step2_response.json()["step_number"] == 2
        
        # Check final game state
        state_response = self.client.get(f"/impostor-game/game/{game_id}")
        data = state_response.json()
        
        # Verify memory accumulation
        for agent in data["agents"]:
            assert len(agent["memory_history"]) == 2
            
            # Check step 1 memory
            memory1 = agent["memory_history"][0]
            assert memory1["step_number"] == 1
            assert memory1["emotion_state"] == "neutral"
            
            # Check step 2 memory
            memory2 = agent["memory_history"][1]
            assert memory2["step_number"] == 2
            assert memory2["emotion_state"] == "suspicious"

class TestMemoryAPIIntegration:
    """Integration tests for memory system through API"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.client = TestClient(app)
    
    @patch('src.core.llm_client.LLMClient.generate_response')
    def test_impostor_vs_crewmate_memory(self, mock_llm):
        """Test that impostor and crewmate memory differs appropriately"""
        # Create game
        init_response = self.client.post("/impostor-game/init")
        game_data = init_response.json()
        game_id = game_data["game_id"]
        
        # Find impostor ID directly from agents
        impostor_id = None
        for agent in game_data["agents"]:
            if agent["is_impostor"]:
                impostor_id = agent["id"]
                break
        
        # Mock different responses for impostor vs crewmates
        mock_responses = []
        for agent in game_data["agents"]:
            if agent["is_impostor"]:
                mock_responses.append('''
                {
                    "think": "I need to deflect suspicion and blend in",
                    "speak": "I was doing tasks in Navigation",
                    "memory_update": {
                        "step_number": 1,
                        "observations": ["Crewmates are getting suspicious"],
                        "strategy_notes": "Act innocent, blame others",
                        "emotion_state": "nervous"
                    }
                }
                ''')
            else:
                mock_responses.append(f'''
                {{
                    "think": "Looking for the impostor among us",
                    "speak": "Has anyone seen anything suspicious?",
                    "memory_update": {{
                        "step_number": 1,
                        "observations": ["Agent {impostor_id} acting strange"],
                        "suspicions": {{"{impostor_id}": "nervous behavior"}},
                        "strategy_notes": "Watch agent {impostor_id}",
                        "emotion_state": "alert"
                    }}
                }}
                ''')
        
        mock_llm.side_effect = mock_responses
        
        # Execute step
        self.client.post(f"/impostor-game/step/{game_id}")
        
        # Get final state
        state_response = self.client.get(f"/impostor-game/game/{game_id}")
        data = state_response.json()
        
        # Check impostor vs crewmate memory differences
        for agent in data["agents"]:
            memory = agent["memory_history"][0]
            
            if agent["is_impostor"]:
                assert "nervous" in memory["emotion_state"]
                assert "blame others" in memory["strategy_notes"]
                assert "Crewmates are getting suspicious" in memory["observations"]
            else:
                assert "alert" in memory["emotion_state"]
                assert str(impostor_id) in str(memory.get("suspicions", {}))
                assert f"Agent {impostor_id}" in memory["observations"][0]

if __name__ == "__main__":
    pytest.main([__file__])