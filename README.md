
# SignalCraft — Brand & Campaign Studio

SignalCraft is an AI-powered brand and campaign management application designed to help marketing teams transform campaign briefs and business information into structured, reusable marketing assets.

The application uses a FastAPI backend, a Streamlit frontend, SQLite for persistent storage, and configurable AI providers to support marketing workflows.

## Features

- **Campaign Planning:** Extract campaign objectives, target audiences, key messages, channels, budgets, and other details from campaign briefs.
- **Content Calendar Generation:** Generate structured content plans with platform-specific captions, hashtags, calls to action, and publishing details.
- **Brand Profile Extraction:** Extract brand identity, target audience, brand voice, preferred phrases, differentiators, and visual guidance from source material.
- **Performance Insights:** Convert campaign performance notes into structured insights, issues, and recommended next actions.
- **Platform-Specific Content Drafts:** Generate different content variations for selected marketing platforms.
- **Draft Versioning:** Save updated drafts and maintain a history of revisions.
- **Persistent Storage:** Store campaigns, calendars, brand profiles, performance reports, and drafts in SQLite.
- **Multi-Provider AI Support:** Configure Groq, Google Gemini, and OpenAI as available AI providers.
- **REST API:** Expose application functionality through FastAPI endpoints.

## Technology Stack

| Component | Technology |
|---|---|
| Frontend | Streamlit |
| Backend | FastAPI |
| AI Integration | LangChain |
| Primary AI Provider | Groq |
| Additional AI Providers | Google Gemini, OpenAI |
| Database | SQLite |
| Data Validation | Pydantic |
| Language | Python |
| Development Environment | Visual Studio Code |

## Project Structure

```text
genaica3/
├── signalcraft.py       # FastAPI backend and AI workflows
├── uisignalcraft.py     # Streamlit frontend
├── requirements.txt     # Python dependencies
├── .gitignore           # Files excluded from Git
├── .env                 # Local API keys and configuration
└── signalcraft.db       # Local SQLite database
```

The `.env` and database files are local runtime files and should not be committed to Git.

## Prerequisites

Before running SignalCraft, install:

- Python 3.10 or later, compatible with the installed dependencies
- Git
- A Groq API key
- Visual Studio Code or another Python development environment

Optional AI providers can be configured with their respective API keys.

## Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/Amar377/SignalCraft-Brand-Campaign-Studio.git
cd SignalCraft-Brand-Campaign-Studio
```

### 2. Create a virtual environment

**Windows PowerShell:**

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

If dependency resolution fails, use the package manager appropriate for your Python environment and the dependency versions in `requirements.txt`.

### 4. Configure environment variables

Create a `.env` file in the project root.

```env
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b

AI_PROVIDER_ORDER=groq

API_URL=http://127.0.0.1:8000
SIGNALCRAFT_DB_PATH=signalcraft.db
```

Replace the placeholder API key with your own Groq API key.

Optional provider configuration:

```env
GOOGLE_API_KEY=your_google_api_key
GEMINI_MODEL=your_supported_gemini_model

OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=your_supported_openai_model
```

Configure only the providers you intend to use. Provider names and model identifiers must be supported by your installed integrations and API account.

**Security:** Never commit API keys, passwords, or other secrets to GitHub.

### 5. Start the FastAPI backend

Open a terminal in the project root and run:

```powershell
uvicorn signalcraft:app --reload
```

The API should be available at:

- API base URL: http://127.0.0.1:8000
- Interactive API documentation: http://127.0.0.1:8000/docs
- Health endpoint: http://127.0.0.1:8000/health

### 6. Start the Streamlit frontend

Open a second terminal, activate the same virtual environment, and run:

```powershell
streamlit run uisignalcraft.py
```

Open the local URL displayed in the terminal.

Ensure the frontend's configured API URL points to the running FastAPI backend.

## API Endpoints

| Method | Endpoint | Purpose |
|---|---|---|
| GET | `/health` | Check API status and configured providers |
| POST | `/campaigns` | Extract and save a campaign plan |
| GET | `/campaigns` | Retrieve saved campaigns |
| PUT | `/campaigns/{cid}` | Update a campaign |
| DELETE | `/campaigns/{cid}` | Delete a campaign |
| POST | `/calendar` | Generate and save a content calendar |
| GET | `/calendar` | Retrieve saved calendars |
| POST | `/brand-profiles` | Extract and save a brand profile |
| GET | `/brand-profiles` | Retrieve saved brand profiles |
| POST | `/performance-insights` | Generate performance insights |
| GET | `/performance-insights` | Retrieve saved reports |
| POST | `/content-drafts` | Generate and save content drafts |
| GET | `/content-drafts` | Retrieve saved drafts |
| PUT | `/content-drafts/{draft_id}` | Update a draft and create a version |
| GET | `/content-drafts/{draft_id}/versions` | Retrieve draft version history |

For request parameters and response schemas, use the interactive documentation at `/docs`.

## Example Workflow

1. Enter a campaign brief in the application.
2. Generate a structured campaign plan.
3. Create a content calendar for selected platforms.
4. Extract a reusable brand profile from brand documentation.
5. Generate platform-specific content drafts.
6. Review and update drafts while retaining version history.
7. Submit campaign performance notes to generate insights and recommended actions.

## Database

SignalCraft uses SQLite to persist application records.

The database stores campaign plans, content calendars, brand profiles, performance reports, content drafts, and draft versions.

The database is created and initialized by the backend when the application starts.

## Configuration and Security

- Keep `.env` out of version control.
- Never expose API keys in source code or screenshots.
- Do not commit virtual environments, Python cache files, or local database files.
- Use environment variables for provider configuration.
- Review AI-generated content before publishing it.
- Verify business claims, dates, pricing, and performance figures before using them externally.

## Current Development Status

SignalCraft is under active development. The application includes backend routes for its core marketing workflows, AI-powered structured generation, SQLite persistence, and draft versioning.

Successful generation and end-to-end frontend integration depend on the installed dependencies, provider configuration, and runtime testing.

## Future Improvements

Potential enhancements include:

- Document and voice-note uploads
- Improved campaign and brand-profile management
- Richer content-calendar editing and export
- Advanced analytics dashboards
- More robust AI fallback and error handling
- Authentication and role-based access
- Automated testing and deployment

## Repository

GitHub: https://github.com/Amar377/SignalCraft-Brand-Campaign-Studio

---

Built with Python, FastAPI, Streamlit, SQLite, and LangChain.
