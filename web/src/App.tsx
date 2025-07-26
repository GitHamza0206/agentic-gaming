import React, { useState, useEffect } from 'react';
import { Play, Pause, RotateCcw } from 'lucide-react';

const AmongUsSimulation = () => {
  const [currentStep, setCurrentStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);
  const [phase, setPhase] = useState('simulation');
  const [memoryAccess, setMemoryAccess] = useState({
    red: false,
    blue: false,
    green: false,
    yellow: false
  });

  // Game Master Scenario Data
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

  // Generate memories based on encounters
  const generateMemories = (agentId) => {
    const memories = [];
    for (let i = 0; i <= currentStep; i++) {
      const stepData = gameScenario[i];
      if (stepData && stepData.agents[agentId]) {
        const agent = stepData.agents[agentId];
        if (agent.met && agent.met.length > 0) {
          memories.push({
            step: i,
            content: `Step ${i}: Saw ${agent.met.join(', ')} in ${agent.location}`,
            location: agent.location,
            met: agent.met
          });
        }
      }
    }
    return memories;
  };

  // Generate reasoning for emergency meeting
  const generateReasoning = (agentId) => {
    const personalMemories = generateMemories(agentId);
    let availableMemories = personalMemories;

    if (memoryAccess[agentId]) {
      // Add shared memories from other agents
      const allAgents = ['red', 'blue', 'green', 'yellow'];
      allAgents.forEach(otherId => {
        if (otherId !== agentId && memoryAccess[otherId]) {
          availableMemories = [...availableMemories, ...generateMemories(otherId)];
        }
      });
    }

    if (agentId === 'yellow') {
      // Impostor reasoning
      if (memoryAccess[agentId]) {
        return "I was doing tasks in Navigation and Cafeteria. Based on the shared memories, I can see that everyone was scattered around doing tasks. This is very suspicious timing.";
      } else {
        return "I was doing tasks in Navigation and Cafeteria the whole time. I never went to Electrical.";
      }
    } else {
      // Crew reasoning
      if (memoryAccess[agentId] && availableMemories.length > personalMemories.length) {
        const criticalEvidence = availableMemories.find(m => 
          m.content.includes('yellow') && m.location === 'Electrical'
        );
        if (criticalEvidence) {
          return `Based on shared memories, I can see that yellow was spotted near Electrical around the time of the murder. Cross-referencing the timelines, yellow's alibi doesn't match the witness accounts.`;
        }
        return "Based on shared memories, I can piece together everyone's movements. The timeline shows suspicious gaps in yellow's story.";
      } else {
        return `I remember seeing some people during my tasks, but I can't make a clear connection to who might be the impostor based on my limited observations.`;
      }
    }
  };

  // Auto-advance simulation
  useEffect(() => {
    let interval;
    if (isPlaying && currentStep < 30 && phase === 'simulation') {
      interval = setInterval(() => {
        setCurrentStep(prev => {
          if (prev === 29) {
            setPhase('emergency_meeting');
            setIsPlaying(false);
            return prev + 1;
          }
          return prev + 1;
        });
      }, 2000);
    }
    return () => clearInterval(interval);
  }, [isPlaying, currentStep, phase]);

  const resetSimulation = () => {
    setCurrentStep(0);
    setIsPlaying(false);
    setPhase('simulation');
  };

  const toggleMemoryAccess = (agentId) => {
    setMemoryAccess(prev => ({
      ...prev,
      [agentId]: !prev[agentId]
    }));
  };

  const currentStepData = gameScenario[currentStep] || gameScenario[0];

  return (
    <div className="w-full max-w-6xl mx-auto p-4 bg-gray-100 min-h-screen">
      <div className="bg-white rounded-lg shadow-lg p-6">
        <h1 className="text-3xl font-bold text-center mb-6">Among Us Multi-Agent AI Simulation</h1>
        
        {/* Controls */}
        <div className="flex justify-center items-center gap-4 mb-6">
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className={`flex items-center gap-2 px-4 py-2 rounded ${
              isPlaying ? 'bg-red-500 hover:bg-red-600' : 'bg-green-500 hover:bg-green-600'
            } text-white`}
            disabled={phase === 'emergency_meeting'}
          >
            {isPlaying ? <Pause size={16} /> : <Play size={16} />}
            {isPlaying ? 'Pause' : 'Play'}
          </button>
          
          <button
            onClick={resetSimulation}
            className="flex items-center gap-2 px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded"
          >
            <RotateCcw size={16} />
            Reset
          </button>
          
          <div className="text-lg font-semibold">
            Step: {currentStep}/30 | Phase: {phase === 'simulation' ? 'Simulation' : 'Emergency Meeting'}
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Game Map */}
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

              {/* Memory connections */}
              {Object.entries(memoryAccess).map(([agentId, hasAccess]) => {
                if (!hasAccess || currentStepData.agents[agentId]?.status === 'dead') return null;
                
                return Object.entries(memoryAccess).map(([otherId, otherAccess]) => {
                  if (agentId === otherId || !otherAccess || currentStepData.agents[otherId]?.status === 'dead') return null;
                  
                  const pos1 = roomPositions[currentStepData.agents[agentId].location];
                  const pos2 = roomPositions[currentStepData.agents[otherId].location];
                  const offset1 = Object.keys(currentStepData.agents).indexOf(agentId) * 35;
                  const offset2 = Object.keys(currentStepData.agents).indexOf(otherId) * 35;
                  
                  return (
                    <svg
                      key={`${agentId}-${otherId}`}
                      className="absolute top-0 left-0 w-full h-full pointer-events-none"
                    >
                      <line
                        x1={pos1.x + 10 + offset1}
                        y1={pos1.y + 10}
                        x2={pos2.x + 10 + offset2}
                        y2={pos2.y + 10}
                        stroke="#00ff00"
                        strokeWidth="2"
                        strokeDasharray="5,5"
                        opacity="0.7"
                      />
                    </svg>
                  );
                });
              })}
            </div>
          </div>

          {/* Control Panel */}
          <div className="space-y-4">
            {/* Memory Access Controls */}
            <div className="bg-gray-50 rounded-lg p-4">
              <h3 className="text-lg font-bold mb-3">Memory Access Control</h3>
              {Object.entries(agentColors).map(([agentId, color]) => (
                <div key={agentId} className="flex items-center gap-2 mb-2">
                  <input
                    type="checkbox"
                    id={`memory-${agentId}`}
                    checked={memoryAccess[agentId]}
                    onChange={() => toggleMemoryAccess(agentId)}
                    className="w-4 h-4"
                  />
                  <label htmlFor={`memory-${agentId}`} className="flex items-center gap-2">
                    <div
                      className="w-4 h-4 rounded-full border"
                      style={{backgroundColor: color}}
                    />
                    {agentId} {agentId === 'yellow' ? '(impostor)' : ''}
                  </label>
                </div>
              ))}
            </div>

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

            {/* Emergency Meeting */}
            {phase === 'emergency_meeting' && (
              <div className="bg-red-50 border border-red-200 rounded-lg p-4">
                <h3 className="text-lg font-bold mb-3 text-red-800">Emergency Meeting</h3>
                <p className="text-sm text-red-600 mb-3">Body found in Electrical! Discuss and find the impostor.</p>
                
                {Object.entries(currentStepData.agents)
                  .filter(([_, agentData]) => agentData.status !== 'dead')
                  .map(([agentId, _]) => (
                    <div key={agentId} className="mb-3 p-2 bg-white rounded border">
                      <div className="font-semibold mb-1" style={{color: agentColors[agentId]}}>
                        {agentId} {agentId === 'yellow' ? '(impostor)' : ''}:
                      </div>
                      <div className="text-sm text-gray-700">
                        {generateReasoning(agentId)}
                      </div>
                    </div>
                  ))}
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default AmongUsSimulation;