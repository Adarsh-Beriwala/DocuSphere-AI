# DocuSphere AI

A local-first RAG documentation assistant built with **React**, **FastAPI**, **LangChain**, **ChromaDB** and a **Groq-hosted language model**. Upload a text-based PDF or ingest a public webpage, then ask questions and inspect retrieved source excerpts.

## Features

- Email/password signup and login with hashed passwords and JWT authentication.
- Per-user document records and retrieval filtering.
- Ingest text-based PDFs with page metadata and public HTML webpages.
- Recursive character chunking, Hugging Face embeddings (`all-mpnet-base-v2`) and ChromaDB vector search.
- Configurable cosine-distance relevance gate, optional query rewriting and source excerpts.
- Clickable inline source references that navigate to retrieved excerpts.
- SQLite-persisted document list and per-user chat history (restored after refresh or login).
- Delete an ingested document or clear your saved chat.

## Repository layout

```text
DocuSphere-AI/
├── docusphere-backend/    # FastAPI, JWT, SQLite, RAG, ChromaDB, tests
├── docusphere-frontend/   # React UI and Axios client
├── README.md
└── .gitignore
```

## Local setup (Windows / PowerShell)

Requires **Python 3.11** and a recent **Node.js LTS** release, plus a [Groq API key](https://console.groq.com/keys).

### Backend

```powershell
cd docusphere-backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Edit `docusphere-backend/.env`: replace `GROQ_API_KEY` with your real API key and `JWT_SECRET` with the generated secret (32+ characters). Keep `.env` private. The default LLM is `openai/gpt-oss-20b` via Groq. Then start the backend:

```powershell
.\.venv\Scripts\python.exe run_server.py
```

Check <http://127.0.0.1:8000/health> or browse the interactive FastAPI docs at <http://127.0.0.1:8000/docs>. The public Hugging Face embedding model downloads on the first run.

### Frontend (new terminal from the repository root)

```powershell
cd docusphere-frontend
npm install
npm start
```

Open <http://localhost:3000>. The frontend defaults to `http://127.0.0.1:8000` for API calls.

## API overview

| Method | Endpoint | Function |
| --- | --- | --- |
| GET | `/health` | Health check |
| POST | `/auth/register` | Register an account |
| POST | `/auth/login` | Sign in |
| GET | `/auth/me` | Current user |
| POST | `/ingest/pdf` | Ingest a PDF |
| POST | `/ingest/url` | Ingest a webpage |
| GET | `/documents` | List owned documents |
| DELETE | `/documents/{document_id}` | Remove an owned document |
| POST | `/query` | Ask a grounded question |
| GET | `/chat/history` | Load saved messages |
| DELETE | `/chat/history` | Clear saved messages |

## Data and security

ChromaDB embeddings, SQLite user accounts and chat history live in `docusphere-backend/data/` and are **not committed**. The `.env` file containing secrets is ignored. `.env.example` contains only placeholders. Passwords are stored as hashes.

This is an interview/demo application, **not a production security audit**. Publicly hosted URL ingestion would need additional server-side request forgery (SSRF) hardening. A low cosine distance is not proof that a passage supports the answer; prompt instructions and the relevance gate reduce some unsupported answers but do not eliminate hallucinations. Inline citations are navigable pointers to retrieved excerpts, not verified sentence-level citations. The previously observed raw-string false rejection remains a known retrieval issue that requires further diagnostics.
