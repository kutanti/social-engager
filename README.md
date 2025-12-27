# Social Engager Deep Research Agent

An AI-powered deep research agent that discovers trending positive news in AI, Science, and Technology, researches topics thoroughly, generates engaging tweets, and automatically posts to X daily.

## Features

- **Trend Discovery**: Finds trending positive news using Tavily API
- **Deep Research**: Thoroughly investigates topics with iterative search
- **Smart Tweet Generation**: Creates engaging tweets with adaptive styling
- **Content Safety**: Multi-layered guardrails prevent off-topic or harmful content
- **Automatic Posting**: Posts directly to X with rate limit handling
- **Azure Functions Ready**: Deploy as a serverless function with timer trigger

## Installation

### Prerequisites

- Python 3.11 or later
- [uv](https://docs.astral.sh/uv/) package manager (recommended)
- Azure Functions Core Tools (for Azure deployment)

### Local Setup

1. Clone the repository:
```bash
cd social_engager
```

2. Install dependencies:
```bash
uv sync
```

3. Configure environment variables:
```bash
cp env.example .env
# Edit .env with your API keys
```

### Required API Keys

| Service | Purpose | Get Key |
|---------|---------|---------|
| Azure OpenAI | LLM for agents | [Azure Portal](https://portal.azure.com) |
| Tavily | News search | [tavily.com](https://tavily.com) |
| X (Twitter) | Posting tweets | [developer.twitter.com](https://developer.twitter.com) |

### Azure OpenAI Setup

1. Create an Azure OpenAI resource in Azure Portal
2. Deploy a model (GPT-4.1 recommended)
3. Note your endpoint URL and API key
4. Set the deployment name in your `.env` file as `AZURE_GPT41_DEPLOYMENT`

## Usage

### Run Locally

```bash
# Dry run (logs only, no posting)
python -m social_engager.cli --dry-run

# Live posting
python -m social_engager.cli --live

# Check environment configuration
python -m social_engager.cli --check
```

## Azure Functions Deployment

The project is ready to deploy as an Azure Function with a daily timer trigger.

### Project Structure for Azure Functions

```
social_engager/
├── function_app.py              # Azure Function entry point
├── host.json                    # Azure Functions host config
├── local.settings.json.example  # Local settings template
├── requirements.txt             # Python dependencies
├── .funcignore                  # Files to exclude from deployment
└── src/social_engager/          # Main application code
```

### Local Testing with Azure Functions

1. Install Azure Functions Core Tools:
```bash
brew install azure-functions-core-tools@4
```

2. Copy and configure local settings:
```bash
cp local.settings.json.example local.settings.json
# Edit local.settings.json with your API keys
```

3. Start the function locally:
```bash
func start
```

4. Test the endpoints:
```bash
# Health check
curl http://localhost:7071/api/health

# Manual trigger (requires function key in production)
curl -X POST http://localhost:7071/api/run
```

### Deploy to Azure

1. Create Azure Function App:
```bash
az functionapp create \
  --resource-group your-rg \
  --consumption-plan-location eastus \
  --runtime python \
  --runtime-version 3.11 \
  --functions-version 4 \
  --name social-engager-func \
  --storage-account yourstorageaccount
```

2. Set environment variables:
```bash
az functionapp config appsettings set \
  --name social-engager-func \
  --resource-group your-rg \
  --settings \
    AZURE_OPENAI_ENDPOINT="https://your-resource.openai.azure.com/" \
    AZURE_OPENAI_API_KEY="your-key" \
    AZURE_OPENAI_API_VERSION="2024-02-15-preview" \
    AZURE_GPT41_DEPLOYMENT="gpt-41" \
    TAVILY_API_KEY="your-tavily-key" \
    X_API_KEY="your-x-key" \
    X_API_SECRET="your-x-secret" \
    X_ACCESS_TOKEN="your-token" \
    X_ACCESS_TOKEN_SECRET="your-token-secret" \
    X_BEARER_TOKEN="your-bearer" \
    DRY_RUN="false"
```

3. Deploy:
```bash
func azure functionapp publish social-engager-func
```

### Function Endpoints

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| `/api/health` | GET | Anonymous | Health check |
| `/api/run` | POST | Function Key | Manual trigger |
| Timer | - | - | Daily at 9 AM UTC |

## Architecture

The agent follows a four-phase workflow:

```
Discover → Research → Generate → Post
```

1. **Trend Discovery**: Finds trending positive news in AI/Science/Tech
2. **Deep Research**: Investigates the topic with multiple searches
3. **Tweet Generation**: Creates engaging content with adaptive styling
4. **Content Safety**: Validates through multiple guardrail layers
5. **Posting**: Publishes to X (or logs in dry run mode)

## Content Safety

Multi-layered guardrails ensure safe, on-topic content:

1. **Topic Validation**: Pydantic schemas enforce allowed categories
2. **Azure OpenAI Moderation**: LLM-based content safety check
3. **Keyword Blocklist**: Filters politics, controversy, negativity
4. **Dry Run Mode**: Test without posting
5. **Audit Logging**: Full traceability

## License

MIT
