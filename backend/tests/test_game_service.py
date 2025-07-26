import pytest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features.impostor_game.service import ImpostorGameService
from features.impostor_game.schema import GameStatus, GamePhase
from unittest.mock import Mock, patch

class TestImpostorGameService:
    """Test the game service with memory functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ImpostorGameService()
    
    def test_game_creation_with_memory(self):
        """Test that new games create agents with empty memory"""
        response = self.service.create_game()
        
        assert response.game_id is not None
        assert len(response.agents) == 8
        
        # Check that all agents have empty memory initially
        for agent in response.agents:
            assert len(agent.memory_history) == 0
    
    @patch('src.core.llm_client.LLMClient.generate_response')
    def test_game_step_with_memory(self, mock_llm):
        """Test that game steps create and store memory"""
        # Create a game
        init_response = self.service.create_game()
        game_id = init_response.game_id
        
        # Mock LLM responses with memory for all agents
        mock_responses = []
        for i in range(8):
            mock_responses.append(f'''
            {{
                "think": "Agent {i} thinking about the situation",
                "speak": "Agent {i} speaking",
                "memory_update": {{
                    "step_number": 1,
                    "observations": ["Step 1 observation for agent {i}"],
                    "emotion_state": "neutral",
                    "strategy_notes": "Agent {i} strategy"
                }}
            }}
            ''')
        
        mock_llm.side_effect = mock_responses
        
        # Execute one step
        step_response = self.service.step_game(game_id)
        
        assert step_response.step_number == 1
        assert len(step_response.turns) == 8
        
        # Check that each agent now has memory
        game_state = self.service.games[game_id]
        for agent in game_state.agents:
            assert len(agent.memory_history) == 1
            memory = agent.memory_history[0]
            assert memory.step_number == 1
            assert f"Step 1 observation for agent {agent.id}" in memory.observations
            assert f"Agent {agent.id} strategy" in memory.strategy_notes
    
    @patch('src.core.llm_client.LLMClient.generate_response')
    def test_memory_persistence_across_steps(self, mock_llm):
        """Test that memory persists and accumulates across multiple steps"""
        # Create a game
        init_response = self.service.create_game()
        game_id = init_response.game_id
        
        # Mock responses for 2 steps
        step1_responses = [f'''
        {{
            "think": "Step 1 thinking for agent {i}",
            "memory_update": {{
                "step_number": 1,
                "observations": ["Step 1 obs {i}"],
                "emotion_state": "neutral"
            }}
        }}
        ''' for i in range(8)]
        
        step2_responses = [f'''
        {{
            "think": "Step 2 thinking for agent {i}",
            "memory_update": {{
                "step_number": 2,
                "observations": ["Step 2 obs {i}"],
                "emotion_state": "suspicious"
            }}
        }}
        ''' for i in range(8)]
        
        mock_llm.side_effect = step1_responses + step2_responses
        
        # Execute two steps
        step1_response = self.service.process_step(game_id)
        step2_response = self.service.process_step(game_id)
        
        assert step1_response.step_number == 1
        assert step2_response.step_number == 2
        
        # Check memory accumulation
        game_state = self.service.games[game_id]
        for agent in game_state.agents:
            assert len(agent.memory_history) == 2
            
            # Check first memory
            memory1 = agent.memory_history[0]
            assert memory1.step_number == 1
            assert f"Step 1 obs {agent.id}" in memory1.observations
            assert memory1.emotion_state == "neutral"
            
            # Check second memory
            memory2 = agent.memory_history[1]
            assert memory2.step_number == 2
            assert f"Step 2 obs {agent.id}" in memory2.observations
            assert memory2.emotion_state == "suspicious"
    
    def test_memory_in_game_state_response(self):
        """Test that memory is included in game state responses"""
        # Create a game
        init_response = self.service.create_game()
        game_id = init_response.game_id
        
        # Add some memory manually for testing
        game_state = self.service.games[game_id]
        from features.impostor_game.schema import AgentMemory
        
        test_memory = AgentMemory(
            step_number=1,
            observations=["Test observation"],
            suspicions={1: "Test suspicion"},
            strategy_notes="Test strategy",
            emotion_state="test_emotion"
        )
        
        game_state.agents[0].memory_history.append(test_memory)
        
        # Get game state
        response = self.service.get_game_state_response(game_id)
        
        # Check that memory is included
        agent_with_memory = response.agents[0]
        assert len(agent_with_memory.memory_history) == 1
        memory = agent_with_memory.memory_history[0]
        assert memory.step_number == 1
        assert "Test observation" in memory.observations
        assert memory.suspicions[1] == "Test suspicion"
        assert memory.strategy_notes == "Test strategy"
        assert memory.emotion_state == "test_emotion"

class TestMemoryGameFlow:
    """Test complete game flow with memory system"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.service = ImpostorGameService()
    
    @patch('src.core.llm_client.LLMClient.generate_response')
    def test_complete_game_with_memory(self, mock_llm):
        """Test a complete game flow ensuring memory works throughout"""
        # Create game
        init_response = self.service.create_game()
        game_id = init_response.game_id
        impostor_id = init_response.impostor_revealed.split()[0]  # Extract impostor name
        
        # Find the actual impostor agent
        game_state = self.service.games[game_id]
        impostor_agent = None
        for agent in game_state.agents:
            if agent.is_impostor:
                impostor_agent = agent
                break
        
        # Mock responses for multiple steps with evolving memory
        def create_response(agent_id, step, is_impostor=False):
            if is_impostor:
                return f'''
                {{
                    "think": "I need to blend in and deflect suspicion",
                    "speak": "I was doing tasks in Navigation",
                    "memory_update": {{
                        "step_number": {step},
                        "observations": ["Crewmates getting suspicious"],
                        "strategy_notes": "Deflect to others, act innocent",
                        "emotion_state": "nervous"
                    }}
                }}
                '''
            else:
                return f'''
                {{
                    "think": "Looking for suspicious behavior from others",
                    "speak": "Has anyone seen anything suspicious?",
                    "vote": {impostor_agent.id if step > 2 else "null"},
                    "memory_update": {{
                        "step_number": {step},
                        "observations": ["Agent {impostor_agent.id} seems nervous"],
                        "suspicions": {{"{impostor_agent.id}": "acting strange"}},
                        "strategy_notes": "Watch agent {impostor_agent.id}",
                        "emotion_state": "suspicious"
                    }}
                }}
                '''
        
        # Generate responses for 3 steps
        all_responses = []
        for step in range(1, 4):
            for agent in game_state.agents:
                response = create_response(agent.id, step, agent.is_impostor)
                all_responses.append(response)
        
        mock_llm.side_effect = all_responses
        
        # Execute 3 steps
        responses = []
        for step in range(3):
            response = self.service.step_game(game_id)
            responses.append(response)
            
            # Verify step progression
            assert response.step_number == step + 1
            assert len(response.turns) == 8  # All agents participate
        
        # Check final game state
        final_state = self.service.get_game_state_response(game_id)
        
        # Verify memory accumulation
        for agent in final_state.agents:
            assert len(agent.memory_history) == 3  # 3 steps of memory
            
            # Check memory progression
            for i, memory in enumerate(agent.memory_history):
                assert memory.step_number == i + 1
                
                if agent.is_impostor:
                    assert "nervous" in memory.emotion_state
                    assert "Deflect to others" in memory.strategy_notes
                else:
                    assert "suspicious" in memory.emotion_state
                    assert str(impostor_agent.id) in str(memory.suspicions)
        
        # Check that voting occurred in later steps
        step3_response = responses[2]
        votes_cast = sum(1 for turn in step3_response.turns if turn.vote is not None)
        assert votes_cast > 0  # At least some agents voted

if __name__ == "__main__":
    pytest.main([__file__])