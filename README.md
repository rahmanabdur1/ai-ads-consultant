AI ADS CONSULTANT — FULL SYSTEM ARCHITECTURE:


LAYER 1 — USER INTERFACE (Frontend)

┌─────────────────────────────────────────────────────────────────┐
│                    NEXT.JS 14 FRONTEND                          │
│                   React + Tailwind CSS                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Auth Pages  │  │  App Layout  │  │     Page Routes      │  │
│  │  /login      │  │  Sidebar     │  │  /dashboard          │  │
│  │  /register   │  │  Navbar      │  │  /campaigns/new      │  │
│  └──────────────┘  │  Protected   │  │  /campaigns/[id]     │  │
│                    │  Route Guard │  │  /chat               │  │
│                    └──────────────┘  │  /analytics          │  │
│                                      │  /trends             │  │
│                                      │  /competitor         │  │
│                                      │  /ab-test            │  │
│                                      │  /budget             │  │
│                                      │  /creatives          │  │
│                                      │  /voice              │  │
│                                      │  /plugins            │  │
│                                      │  /settings           │  │
│                                      └──────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │                  STATE MANAGEMENT                         │  │
│  │   authStore (zustand+persist)  campaignStore (zustand)    │  │
│  └───────────────────────────────────────────────────────────┘  │
│                                                                 │
│  ┌───────────────────────────────────────────────────────────┐  │
│  │              COMMUNICATION LAYER                          │  │
│  │   axios (REST API calls)    WebSocket (real-time stream)  │  │
│  └───────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              │
                    HTTP / WebSocket
                    
                              │

                              

LAYER 2 — NGINX REVERSE PROXY:

