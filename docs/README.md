# Documentation Index

Welcome to the AI Impostor Game documentation. This directory contains comprehensive documentation for understanding, developing, and deploying the application.

## Documentation Structure

### 📋 [Application Overview](./application-overview.md)
Complete technical documentation covering:
- System architecture and component breakdown
- Game mechanics and AI agent behavior
- API specification and data models
- Development workflow and setup
- Future enhancements and security considerations

### 🧪 [API Testing Guide](./api-testing-guide.md)
Comprehensive testing instructions including:
- Complete endpoint testing with curl, Postman, HTTPie
- Full game workflow testing scripts (Bash & Python)
- Error scenario testing and debugging tips
- Performance testing and monitoring
- Expected response examples and patterns

### 🚀 Quick Start
For immediate setup, see the [backend README](../backend/README.md) for installation and running instructions.

### 🎮 Game Description
AI-powered social deduction game where autonomous agents play Among Us-style impostor elimination rounds with sophisticated reasoning and strategy.

## Key Features

- **8 AI Agents** with distinct personalities (crewmates + 1 impostor)
- **Natural Language Processing** for agent communication
- **Strategic Decision Making** with private thoughts and public statements
- **RESTful API** for easy frontend integration
- **Real-time Game State** management

## Technology Stack

- **Backend**: FastAPI + Python
- **AI Engine**: Cerebras Cloud SDK (Qwen-3-235B)
- **Data Validation**: Pydantic
- **Server**: Uvicorn ASGI

## Getting Started

1. Read the [Application Overview](./application-overview.md) for technical details
2. Follow the [Backend Setup Guide](../backend/README.md) for installation
3. Explore the API endpoints via `/docs` when server is running

## Contributing

This documentation is designed to help developers understand and extend the AI Impostor Game system. For questions or improvements, please refer to the detailed architecture documentation.