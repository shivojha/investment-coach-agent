# Investment Coach Agent

A conversational AI investment coach built on Azure.

## Structure

```
investment-coach-agent/
├── backend/      FastAPI + Semantic Kernel agent
├── frontend/     Vite + React + Tailwind chat UI
├── infra/        Bicep infrastructure as code
└── docs/         Requirements, design, ADRs
```

## Azure Services (~$5-10/month showcase cost)

| Service | Tier | Cost |
| ------- | ---- | ---- |
| Azure OpenAI (GPT-4o + embeddings) | S0 pay-per-token | ~$1-5 |
| Azure AI Search | FREE | $0 |
| Azure Cosmos DB | Serverless | ~$0 |
| Azure Container Apps | Consumption | ~$0 idle |
| Azure Container Registry | Basic | ⚠️ ~$5/month |
| Azure Static Web Apps | FREE | $0 |
| Azure Key Vault | Standard | $0 |
| Azure Monitor / App Insights | FREE tier | $0 |

## Local Development

### Backend
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill in your values
uvicorn app.main:app --reload
```

### Frontend
```bash
cd frontend
npm install
npm run dev            # proxies /v1/* to localhost:8000
```

## Docs

- [Requirements](docs/requirements.md)
- [Architecture Design](docs/design.md)
- [ADR-001 Agent Orchestration](docs/adr/ADR-001-agent-orchestration-framework.md)
- [ADR-002 LLM Provider](docs/adr/ADR-002-llm-provider.md)
- [ADR-003 Long-Term Memory](docs/adr/ADR-003-long-term-memory-vector-store.md)
- [ADR-004 Short-Term Memory](docs/adr/ADR-004-short-term-memory-chat-history.md)
- [ADR-005 Deployment Platform](docs/adr/ADR-005-deployment-platform.md)
- [ADR-006 Language & SDK](docs/adr/ADR-006-language-and-sdk.md)
- [ADR-007 API Layer](docs/adr/ADR-007-api-layer.md)
