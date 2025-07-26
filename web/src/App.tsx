import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';

interface Agent {
  id: number;
  name: string;
  color: string;
  is_impostor: boolean;
  is_alive: boolean;
}

interface AgentAction {
  agent_id: number;
  action_type: string;
  content: string;
  target_agent_id?: number;
}

interface AgentTurn {
  agent_id: number;
  think: string;
  speak?: string;
  vote?: number;
}

interface GameData {
  game_id: string;
  agents: Agent[];
  conversation_history: AgentAction[];
  step_number: number;
  max_steps: number;
  game_over: boolean;
  winner?: string;
  message: string;
}

const AmongUsSimulation = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [phase, setPhase] = useState('simulation');
  const [gameData, setGameData] = useState<GameData | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // API Configuration
  const API_BASE = 'http://localhost:8000';

  // Initialize game
  const initializeGame = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE}/impostor-game/init?num_players=4`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setGameData({
        game_id: data.game_id,
        agents: data.agents,
        conversation_history: [],
        step_number: 0,
        max_steps: 30,
        game_over: false,
        message: data.message
      });
      setPhase('simulation');
      setCurrentStep(0);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to initialize game');
    } finally {
      setLoading(false);
    }
  };

  // Step game forward
  const stepGame = async () => {
    if (!gameData) return;
    
    try {
      setLoading(true);
      const response = await fetch(`${API_BASE}/impostor-game/step/${gameData.game_id}`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      const data = await response.json();
      setGameData({
        ...gameData,
        conversation_history: data.conversation_history,
        step_number: data.step_number,
        game_over: data.game_over,
        winner: data.winner,
        message: data.message
      });
      
      setCurrentStep(data.step_number);
      
      // Switch to emergency meeting phase at step 25
      if (data.step_number >= 25) {
        setPhase('emergency_meeting');
      }
      
      if (data.game_over || data.step_number >= 30) {
        setIsPlaying(false);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to step game');
      setIsPlaying(false);
    } finally {
      setLoading(false);
    }
  };

  // Initialize game only when reaching step 25
  useEffect(() => {
    if (currentStep === 25 && !gameData) {
      initializeGame();
    }
  }, [currentStep, gameData]);

  // Game Master Scenario Data (keeping for visual simulation)
  const gameScenario = [
    {step: 0, agents: {red: {location: 'Cafeteria', action: 'starts doing wiring task', met: ['blue', 'green', 'yellow']}, blue: {location: 'Cafeteria', action: 'starts doing fuel task', met: ['red', 'green', 'yellow']}, green: {location: 'Cafeteria', action: 'starts doing garbage disposal task', met: ['red', 'blue', 'yellow']}, yellow: {location: 'Cafeteria', action: 'pretends to do card swipe task', met: ['red', 'blue', 'green']}}},
    {step: 1, agents: {red: {location: 'Cafeteria', action: 'continues wiring task', met: ['blue', 'green', 'yellow']}, blue: {location: 'Cafeteria', action: 'continues fuel task', met: ['red', 'green', 'yellow']}, green: {location: 'Cafeteria', action: 'continues garbage disposal task', met: ['red', 'blue', 'yellow']}, yellow: {location: 'Cafeteria', action: 'fake struggling with card swipe', met: ['red', 'blue', 'green']}}},
    {step: 2, agents: {red: {location: 'Cafeteria', action: 'finishes wiring task', met: ['blue', 'green', 'yellow']}, blue: {location: 'Cafeteria', action: 'finishes fuel task', met: ['red', 'green', 'yellow']}, green: {location: 'Cafeteria', action: 'finishes garbage disposal task', met: ['red', 'blue', 'yellow']}, yellow: {location: 'Cafeteria', action: 'fake finishes card swipe', met: ['red', 'blue', 'green']}}},
    {step: 3, agents: {red: {location: 'Hallway', action: 'starts moving toward Electrical', met: []}, blue: {location: 'Hallway', action: 'starts moving toward Navigation', met: []}, green: {location: 'Cafeteria', action: 'remains in Cafeteria, starts second task', met: ['yellow']}, yellow: {location: 'Cafeteria', action: 'remains in Cafeteria with green', met: ['green']}}},
    {step: 4, agents: {red: {location: 'Hallway', action: 'walking toward Electrical', met: []}, blue: {location: 'Hallway', action: 'walking toward Navigation', met: []}, green: {location: 'Cafeteria', action: 'working on download task', met: ['yellow']}, yellow: {location: 'Cafeteria', action: 'pretends to do another cafeteria task', met: ['green']}}},
    {step: 5, agents: {red: {location: 'Electrical', action: 'enters Electrical room', met: []}, blue: {location: 'Navigation', action: 'enters Navigation room', met: []}, green: {location: 'Cafeteria', action: 'finishes download task', met: ['yellow']}, yellow: {location: 'Cafeteria', action: 'finishes fake cafeteria task', met: ['green']}}},
    {step: 6, agents: {red: {location: 'Electrical', action: 'starts electrical wiring task', met: []}, blue: {location: 'Navigation', action: 'starts navigation calibration', met: []}, green: {location: 'Hallway', action: 'starts moving toward Navigation', met: []}, yellow: {location: 'Hallway', action: 'starts moving toward Electrical', met: []}}},
    {step: 7, agents: {red: {location: 'Electrical', action: 'working on electrical wiring', met: []}, blue: {location: 'Navigation', action: 'working on navigation calibration', met: []}, green: {location: 'Hallway', action: 'walking toward Navigation', met: ['yellow']}, yellow: {location: 'Hallway', action: 'walking toward Electrical', met: ['green']}}},
    {step: 8, agents: {red: {location: 'Electrical', action: 'continues electrical wiring', met: []}, blue: {location: 'Navigation', action: 'continues navigation calibration', met: []}, green: {location: 'Hallway', action: 'reaches Navigation room entrance', met: []}, yellow: {location: 'Hallway', action: 'reaches Electrical room entrance', met: []}}},
    {step: 9, agents: {red: {location: 'Electrical', action: 'nearly finished electrical wiring', met: ['yellow']}, blue: {location: 'Navigation', action: 'finishes navigation calibration', met: ['green']}, green: {location: 'Navigation', action: 'enters Navigation room', met: ['blue']}, yellow: {location: 'Electrical', action: 'enters Electrical room', met: ['red']}}},
    {step: 10, agents: {red: {location: 'Electrical', action: 'finishes electrical wiring task', met: ['yellow']}, blue: {location: 'Navigation', action: 'starts second navigation task', met: ['green']}, green: {location: 'Navigation', action: 'starts navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'pretends to start electrical task', met: ['red']}}},
    {step: 11, agents: {red: {location: 'Electrical', action: 'starts second electrical task', met: ['yellow']}, blue: {location: 'Navigation', action: 'working on navigation task', met: ['green']}, green: {location: 'Navigation', action: 'working on navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'fake working on electrical task', met: ['red']}}},
    {step: 12, agents: {red: {location: 'Electrical', action: 'working on electrical task', met: ['yellow']}, blue: {location: 'Navigation', action: 'finishes navigation task', met: ['green']}, green: {location: 'Navigation', action: 'continues navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'continues fake electrical work', met: ['red']}}},
    {step: 13, agents: {red: {location: 'Electrical', action: 'finishes electrical task, starts leaving', met: ['yellow']}, blue: {location: 'Navigation', action: 'starts third navigation task', met: ['green']}, green: {location: 'Navigation', action: 'finishes navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'notices red leaving', met: ['red']}}},
    {step: 14, agents: {red: {location: 'Hallway', action: 'exits Electrical room', met: []}, blue: {location: 'Navigation', action: 'working on navigation task', met: ['green']}, green: {location: 'Navigation', action: 'starts second navigation task', met: ['blue']}, yellow: {location: 'Electrical', action: 'alone in Electrical, stops pretending', met: []}}},
    {step: 15, agents: {red: {location: 'Hallway', action: 'walking toward Cafeteria', met: []}, blue: {location: 'Navigation', action: 'continues navigation task', met: ['green']}, green: {location: 'Navigation', action: 'working on navigation task', met: ['blue']}, yellow: {location: 'Hallway', action: 'leaves Electrical, moves toward Navigation', met: []}}},
    {step: 16, agents: {red: {location: 'Cafeteria', action: 'reaches Cafeteria', met: []}, blue: {location: 'Navigation', action: 'finishes navigation task', met: ['green']}, green: {location: 'Navigation', action: 'continues navigation task', met: ['blue']}, yellow: {location: 'Hallway', action: 'walking toward Navigation', met: []}}},
    {step: 17, agents: {red: {location: 'Cafeteria', action: 'starts cafeteria task', met: []}, blue: {location: 'Hallway', action: 'starts moving toward Cafeteria', met: ['yellow']}, green: {location: 'Navigation', action: 'finishes navigation task, starts leaving', met: []}, yellow: {location: 'Hallway', action: 'walking toward Navigation, crosses paths with blue', met: ['blue']}}},
    {step: 18, agents: {red: {location: 'Cafeteria', action: 'working on cafeteria task', met: []}, blue: {location: 'Hallway', action: 'continues toward Cafeteria', met: []}, green: {location: 'Hallway', action: 'exits Navigation room, walking', met: []}, yellow: {location: 'Navigation', action: 'reaches Navigation room', met: []}}},
    {step: 19, agents: {red: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'enters Cafeteria', met: ['red']}, green: {location: 'Hallway', action: 'walking toward Electrical', met: []}, yellow: {location: 'Navigation', action: 'enters Navigation room, pretends to do task', met: []}}},
    {step: 20, agents: {red: {location: 'Cafeteria', action: 'working on cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'starts cafeteria task', met: ['red']}, green: {location: 'Hallway', action: 'continues toward Electrical', met: []}, yellow: {location: 'Hallway', action: 'quickly leaves Navigation, follows green toward Electrical', met: []}}},
    {step: 21, agents: {red: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'working on cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'enters Electrical room', met: []}, yellow: {location: 'Hallway', action: 'reaches Electrical room entrance', met: []}}},
    {step: 22, agents: {red: {location: 'Cafeteria', action: 'finishes cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'starts electrical task', met: ['yellow']}, yellow: {location: 'Electrical', action: 'enters Electrical room', met: ['green']}}},
    {step: 23, agents: {red: {location: 'Cafeteria', action: 'starts second cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'finishes cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'working on electrical task', met: ['yellow'], status: 'alive'}, yellow: {location: 'Electrical', action: 'kills green', met: ['green']}}},
    {step: 24, agents: {red: {location: 'Cafeteria', action: 'working on cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'starts second cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Hallway', action: 'quickly leaves Electrical', met: []}}},
    {step: 25, agents: {red: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['blue']}, blue: {location: 'Cafeteria', action: 'working on cafeteria task', met: ['red']}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Hallway', action: 'walking quickly toward Cafeteria', met: []}}},
    {step: 26, agents: {red: {location: 'Cafeteria', action: 'finishes cafeteria task', met: ['blue', 'yellow']}, blue: {location: 'Cafeteria', action: 'continues cafeteria task', met: ['red', 'yellow']}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Cafeteria', action: 'enters Cafeteria, pretends to have been doing tasks', met: ['red', 'blue']}}},
    {step: 27, agents: {red: {location: 'Hallway', action: 'starts moving toward Electrical', met: []}, blue: {location: 'Hallway', action: 'finishes cafeteria task, starts moving toward Navigation', met: []}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Cafeteria', action: 'remains in Cafeteria, does fake task to establish alibi', met: []}}},
    {step: 28, agents: {red: {location: 'Hallway', action: 'walking toward Electrical', met: []}, blue: {location: 'Hallway', action: 'walking toward Navigation', met: []}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Hallway', action: 'finishes fake cafeteria task, starts moving toward Navigation', met: []}}},
    {step: 29, agents: {red: {location: 'Hallway', action: 'reaches Electrical room entrance', met: []}, blue: {location: 'Navigation', action: 'enters Navigation room', met: []}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Hallway', action: 'walking toward Navigation', met: []}}},
    {step: 30, agents: {red: {location: 'Electrical', action: 'enters Electrical, discovers green\'s dead body, calls emergency meeting', met: []}, blue: {location: 'Cafeteria', action: 'hears emergency meeting call, walks to meeting table', met: []}, green: {location: 'Electrical', action: 'DEAD', met: [], status: 'dead'}, yellow: {location: 'Cafeteria', action: 'hears emergency meeting call, walks to meeting table', met: []}}}
  ];

  // Room positions for visual layout
  const roomPositions = {
    'Cafeteria': { x: 200, y: 150, width: 120, height: 80, color: '#ffeb3b' },
    'Electrical': { x: 450, y: 150, width: 100, height: 80, color: '#f44336' },
    'Navigation': { x: 200, y: 300, width: 100, height: 80, color: '#2196f3' },
    'Hallway': { x: 350, y: 225, width: 80, height: 50, color: '#9e9e9e' }
  };

  // Agent colors
  const agentColors = {
    red: '#f44336',
    blue: '#2196f3',
    green: '#4caf50',
    yellow: '#ffeb3b'
  };


  // Auto-advance simulation 
  useEffect(() => {
    let interval;
    if (isPlaying && currentStep < 30 && phase === 'simulation') {
      interval = setInterval(() => {
        setCurrentStep(prev => {
          const nextStep = prev + 1;
          
          // At step 25, switch to emergency meeting and start using API
          if (nextStep === 25) {
            setPhase('emergency_meeting');
            // API will be initialized by the other useEffect
          }
          
          return nextStep;
        });
      }, 500); // 0.5 seconds for visual simulation
    }
    
    // For API steps (25+), use different interval
    if (isPlaying && gameData && currentStep >= 25 && !gameData.game_over) {
      interval = setInterval(() => {
        stepGame();
      }, 2000); // 2 seconds for API calls
    }
    
    return () => clearInterval(interval);
  }, [isPlaying, currentStep, gameData, phase]);

  const resetSimulation = () => {
    setCurrentStep(0);
    setIsPlaying(false);
    setPhase('simulation');
    setGameData(null); // Clear API data
    setError(null);
  };

  // Map agent colors to hex values
  const getAgentColor = (color: string) => {
    const colorMap: { [key: string]: string } = {
      'red': '#f44336',
      'blue': '#2196f3', 
      'green': '#4caf50',
      'yellow': '#ffeb3b',
      'pink': '#e91e63',
      'orange': '#ff9800',
      'black': '#424242',
      'white': '#fafafa'
    };
    return colorMap[color.toLowerCase()] || '#9e9e9e';
  };

  // Get agent by ID
  const getAgentById = (id: number) => {
    return gameData?.agents.find(agent => agent.id === id);
  };

  const currentStepData = gameScenario[currentStep] || gameScenario[0];

  return (
    <div className="w-full max-w-6xl mx-auto p-4 bg-gray-100 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        {/* Loading State */}
        {loading && (
          <div className="text-center py-8">
            <div className="text-lg">Loading...</div>
          </div>
        )}
        
        {/* Error State */}
        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-4">
            <strong className="font-bold">Error:</strong> {error}
          </div>
        )}
        
        {/* Header and Controls - Hidden during emergency meeting */}
        {phase === 'simulation' && (
          <>
            <h1 className="text-3xl font-bold text-center mb-6">Among Us Multi-Agent AI Simulation</h1>
            
            {/* Controls */}
            <div className="flex justify-center items-center gap-4 mb-6">
              <button
                onClick={() => setIsPlaying(!isPlaying)}
                className={`flex items-center gap-2 px-4 py-2 rounded ${
                  isPlaying ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
                } text-white`}
                disabled={loading || (gameData && gameData.game_over)}
              >
                {isPlaying ? <Pause size={16} /> : <Play size={16} />}
                {isPlaying ? 'Pause' : 'Play'}
              </button>
              
              <button
                onClick={resetSimulation}
                className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded"
                disabled={loading}
              >
                <RotateCcw size={16} />
                Reset
              </button>
              
              <div className="text-lg font-semibold">
                Step: {currentStep}/30 | Phase: {phase === 'simulation' ? 'Simulation' : 'Emergency Meeting'}
              </div>
            </div>
            
            {/* Game Status */}
            {gameData && (
              <div className="text-center mb-4 p-3 bg-gray-50 rounded">
                <p className="text-lg">{gameData.message}</p>
              </div>
            )}
          </>
        )}

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* Game Map - Hidden during emergency meeting */}
            {phase === 'simulation' && (
            <div className="lg:col-span-2">
              <div className="bg-gray-800 rounded-lg p-4 relative" style={{height: '500px'}}>
                <h3 className="text-white text-xl mb-4">Game Map</h3>
              
              {/* Roads/Paths between rooms */}
              <svg className="absolute top-0 left-0 w-full h-full pointer-events-none" style={{zIndex: 1}}>
                {/* Cafeteria to Hallway */}
                <line x1="320" y1="190" x2="350" y2="225" stroke="#666" strokeWidth="8" opacity="0.7" />
                {/* Hallway to Electrical */}
                <line x1="430" y1="240" x2="450" y2="190" stroke="#666" strokeWidth="8" opacity="0.7" />
                {/* Hallway to Navigation */}
                <line x1="380" y1="275" x2="250" y2="300" stroke="#666" strokeWidth="8" opacity="0.7" />
                
                {/* Path indicators (small circles at intersections) */}
                <circle cx="350" cy="225" r="4" fill="#444" />
                <circle cx="430" cy="240" r="4" fill="#444" />
                <circle cx="380" cy="275" r="4" fill="#444" />
              </svg>

              {/* Rooms */}
              {Object.entries(roomPositions).map(([roomName, pos]) => (
                <div
                  key={roomName}
                  className="absolute border-2 border-gray-600 rounded flex items-center justify-center text-black font-bold"
                  style={{
                    left: pos.x,
                    top: pos.y,
                    width: pos.width,
                    height: pos.height,
                    backgroundColor: pos.color,
                    zIndex: 2
                  }}
                >
                  {roomName}
                </div>
              ))}
              
              {/* Agents */}
              {Object.entries(currentStepData.agents).map(([agentId, agentData]) => {
                if (agentData.status === 'dead') {
                  const pos = roomPositions[agentData.location];
                  return (
                    <div
                      key={agentId}
                      className="absolute border-4 border-red-800 rounded-full flex items-center justify-center text-white font-bold text-xs"
                      style={{
                        left: pos.x + 20,
                        top: pos.y + 20,
                        width: 30,
                        height: 30,
                        backgroundColor: '#666',
                        transform: 'translate(-50%, -50%)',
                        zIndex: 3
                      }}
                    >
                      💀
                    </div>
                  );
                }
                
                const pos = roomPositions[agentData.location];
                const agentOffset = Object.keys(currentStepData.agents).indexOf(agentId) * 35;
                
                return (
                  <div
                    key={agentId}
                    className="absolute border-2 border-white rounded-full flex items-center justify-center text-white font-bold text-xs transition-all duration-1000"
                    style={{
                      left: pos.x + 10 + agentOffset,
                      top: pos.y + 10,
                      width: 30,
                      height: 30,
                      backgroundColor: agentColors[agentId],
                      transform: 'translate(-50%, -50%)',
                      zIndex: 3
                    }}
                  >
                    {agentId.charAt(0).toUpperCase()}
                  </div>
                );
              })}

            </div>
          </div>
          )}

          {/* Control Panel - Show current step info during simulation */}
          {phase === 'simulation' && (
          <div className="space-y-4">
            {/* Current Step Info */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-bold mb-3">Current Step Actions</h3>
              {Object.entries(currentStepData.agents).map(([agentId, agentData]) => (
                <div key={agentId} className="mb-2 text-sm">
                  <span className="font-semibold" style={{color: agentColors[agentId]}}>
                    {agentId}:
                  </span>{' '}
                  {agentData.action} in {agentData.location}
                  {agentData.met && agentData.met.length > 0 && (
                    <div className="text-xs text-gray-600 ml-4">
                      Met: {agentData.met.join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Preview: Chat will start at step 25 */}
            <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
              <h3 className="text-lg font-bold mb-2 text-blue-800">Coming Up</h3>
              <div className="text-sm text-blue-700">
                {currentStep < 25 ? (
                  <div>
                    <div>🎬 Simulation Phase (Steps 1-24)</div>
                    <div className="mt-1">💬 AI Chat starts at Step 25</div>
                  </div>
                ) : (
                  <div>🤖 AI agents are now discussing!</div>
                )}
              </div>
            </div>
          </div>
          )}

          {/* Control Panel - Show real agents during emergency meeting */}
          {phase === 'emergency_meeting' && gameData && (
          <div className="space-y-4">
            {/* Current Agents */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-bold mb-3">Current Agents</h3>
              <div className="space-y-2">
                {gameData.agents.map((agent) => (
                  <div key={agent.id} className="flex items-center gap-3">
                    <div
                      className="w-6 h-6 rounded-full border-2 border-gray-300"
                      style={{backgroundColor: getAgentColor(agent.color)}}
                    />
                    <span className="font-medium">{agent.name}</span>
                    {agent.is_impostor && (
                      <span className="text-sm bg-red-100 text-red-600 px-2 py-1 rounded-full font-medium">
                        impostor
                      </span>
                    )}
                    {!agent.is_alive && (
                      <span className="text-sm bg-gray-100 text-gray-600 px-2 py-1 rounded-full font-medium">
                        eliminated
                      </span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
          )}
        </div>

        {/* Emergency Meeting Panel - Below Map */}
        {phase === 'emergency_meeting' && gameData && (
          <div className="mt-6 bg-red-50 border border-red-200 rounded-lg p-6">
            <div className="text-center mb-6">
              <h2 className="text-3xl font-bold text-red-800 mb-2">🚨 Emergency Meeting 🚨</h2>
              <p className="text-lg text-red-600">{gameData.message}</p>
              <div className="text-sm text-gray-600 mt-2">
                Step {gameData.step_number} / {gameData.max_steps} | 
                Alive: {gameData.agents.filter(a => a.is_alive).length} agents
              </div>
              {gameData.winner && (
                <p className="text-xl font-bold mt-2 text-green-600">Winner: {gameData.winner}</p>
              )}
            </div>
            
            {/* Chat Panel */}
            <div className="bg-white rounded-lg border shadow-lg">
              <div className="p-4 border-b bg-gray-50 rounded-t-lg">
                <h3 className="text-xl font-semibold text-gray-800">Discussion</h3>
                <p className="text-sm text-gray-600 mt-1">Agents are sharing their observations and suspicions</p>
              </div>
              <div className="p-6 space-y-4 max-h-96 overflow-y-auto">
                {gameData.conversation_history
                  .filter(action => action.action_type === 'speak')
                  .map((action, index) => {
                    const agent = getAgentById(action.agent_id);
                    if (!agent) return null;
                    
                    return (
                      <div key={index} className="flex items-start gap-4 p-4 bg-gray-50 rounded-lg">
                        {/* Agent Avatar */}
                        <div
                          className="w-12 h-12 rounded-full border-3 border-white shadow-lg flex items-center justify-center text-white font-bold text-lg flex-shrink-0"
                          style={{backgroundColor: getAgentColor(agent.color)}}
                        >
                          {agent.name.charAt(0).toUpperCase()}
                        </div>
                        
                        {/* Chat Message */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-2">
                            <span className="font-bold text-lg" style={{color: getAgentColor(agent.color)}}>
                              {agent.name}
                            </span>
                            {agent.is_impostor && (
                              <span className="text-sm bg-red-100 text-red-600 px-3 py-1 rounded-full font-medium">
                                impostor
                              </span>
                            )}
                            <span className="text-sm text-gray-400">step {gameData.step_number}</span>
                          </div>
                          <div className="text-base text-gray-700 leading-relaxed bg-white p-3 rounded-lg border">
                            {action.content}
                          </div>
                        </div>
                      </div>
                    );
                  })}
                
                {/* Show votes */}
                {gameData.conversation_history
                  .filter(action => action.action_type === 'vote')
                  .map((action, index) => {
                    const voter = getAgentById(action.agent_id);
                    const target = action.target_agent_id ? getAgentById(action.target_agent_id) : null;
                    if (!voter) return null;
                    
                    return (
                      <div key={`vote-${index}`} className="p-3 bg-yellow-50 rounded-lg border-l-4 border-yellow-400">
                        <span className="font-semibold" style={{color: getAgentColor(voter.color)}}>
                          {voter.name}
                        </span>
                        <span className="text-gray-600"> voted to eliminate </span>
                        {target && (
                          <span className="font-semibold" style={{color: getAgentColor(target.color)}}>
                            {target.name}
                          </span>
                        )}
                      </div>
                    );
                  })}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AmongUsSimulation;