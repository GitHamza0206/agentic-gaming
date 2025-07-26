import pytest
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from features.impostor_game.schema import Agent, AgentMemory, AgentTurn
from features.impostor_game.agents import Crewmate, Impostor
from unittest.mock import Mock

class TestAgentMemory:
    """Test the enhanced memory system for agents"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent_data = Agent(id=0, name="Red", color="red", is_impostor=False)
        self.mock_llm = Mock()
        self.crewmate = Crewmate(self.agent_data, self.mock_llm)
    
    def test_agent_memory_creation(self):
        """Test that agents can be created with empty memory"""
        assert len(self.agent_data.memory_history) == 0
        assert self.agent_data.name == "Red"
        assert self.agent_data.is_impostor == False
    
    def test_memory_structure(self):
        """Test that AgentMemory has all required fields"""
        memory = AgentMemory(
            step_number=1,
            observations=["Blue acted suspicious"],
            suspicions={2: "Blue was near the body"},
            alliances=[1, 3],
            strategy_notes="Focus on Blue",
            emotion_state="suspicious"
        )
        
        assert memory.step_number == 1
        assert "Blue acted suspicious" in memory.observations
        assert memory.suspicions[2] == "Blue was near the body"
        assert 1 in memory.alliances
        assert memory.strategy_notes == "Focus on Blue"
        assert memory.emotion_state == "suspicious"
    
    def test_memory_formatting(self):
        """Test that memory context is formatted correctly"""
        # Add some memory to the agent
        memory1 = AgentMemory(
            step_number=1,
            observations=["Blue acted suspicious"],
            suspicions={2: "near body"},
            alliances=[1],
            strategy_notes="Watch Blue",
            emotion_state="alert"
        )
        memory2 = AgentMemory(
            step_number=2,
            observations=["Green defended Blue"],
            suspicions={2: "still suspicious", 3: "might be allied"},
            alliances=[1],
            strategy_notes="Blue and Green might be team",
            emotion_state="concerned"
        )
        
        self.agent_data.memory_history = [memory1, memory2]
        
        formatted = self.crewmate._format_memory_context()
        
        assert "Step 1:" in formatted
        assert "Step 2:" in formatted
        assert "Blue acted suspicious" in formatted
        assert "Agent2: near body" in formatted
        assert "alert" in formatted
        assert "concerned" in formatted
    
    def test_memory_limit(self):
        """Test that memory formatting only shows last 3 steps"""
        # Add 5 memories
        for i in range(5):
            memory = AgentMemory(
                step_number=i+1,
                observations=[f"Observation {i+1}"],
                emotion_state="neutral"
            )
            self.agent_data.memory_history.append(memory)
        
        formatted = self.crewmate._format_memory_context()
        
        # Should only show steps 3, 4, 5
        assert "Step 3:" in formatted
        assert "Step 4:" in formatted  
        assert "Step 5:" in formatted
        assert "Step 1:" not in formatted
        assert "Step 2:" not in formatted
    
    def test_empty_memory_formatting(self):
        """Test memory formatting when no memories exist"""
        formatted = self.crewmate._format_memory_context()
        assert formatted == "No previous memories."
    
    def test_memory_in_agent_turn(self):
        """Test that AgentTurn can include memory updates"""
        memory = AgentMemory(
            step_number=1,
            observations=["Test observation"],
            emotion_state="neutral"
        )
        
        turn = AgentTurn(
            agent_id=0,
            think="I'm thinking...",
            speak="I have something to say",
            vote=2,
            memory_update=memory
        )
        
        assert turn.memory_update is not None
        assert turn.memory_update.step_number == 1
        assert "Test observation" in turn.memory_update.observations

class TestMemoryIntegration:
    """Test memory system integration with game flow"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent_data = Agent(id=0, name="Red", color="red", is_impostor=False)
        self.mock_llm = Mock()
        self.crewmate = Crewmate(self.agent_data, self.mock_llm)
    
    def test_memory_parsing_success(self):
        """Test successful parsing of memory from LLM response"""
        # Mock LLM response with memory
        mock_response = '''
        {
            "think": "I need to analyze the situation carefully",
            "speak": "I was in Navigation doing tasks",
            "vote": null,
            "memory_update": {
                "step_number": 1,
                "observations": ["Blue was acting suspicious"],
                "suspicions": {"2": "Blue near body"},
                "alliances": [1, 3],
                "strategy_notes": "Focus on Blue",
                "emotion_state": "alert"
            }
        }
        '''
        
        self.mock_llm.generate_response.return_value = mock_response
        
        # Call choose_action (this will parse the response)
        turn = self.crewmate.choose_action("Test context", [], [], 1)
        
        # Check that memory was added to agent
        assert len(self.agent_data.memory_history) == 1
        memory = self.agent_data.memory_history[0]
        assert memory.step_number == 1
        assert "Blue was acting suspicious" in memory.observations
        assert memory.suspicions[2] == "Blue near body"
        assert 1 in memory.alliances
        assert memory.strategy_notes == "Focus on Blue"
        assert memory.emotion_state == "alert"
        
        # Check turn response
        assert turn.memory_update is not None
        assert turn.think == "I need to analyze the situation carefully"
        assert turn.speak == "I was in Navigation doing tasks"
        assert turn.vote is None
    
    def test_memory_parsing_fallback(self):
        """Test fallback memory creation when parsing fails"""
        # Mock LLM response that will fail parsing
        mock_response = "Invalid JSON response"
        
        self.mock_llm.generate_response.return_value = mock_response
        
        # Call choose_action
        turn = self.crewmate.choose_action("Test context", [], [], 1)
        
        # Check that fallback memory was created
        assert len(self.agent_data.memory_history) == 1
        memory = self.agent_data.memory_history[0]
        assert memory.step_number == 1
        assert "Failed to parse response properly" in memory.observations
        assert memory.emotion_state == "confused"
        
        # Check turn response
        assert turn.memory_update is not None
        assert "Invalid JSON response" in turn.think
    
    def test_memory_accumulation(self):
        """Test that memory accumulates across multiple steps"""
        # First step
        mock_response1 = '''
        {
            "think": "Step 1 thinking",
            "memory_update": {
                "step_number": 1,
                "observations": ["First observation"],
                "emotion_state": "neutral"
            }
        }
        '''
        
        # Second step  
        mock_response2 = '''
        {
            "think": "Step 2 thinking",
            "memory_update": {
                "step_number": 2,
                "observations": ["Second observation"],
                "emotion_state": "suspicious"
            }
        }
        '''
        
        self.mock_llm.generate_response.side_effect = [mock_response1, mock_response2]
        
        # Execute two steps
        turn1 = self.crewmate.choose_action("Context 1", [], [], 1)
        turn2 = self.crewmate.choose_action("Context 2", [], [], 2)
        
        # Check that both memories are stored
        assert len(self.agent_data.memory_history) == 2
        assert self.agent_data.memory_history[0].step_number == 1
        assert self.agent_data.memory_history[1].step_number == 2
        assert "First observation" in self.agent_data.memory_history[0].observations
        assert "Second observation" in self.agent_data.memory_history[1].observations

class TestImpostorMemory:
    """Test memory system for impostor agents"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.agent_data = Agent(id=0, name="Red", color="red", is_impostor=True)
        self.mock_llm = Mock()
        self.impostor = Impostor(self.agent_data, self.mock_llm)
    
    def test_impostor_memory_functionality(self):
        """Test that impostor agents can use memory system"""
        mock_response = '''
        {
            "think": "I need to deflect suspicion",
            "speak": "I was doing tasks in Cafeteria",
            "memory_update": {
                "step_number": 1,
                "observations": ["Crewmates are suspicious of me"],
                "strategy_notes": "Act innocent, blame others",
                "emotion_state": "nervous"
            }
        }
        '''
        
        self.mock_llm.generate_response.return_value = mock_response
        
        turn = self.impostor.choose_action("Test context", [], [], 1)
        
        # Check impostor-specific memory
        assert len(self.agent_data.memory_history) == 1
        memory = self.agent_data.memory_history[0]
        assert "Crewmates are suspicious of me" in memory.observations
        assert "Act innocent, blame others" in memory.strategy_notes
        assert memory.emotion_state == "nervous"

if __name__ == "__main__":
    pytest.main([__file__])