┌─────────────────────────────────────────────────────────────────┐
│                    NGINX (Port 80 / 443)                        │
│                  SSL Termination + Routing                      │
│                                                                 │
│   /ws/*        →  WebSocket  →  Backend:8000                   │
│   /api/*       →  REST API   →  Backend:8000                   │
│   /flower/*    →  Celery UI  →  Flower:5555                    │
│   /*           →  Frontend   →  Next.js:3000                   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │



                              LAYER 3 — API GATEWAY (FastAPI)
┌─────────────────────────────────────────────────────────────────┐
│              FASTAPI APPLICATION (Port 8000)                    │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   MIDDLEWARE STACK                       │   │
│  │  CORSMiddleware → RateLimitMiddleware → LoggingMiddleware│   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   ROUTE GROUPS                          │   │
│  │                                                         │   │
│  │  /auth          →  auth.py        (register, login)     │   │
│  │  /users         →  users.py       (profile, password)   │   │
│  │  /workspace     →  workspace.py   (CRUD)                │   │
│  │  /campaign      →  campaign.py    (CRUD+launch+pause)   │   │
│  │  /agent         →  agent.py       (run, chat)           │   │
│  │  /analytics     →  analytics.py   (summary, per-camp)   │   │
│  │  /competitor    →  competitor.py  (scrape+analyze)      │   │
│  │  /voice         →  voice.py       (STT, TTS, command)   │   │
│  │  /ab            →  ab_test.py     (variants, monitor)   │   │
│  │  /plugins       →  plugins.py     (install, emit)       │   │
│  │  /trends        →  trends.py      (detect)              │   │
│  │  /budget        →  budget.py      (scale, history)      │   │
│  │  /creatives     →  creatives.py   (image, policy)       │   │
│  │  /keywords      →  keywords.py    (research, expand)    │   │
│  │  /ws/agent/{id} →  ws_agent.py    (WebSocket stream)    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │               ERROR HANDLER LAYER                       │   │
│  │   AppError → HTTPException → ValidationError → 500      │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │

LAYER 4 — AI ORCHESTRATION ENGINE
┌─────────────────────────────────────────────────────────────────┐
│              LANGGRAPH ORCHESTRATOR                             │
│                                                                 │
│   INPUT: user_input, budget, platform, goal, tone               │
│                                                                 │
│   ┌─────────────────────────────────────────────────────────┐  │
│   │              GRAPH EXECUTION FLOW                       │  │
│   │                                                         │  │
│   │   load_memory                                           │  │
│   │       ↓                                                 │  │
│   │   research_agent  →  strategy_agent  →  copywriting     │  │
│   │                                           ↓             │  │
│   │                                       creative_agent    │  │
│   │                                           ↓             │  │
│   │                                       validator_agent   │  │
│   │                                           ↓             │  │
│   │                               ┌─── APPROVED? ───┐       │  │
│   │                               │                 │       │  │
│   │                            save_memory      retry (x2)  │  │
│   │                               ↓                 ↓       │  │
│   │                              END           copywriting   │  │
│   └─────────────────────────────────────────────────────────┘  │
│                                                                 │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────┐ │
│   │ Research   │  │ Strategy   │  │Copywriting │  │Creative │ │
│   │ Agent      │  │ Agent      │  │ Agent      │  │ Agent   │ │
│   │ market     │  │ campaign   │  │ headlines  │  │ briefs  │ │
│   │ analysis   │  │ planning   │  │ copy CTAs  │  │ DALL-E  │ │
│   └────────────┘  └────────────┘  └────────────┘  └─────────┘ │
│   ┌────────────┐  ┌────────────┐  ┌────────────┐  ┌─────────┐ │
│   │ Execution  │  │Optimization│  │ Validator  │  │ Memory  │ │
│   │ Agent      │  │ Agent      │  │ Agent      │  │ Agent   │ │
│   │ publish    │  │ scale/A-B  │  │ anti-hall  │  │ r/w mem │ │
│   │ ads        │  │ testing    │  │ quality    │  │ compress│ │
│   └────────────┘  └────────────┘  └────────────┘  └─────────┘ │
│                                                                 │
│   ALL AGENTS USE: OpenAI GPT-4o via LangChain                  │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              │               │               │

LAYER 5 — MEMORY SYSTEM
┌─────────────────────────────────────────────────────────────────┐
│                    MEMORY LAYER                                 │
│                                                                 │
│  ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐  │
│  │  SHORT-TERM MEM  │  │  LONG-TERM MEM   │  │  VECTOR MEM  │  │
│  │                  │  │                  │  │              │  │
│  │  Redis           │  │  PostgreSQL      │  │  Pinecone    │  │
│  │  Session context │  │  memory_logs     │  │  Embeddings  │  │
│  │  Last 20 msgs    │  │  workspace facts │  │  Semantic    │  │
│  │  TTL: 1 hour     │  │  ROI scores      │  │  search      │  │
│  │                  │  │  campaign results│  │  top-K recall│  │
│  │  key:            │  │  user prefs      │  │              │  │
│  │  context:{sid}   │  │  Keep 90 days    │  │  dim: 1536   │  │
│  └──────────────────┘  └──────────────────┘  └──────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                CONTEXT BUILDER                          │   │
│  │  short_term + long_term + vector → ranked context       │   │
│  │  injected into every agent prompt automatically         │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Memory Types: Short-term │ Long-term │ Vector │ Episodic       │
│                Procedural │ Time-weighted recall                │
└─────────────────────────────────────────────────────────────────┘

LAYER 6 — SERVICES LAYER
┌─────────────────────────────────────────────────────────────────┐
│                    SERVICES LAYER                               │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Google Ads  │  │  Meta Ads    │  │  Trend Detector      │  │
│  │  Service     │  │  Service     │  │                      │  │
│  │              │  │              │  │  Google Trends       │  │
│  │  Campaigns   │  │  Campaigns   │  │  Reddit Hot Posts    │  │
│  │  Ad Groups   │  │  Ad Sets     │  │  News RSS            │  │
│  │  RSA Ads     │  │  Creatives   │  │  Social Signals      │  │
│  │  Keywords    │  │  Targeting   │  │  AI Analysis         │  │
│  │  Stats       │  │  Insights    │  │                      │  │
│  │  Pause/Scale │  │  Pause/Scale │  └──────────────────────┘  │
│  └──────────────┘  └──────────────┘                            │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  Competitor  │  │  Voice       │  │  Auto Budget Scaler  │  │
│  │  Scraper     │  │  Service     │  │                      │  │
│  │              │  │              │  │  14-day history      │  │
│  │  httpx       │  │  Whisper STT │  │  8 action types      │  │
│  │  BeautifulS  │  │  TTS reply   │  │  AGGRESSIVE_SCALE    │  │
│  │  AI analysis │  │  Intent parse│  │  MODERATE_SCALE      │  │
│  │  Keyword ext │  │  Voice cmd   │  │  HOLD / PAUSE        │  │
│  └──────────────┘  └──────────────┘  │  REDUCE / OPTIMIZE   │  │
│                                      └──────────────────────┘  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │  A/B Testing │  │  Keyword     │  │  Creative Service    │  │
│  │  Service     │  │  Service     │  │                      │  │
│  │              │  │              │  │  DALL-E 3 image gen  │  │
│  │  Generate    │  │  Research    │  │  Ad variations       │  │
│  │  variants    │  │  Expand      │  │  Policy checker      │  │
│  │  Track stats │  │  Negatives   │  │  Creative briefs     │  │
│  │  Pick winner │  │  Long-tail   │  │                      │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                 │
│  ┌──────────────┐                                               │
│  │  Email       │                                               │
│  │  Service     │                                               │
│  │  SMTP / TLS  │                                               │
│  │  Templates   │                                               │
│  └──────────────┘                                               │
└─────────────────────────────────────────────────────────────────┘

LAYER 7 — DATABASE LAYER
┌─────────────────────────────────────────────────────────────────┐
│                    DATABASE LAYER                               │
│                                                                 │
│  ┌────────────────────────────────────────────────────────┐    │
│  │              POSTGRESQL (Primary DB)                   │    │
│  │                                                        │    │
│  │  users          id, email, password, name, active      │    │
│  │      │                                                 │    │
│  │  workspaces     id, name, owner_id(FK→users)           │    │
│  │      │                                                 │    │
│  │  campaigns      id, workspace_id, name, platform       │    │
│  │      │          budget, status, objective, ad_copy     │    │
│  │      │          google_campaign_resource               │    │
│  │      │          meta_campaign_id, meta_ad_set_id       │    │
│  │      │          ctr, spend, roi, landing_url           │    │
│  │      │                                                 │    │
│  │  analytics      id, campaign_id, impressions, clicks   │    │
│  │                 ctr, cpc, spend, roi, recorded_at      │    │
│  │                                                        │    │
│  │  memory_logs    id, workspace_id, type, content        │    │
│  │                 roi_score, embedding_id, created_at    │    │
│  │                                                        │    │
│  │  agent_tasks    id, campaign_id, agent_name, status    │    │
│  │                 input_data, output_data, error         │    │
│  │                                                        │    │
│  │  ab_tests       id, campaign_id, variant_a, variant_b  │    │
│  │                 impressions, clicks, conversions        │    │
│  │                 winner, is_complete, min_impressions    │    │
│  └────────────────────────────────────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────┐  ┌────────────────────────────────┐  │
│  │  REDIS               │  │  PINECONE (Vector DB)          │  │
│  │                      │  │                                │  │
│  │  DB 0: App cache     │  │  Index: ai-ads-memory          │  │
│  │    session context   │  │  Dimensions: 1536              │  │
│  │    rate limit state  │  │  Metric: cosine                │  │
│  │                      │  │  Metadata: workspace_id, type  │  │
│  │  DB 1: Celery broker │  │  Namespaced per workspace      │  │
│  │  DB 2: Celery result │  │                                │  │
│  └──────────────────────┘  └────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

LAYER 8 — BACKGROUND TASK QUEUE
┌─────────────────────────────────────────────────────────────────┐
│              CELERY TASK QUEUE (Redis Broker)                   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                 CELERY WORKER                           │   │
│  │              (4 concurrent processes)                   │   │
│  │                                                         │   │
│  │  campaign_tasks.py                                      │   │
│  │    launch_campaign_task    — run all 8 agents async     │   │
│  │                                                         │   │
│  │  analytics_tasks.py                                     │   │
│  │    sync_all_analytics      — pull stats from APIs       │   │
│  │                                                         │   │
│  │  optimization_tasks.py                                  │   │
│  │    run_optimization_all    — optimize all campaigns      │   │
│  │                                                         │   │
│  │  scaling_tasks.py                                       │   │
│  │    auto_scale_all_workspaces — AI budget decisions      │   │
│  │                                                         │   │
│  │  notification_tasks.py                                  │   │
│  │    notify_campaign_launched — email + plugin hooks      │   │
│  │    notify_optimization      — email + plugin hooks      │   │
│  │    notify_ab_winner         — email + plugin hooks      │   │
│  │                                                         │   │
│  │  report_tasks.py                                        │   │
│  │    generate_weekly_reports  — AI report + email         │   │
│  │                                                         │   │
│  │  memory_tasks.py                                        │   │
│  │    compress_all_memories    — summarize old context     │   │
│  │    cleanup_old_memories     — delete 90+ day records    │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              CELERY BEAT SCHEDULER                      │   │
│  │                                                         │   │
│  │  Every  1 hour   →  sync_all_analytics                  │   │
│  │  Every  6 hours  →  run_optimization_all                │   │
│  │  Every  6 hours  →  auto_scale_all_workspaces           │   │
│  │  Every  24 hours →  compress_all_memories               │   │
│  │  Every  7 days   →  generate_weekly_reports             │   │
│  │  Every  7 days   →  cleanup_old_memories                │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

LAYER 9 — PLUGIN MARKETPLACE
┌─────────────────────────────────────────────────────────────────┐
│                   PLUGIN SYSTEM                                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │              PLUGIN REGISTRY                            │   │
│  │  install → validate config → instantiate → store        │   │
│  │  uninstall → call on_uninstall → remove instance        │   │
│  │  emit_hook → broadcast event to all active plugins      │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  HOOK EVENTS:                                                   │
│    on_campaign_launched → on_optimization_done → on_ab_winner  │
│                                                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │   Slack     │ │  WhatsApp   │ │   Shopify   │              │
│  │  Notifier   │ │  Notifier   │ │    Sync     │              │
│  │  webhook    │ │  Business   │ │  product    │              │
│  │  alerts     │ │  API msgs   │ │  → ad copy  │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐              │
│  │  Creative   │ │   Report    │ │  Audience   │              │
│  │  AI Plugin  │ │  Generator  │ │  Expander   │              │
│  │  DALL-E     │ │  weekly PDF │ │  lookalike  │              │
│  │  image gen  │ │  + email    │ │  interests  │              │
│  └─────────────┘ └─────────────┘ └─────────────┘              │
└─────────────────────────────────────────────────────────────────┘

LAYER 10 — EXTERNAL APIs
┌─────────────────────────────────────────────────────────────────┐
│                   EXTERNAL API INTEGRATIONS                     │
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │     GOOGLE ADS API       │  │     META ADS API         │    │
│  │                          │  │                          │    │
│  │  CampaignService         │  │  /campaigns              │    │
│  │  AdGroupService          │  │  /adsets                 │    │
│  │  AdGroupAdService        │  │  /adcreatives            │    │
│  │  KeywordCriterionService │  │  /ads                    │    │
│  │  GoogleAdsService(stats) │  │  /insights               │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │     OPENAI API           │  │     PINECONE API         │    │
│  │                          │  │                          │    │
│  │  GPT-4o  (all agents)    │  │  upsert vectors          │    │
│  │  DALL-E 3 (image gen)    │  │  query semantic search   │    │
│  │  Whisper (voice STT)     │  │  filter by workspace     │    │
│  │  TTS (voice reply)       │  │                          │    │
│  │  Embeddings (1536 dim)   │  │                          │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
│                                                                 │
│  ┌──────────────────────────┐  ┌──────────────────────────┐    │
│  │  WEB SCRAPING TARGETS    │  │  NOTIFICATION APIs       │    │
│  │                          │  │                          │    │
│  │  Competitor websites     │  │  SMTP (email reports)    │    │
│  │  Reddit JSON API         │  │  Slack Webhooks          │    │
│  │  Google News RSS         │  │  WhatsApp Business API   │    │
│  │  Google Trends           │  │  Shopify REST API        │    │
│  └──────────────────────────┘  └──────────────────────────┘    │
└─────────────────────────────────────────────────────────────────┘

LAYER 11 — DEVOPS & INFRASTRUCTURE
┌─────────────────────────────────────────────────────────────────┐
│          DIGITALOCEAN VPS INFRASTRUCTURE                        │
│            Ubuntu 22.04 LTS — 4 vCPU / 8GB RAM                 │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  DOCKER COMPOSE                         │   │
│  │                                                         │   │
│  │  ┌───────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │ backend   │ │frontend  │ │ postgres │ │  redis   │  │   │
│  │  │ :8000     │ │ :3000    │ │ :5432    │ │ :6379    │  │   │
│  │  └───────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  │  ┌───────────┐ ┌──────────┐ ┌──────────┐               │   │
│  │  │  celery   │ │  celery  │ │  flower  │               │   │
│  │  │  worker   │ │   beat   │ │  :5555   │               │   │
│  │  └───────────┘ └──────────┘ └──────────┘               │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  ┌───────────────────┐  ┌───────────────────────────────────┐  │
│  │   MONITORING      │  │   CI/CD                           │  │
│  │                   │  │                                   │  │
│  │  Prometheus       │  │  scripts/deploy.sh                │  │
│  │  ELK (logs)       │  │  git pull → build → migrate       │  │
│  │  Sentry (errors)  │  │  Makefile shortcuts               │  │
│  │  Flower (celery)  │  │  scripts/backup_db.sh (daily)     │  │
│  └───────────────────┘  └───────────────────────────────────┘  │
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                  SECURITY                               │   │
│  │  JWT Auth    OAuth2    RBAC    AES-256    Tenant Isolation│  │
│  │  Rate Limiting    CORS    SSL/TLS (Let's Encrypt)         │  │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘

FULL END-TO-END REQUEST FLOW
USER TYPES: "Run a $500 Google Ads campaign for my shoe store"
                              │
                              ▼
         ┌─────────────────────────────┐
         │   Next.js Frontend          │
         │   useAgentStream WebSocket  │
         └─────────────┬───────────────┘
                       │  WebSocket connect
                       ▼
         ┌─────────────────────────────┐
         │   Nginx :443                │
         │   /ws/ → backend:8000       │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   FastAPI ws_agent.py       │
         │   JWT auth validated        │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   LangGraph Orchestrator    │
         │                             │
         │   1. load_memory            │──→ Redis + PG + Pinecone
         │      ↓                      │       context returned
         │   2. ResearchAgent          │──→ GPT-4o
         │      ↓  stream event        │←── "Research Agent: started"
         │   3. StrategyAgent          │──→ GPT-4o
         │      ↓  stream event        │←── "Strategy Agent: complete"
         │   4. CopywritingAgent       │──→ GPT-4o
         │      ↓  stream event        │
         │   5. CreativeAgent          │──→ GPT-4o + DALL-E 3
         │      ↓  stream event        │
         │   6. ValidatorAgent         │──→ GPT-4o quality check
         │      ↓                      │
         │   APPROVED? ─── NO ────────→ retry copywriting (max 2x)
         │      │ YES                  │
         │   7. save_memory            │──→ Redis + PG + Pinecone
         │      ↓                      │
         │   done event + result       │
         └─────────────┬───────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   Celery Task (background)  │
         │   launch_campaign_task      │
         │       ↓                     │
         │   ExecutionAgent            │
         │       ├──→ Google Ads API   │──→ campaign created
         │       └──→ Meta Ads API     │──→ campaign created
         │       ↓                     │
         │   notify_campaign_launched  │──→ Email + Slack + WhatsApp
         └─────────────────────────────┘
                       │
                       ▼
         ┌─────────────────────────────┐
         │   Frontend receives result  │
         │   AgentStreamPanel updates  │
         │   Dashboard shows campaign  │
         └─────────────────────────────┘

EVERY 1 HOUR  → analytics synced from Google/Meta APIs
EVERY 6 HOURS → OptimizationAgent reviews ROI → scales/pauses
EVERY 6 HOURS → BudgetScaler reviews 14-day history → AI decision
EVERY 24 HOURS → Memory compressed and summarized
EVERY 7 DAYS  → Weekly PDF report emailed to workspace owner

COMPLETE FILE TREE
ai-ads-consultant/
├── backend/
│   ├── agents/
│   │   ├── base_agent.py
│   │   ├── research_agent.py
│   │   ├── strategy_agent.py
│   │   ├── copywriting_agent.py
│   │   ├── creative_agent.py
│   │   ├── execution_agent.py
│   │   ├── optimization_agent.py
│   │   ├── validator_agent.py
│   │   └── memory_agent.py
│   ├── api/
│   │   ├── auth.py
│   │   ├── users.py
│   │   ├── workspace.py
│   │   ├── campaign.py
│   │   ├── agent.py
│   │   ├── analytics.py
│   │   ├── ws_agent.py
│   │   ├── competitor.py
│   │   ├── voice.py
│   │   ├── ab_test.py
│   │   ├── plugins.py
│   │   ├── trends.py
│   │   ├── budget_scaling.py
│   │   ├── creatives.py
│   │   └── keywords.py
│   ├── core/
│   │   ├── config.py
│   │   ├── database.py
│   │   ├── security.py
│   │   ├── orchestrator.py
│   │   ├── websocket_manager.py
│   │   ├── error_handler.py
│   │   ├── middleware.py
│   │   ├── celery_app.py
│   │   ├── plugin_registry.py
│   │   └── dependencies.py
│   ├── memory/
│   │   ├── short_term.py
│   │   ├── long_term.py
│   │   ├── vector_memory.py
│   │   └── context_builder.py
│   ├── services/
│   │   ├── google_ads_service.py
│   │   ├── meta_ads_service.py
│   │   ├── competitor_scraper.py
│   │   ├── voice_service.py
│   │   ├── ab_testing.py
│   │   ├── budget_scaler.py
│   │   ├── trend_detector.py
│   │   ├── email_service.py
│   │   ├── keyword_service.py
│   │   └── creative_service.py
│   ├── tasks/
│   │   ├── campaign_tasks.py
│   │   ├── analytics_tasks.py
│   │   ├── optimization_tasks.py
│   │   ├── scaling_tasks.py
│   │   ├── notification_tasks.py
│   │   ├── report_tasks.py
│   │   └── memory_tasks.py
│   ├── plugins/
│   │   └── builtin/
│   │       ├── slack_notifier.py
│   │       ├── whatsapp_notifier.py
│   │       ├── shopify_sync.py
│   │       ├── creative_ai.py
│   │       ├── report_generator.py
│   │       └── audience_expander.py
│   ├── utils/
│   │   ├── constants.py
│   │   ├── helpers.py
│   │   ├── validators.py
│   │   └── formatters.py
│   ├── alembic/
│   │   └── env.py
│   ├── main.py
│   ├── requirements.txt
│   ├── Dockerfile
│   └── .env
│
├── frontend/
│   └── src/
│       ├── app/
│       │   ├── layout.jsx
│       │   ├── page.jsx
│       │   ├── (auth)/
│       │   │   ├── layout.jsx
│       │   │   ├── login/page.jsx
│       │   │   └── register/page.jsx
│       │   └── (app)/
│       │       ├── layout.jsx
│       │       ├── dashboard/page.jsx
│       │       ├── chat/page.jsx
│       │       ├── analytics/page.jsx
│       │       ├── campaigns/
│       │       │   ├── new/page.jsx
│       │       │   └── [id]/page.jsx
│       │       ├── trends/page.jsx
│       │       ├── competitor/page.jsx
│       │       ├── ab-test/page.jsx
│       │       ├── budget/page.jsx
│       │       ├── creatives/page.jsx
│       │       ├── voice/page.jsx
│       │       ├── plugins/page.jsx
│       │       └── settings/page.jsx
│       ├── components/
│       │   ├── Sidebar.jsx
│       │   ├── Navbar.jsx
│       │   ├── ProtectedRoute.jsx
│       │   ├── AgentStreamPanel.jsx
│       │   ├── VoiceCommand.jsx
│       │   ├── CampaignCard.jsx
│       │   ├── StatCard.jsx
│       │   ├── AnalyticsChart.jsx
│       │   ├── Toast.jsx
│       │   ├── LoadingSpinner.jsx
│       │   └── Modal.jsx
│       ├── hooks/
│       │   └── useAgentStream.js
│       ├── store/
│       │   ├── authStore.js
│       │   └── campaignStore.js
│       └── lib/
│           ├── api.js
│           └── utils.js
│   ├── next.config.js
│   ├── tailwind.config.js
│   ├── Dockerfile
│   └── .env.local
│
├── scripts/
│   ├── deploy.sh
│   └── backup_db.sh
├── docker-compose.yml
├── nginx.conf
├── Makefile
└── alembic.ini

TECHNOLOGY STACK SUMMARY
CATEGORY        TECHNOLOGY              PURPOSE
─────────────────────────────────────────────────────────────
AI Engine       OpenAI GPT-4o           All 8 AI agents
AI Images       DALL-E 3                Creative generation
AI Voice        Whisper + TTS           Voice commands
AI Framework    LangChain + LangGraph   Agent orchestration
Embeddings      OpenAI 1536-dim         Vector memory

Backend         Python 3.11 + FastAPI   REST API + WebSocket
Task Queue      Celery + Redis          Background jobs
Scheduler       Celery Beat             Cron-style scheduling

Frontend        Next.js 14 + React 18   UI framework
Styling         Tailwind CSS            Component styling
State           Zustand + Persist       Global state
HTTP Client     Axios                   API calls
Real-time       WebSocket native        Agent streaming

Primary DB      PostgreSQL 15           All business data
Cache/Queue     Redis 7                 Sessions + Celery
Vector DB       Pinecone                Semantic memory

Ads Platform    Google Ads API v14      Google campaign mgmt
Ads Platform    Meta Marketing API v19  Facebook/Instagram ads

Proxy           Nginx                   Reverse proxy + SSL
Containers      Docker + Compose        All services
SSL             Let's Encrypt           HTTPS certificates
Hosting         DigitalOcean VPS        Ubuntu 22.04 LTS

Monitoring      Prometheus              Metrics collection
Logging         ELK Stack               Log aggregation
Errors          Sentry                  Error tracking
Celery UI       Flower                  Task monitoring

Migrations      Alembic                 DB schema versioning

SECURITY ARCHITECTURE
REQUEST FLOW SECURITY:

Browser → HTTPS/TLS → Nginx → JWT Verify → Rate Limit → API

AUTHENTICATION:    JWT tokens (HS256, 24h expiry)
AUTHORIZATION:     RBAC per workspace (owner / member)
MULTI-TENANCY:     workspace_id isolation on all DB queries
ENCRYPTION:        AES-256 for stored credentials
PASSWORDS:         bcrypt hashing (never plain text)
API KEYS:          stored in .env, never in DB or logs
RATE LIMITING:     100 requests / 60 seconds per IP
CORS:              configured per environment
INPUT:             sanitized via validators.py before processing
