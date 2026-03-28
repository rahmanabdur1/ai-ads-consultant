AI Ads Consultant — Full System Architecture
🧠 1. Overview

AI Ads Consultant is a SaaS platform that uses Multi-Agent Systems (MAS) to automatically:

Research market trends
Plan ad strategies
Generate ad creatives & copy
Launch campaigns
Optimize performance

The system is built using LangGraph-based agent orchestration, real-time streaming, and a hybrid memory architecture.

🧩 2. High-Level Architecture
Frontend (Next.js)
        ↓
Nginx (Reverse Proxy)
        ↓
FastAPI (API Gateway)
        ↓
LangGraph (Multi-Agent Orchestrator)
        ↓
Memory + Services + External APIs
        ↓
Celery Workers (Async Execution)
🎨 3. Frontend Layer (Next.js 14)
Tech:
Next.js 14 + React 18
Tailwind CSS
Zustand (state management)
Features:
Authentication (Login/Register)
Dashboard & Campaign Management
AI Chat Interface
Real-time Agent Streaming (WebSocket)
Key Modules:
AgentStreamPanel → shows agent execution in real-time
useAgentStream → WebSocket hook
authStore, campaignStore → global state
🌐 4. Nginx Reverse Proxy
Responsibilities:
SSL Termination (HTTPS)
Routing:
/ws/*   → WebSocket → FastAPI
/api/*  → REST API → FastAPI
/*      → Frontend (Next.js)
⚙️ 5. Backend API Gateway (FastAPI)
Core Responsibilities:
REST APIs
WebSocket handling
Authentication (JWT)
Rate limiting & middleware
Route Groups:
/auth → login/register
/campaign → campaign CRUD + launch
/agent → run agents
/analytics → performance data
/ws/agent/{id} → real-time streaming
🤖 6. AI Orchestration Layer (LangGraph)
Core Engine:
LangGraph + LangChain
Powered by OpenAI GPT-4o
🔄 Agent Execution Flow
1. Load Memory
2. Research Agent
3. Strategy Agent
4. Copywriting Agent
5. Creative Agent
6. Validator Agent
7. Save Memory
🧠 Agents Overview
Agent	Role
Research Agent	Market + competitor analysis
Strategy Agent	Campaign planning
Copywriting Agent	Headlines, descriptions
Creative Agent	Image + ad creatives
Execution Agent	Launch ads
Optimization Agent	Improve ROI
Validator Agent	Quality control
Memory Agent	Context management
🧠 7. Memory System (Hybrid)
Types:
🔹 Short-Term Memory
Redis
Stores last 20 messages
TTL: 1 hour
🔹 Long-Term Memory
PostgreSQL
Stores campaign results, user preferences
🔹 Vector Memory
Pinecone
Semantic search using embeddings
🧩 Context Builder

Combines:

Short-term + Long-term + Vector → Ranked Context

Used in every agent prompt.

🔌 8. Services Layer
Core Services:
Google Ads Service
Meta Ads Service
Competitor Scraper
Trend Detector (Google Trends + Reddit + News)
Voice Service (Whisper + TTS)
A/B Testing System
Budget Auto-Scaler
Creative Generator (DALL·E)
🗄️ 9. Database Layer
PostgreSQL (Primary DB)

Stores:

Users
Workspaces
Campaigns
Analytics
Agent logs
Redis
Cache
Session storage
Celery queue
Pinecone (Vector DB)
Embeddings (1536-dim)
Semantic memory retrieval
⚡ 10. Background Processing (Celery)
Worker Tasks:
Campaign Launch
Analytics Sync
Optimization
Budget Scaling
Notifications
Weekly Reports
Scheduler (Celery Beat)
Interval	Task
1 hour	Sync analytics
6 hours	Optimize campaigns
6 hours	Auto scale budget
24 hours	Compress memory
7 days	Generate reports
🔌 11. Plugin System
Features:
Install / uninstall plugins
Event-driven hooks
Example Plugins:
Slack Notifier
WhatsApp Notifier
Shopify Sync
AI Creative Generator
Report Generator
🌍 12. External APIs
Google Ads API
Meta Marketing API
OpenAI (GPT-4o, DALL·E, Whisper)
Pinecone API
Web scraping sources (Reddit, News, Trends)
🔄 13. End-to-End Flow
Example:

User Input:

“Run a $500 Google Ads campaign for shoes”

Execution:
Frontend → WebSocket → FastAPI
→ LangGraph Orchestrator
→ Agents execute step-by-step
→ Memory updated
→ Celery launches campaign
→ Ads API called
→ Result returned to UI
🔐 14. Security Architecture
JWT Authentication (24h expiry)
Role-Based Access Control (RBAC)
AES-256 encryption
bcrypt password hashing
Rate limiting (100 req/min)
CORS protection
Workspace isolation (multi-tenancy)
🐳 15. DevOps & Deployment
Infrastructure:
DigitalOcean VPS (4 vCPU, 8GB RAM)
Stack:
Docker + Docker Compose
Nginx
CI/CD scripts
Monitoring:
Prometheus
ELK Stack
Sentry
Flower (Celery UI)
📁 16. Project Structure
backend/
  agents/
  api/
  core/
  memory/
  services/
  tasks/

frontend/
  app/
  components/
  hooks/
  store/

docker-compose.yml
nginx.conf
