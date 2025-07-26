# Round Table AI Agents with Voice API 使用指南

## 概述

我们已经成功集成了 ElevenLabs TTS 到 Round Table AI Agents 系统中。当 AI 代理在会议中发言时，系统会自动生成语音并返回 Base64 编码的音频数据。

## API 端点

### 1. 初始化游戏
```
POST /impostor-game/init
```

**请求参数:**
```json
{
  "num_players": 4,
  "max_steps": 30
}
```

**响应:**
```json
{
  "game_id": "uuid-string",
  "message": "游戏初始化消息",
  "agents": [...],
  "impostor_revealed": "Red",
  "meeting_trigger": "dead_body",
  "reporter_name": "Red",
  "meeting_reason": "Red found Green's body in Electrical"
}
```

### 2. 游戏步骤 (包含语音生成)
```
POST /impostor-game/step/{game_id}
```

**响应 (包含语音数据):**
```json
{
  "game_id": "uuid-string",
  "phase": "active",
  "step_number": 1,
  "max_steps": 30,
  "turns": [
    {
      "agent_id": 0,
      "think": "I need to analyze who suspects me...",
      "speak": "I was in the electrical room fixing the wiring!",
      "vote": null,
      "memory_update": {...},
      "audio_base64": "UklGRiQAAABXQVZFZm10IBAAAAABAAEA..."  // MP3音频的Base64编码
    }
  ],
  "conversation_history": [...],
  "eliminated": null,
  "winner": null,
  "game_over": false,
  "message": "Step 1 completed."
}
```

## 语音功能特性

### 1. 自动语音生成
- 当 AI 代理发言时，系统自动调用 ElevenLabs API 生成语音
- 每个代理根据颜色分配不同的声音：
  - Red: Rachel (confident female)
  - Blue: Domi (strong male)
  - Green: Bella (soft female)
  - Yellow: Antoni (warm male)
  - Orange: Elli (young female)
  - Pink: Josh (deep male)
  - Purple: Arnold (mature male)
  - Cyan: Adam (clear male)

### 2. 音频数据格式
- 格式: MP3
- 编码: Base64
- 字段: `audio_base64` 在 `AgentTurn` 对象中

## 前端集成示例

### 1. 获取游戏步骤并播放语音

```javascript
async function nextStep() {
    const response = await fetch(`/impostor-game/step/${gameId}`, {
        method: 'POST'
    });
    
    const data = await response.json();
    
    // 处理每个代理的回合
    data.turns.forEach(turn => {
        if (turn.speak && turn.audio_base64) {
            displayAgentSpeech(turn);
        }
    });
}

function displayAgentSpeech(turn) {
    // 显示文本
    const speechElement = document.createElement('div');
    speechElement.innerHTML = `
        <strong>${getAgentName(turn.agent_id)}:</strong> ${turn.speak}
        <button onclick="playAudio('${turn.audio_base64}')">🔊 播放语音</button>
    `;
    
    document.getElementById('conversation').appendChild(speechElement);
}

function playAudio(audioBase64) {
    // 创建音频对象并播放
    const audioData = `data:audio/mpeg;base64,${audioBase64}`;
    const audio = new Audio(audioData);
    audio.play();
}
```

### 2. 完整的前端示例

我已经创建了一个完整的前端示例文件 `frontend_voice_example.html`，展示了如何：

1. 初始化游戏
2. 执行游戏步骤
3. 显示代理发言
4. 播放生成的语音
5. 处理音频播放状态

## 环境配置

### 1. 设置 ElevenLabs API Key

创建 `.env` 文件：
```bash
ELEVENLABS_API_KEY=sk_7b6c0905b03564ec1e8c3db93d54f25bfc464c99ad3c7f07
```

### 2. 启动后端服务器

```bash
cd backend
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

## 测试语音功能

### 1. 运行 TTS 测试脚本

```bash
cd backend
python test_tts.py
```

这将测试不同代理的语音生成功能。

### 2. 使用前端示例

1. 启动后端服务器
2. 在浏览器中打开 `frontend_voice_example.html`
3. 点击"初始化游戏"
4. 点击"下一步"观看代理发言并播放语音

## API 响应数据结构

### AgentTurn 对象
```typescript
interface AgentTurn {
  agent_id: number;
  think: string;                    // 代理的私人思考
  speak?: string;                   // 代理的公开发言
  vote?: number;                    // 投票目标 (agent_id)
  memory_update?: AgentMemory;      // 记忆更新
  audio_base64?: string;            // 语音数据 (Base64编码的MP3)
}
```

### StepResponse 对象
```typescript
interface StepResponse {
  game_id: string;
  phase: string;
  step_number: number;
  max_steps: number;
  turns: AgentTurn[];               // 包含语音数据的代理回合
  conversation_history: AgentAction[];
  eliminated?: string;
  winner?: string;
  game_over: boolean;
  message: string;
}
```

## 注意事项

1. **API 限制**: ElevenLabs API 有使用限制，请注意配额管理
2. **音频大小**: Base64 编码的音频数据可能较大，注意网络传输
3. **浏览器兼容性**: 确保浏览器支持 HTML5 Audio API
4. **错误处理**: 实现适当的错误处理机制，处理 TTS 生成失败的情况

## 下一步

现在你可以：

1. 启动后端服务器测试 API
2. 使用提供的前端示例体验语音功能
3. 集成到你的前端应用中
4. 根据需要自定义语音设置和代理声音映射

语音功能已经完全集成到系统中，每当代理在 Round Table 会议中发言时，都会自动生成相应的语音！🎉
