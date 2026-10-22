# DocuSphere AI

**Ask questions from PDFs and documentation websites — and see where the answers come from.**

DocuSphere AI is a full-stack, **Retrieval-Augmented Generation (RAG)** documentation assistant. Instead of searching through long PDFs or webpages manually, you can add a document, ask a question in plain English, and get an answer based on the information retrieved from your content.

Built with **React, FastAPI, LangChain, ChromaDB, and a Groq-hosted language model**.

## What Can You Do?

- **Upload a PDF** or paste a **public documentation URL** to make its text searchable.
- **Ask questions naturally** without having to search through the document yourself.
- **View the sources** behind an answer using clickable references and text excerpts.
- **Keep your documents private** with login and user-specific document retrieval.
- **Pick up where you left off**: uploaded document records and chat history are saved across refreshes.
- **Manage your workspace** by deleting indexed documents or clearing chat history.

## How It Works

DocuSphere has two main flows:

**1. Document ingestion — making your content searchable**

```text
PDF / Public Webpage
        ↓
   Text Extraction
        ↓
 Chunking + Overlap
        ↓
  MPNet Embeddings
        ↓
      ChromaDB
```

- **PDFs:** `pdfplumber` extracts text and keeps page information when available.
- **Webpages:** `httpx` fetches a public HTML page; `BeautifulSoup` extracts its readable text.
- **Chunking:** LangChain's recursive splitter divides text into manageable, overlapping chunks.
- **Embeddings:** `all-mpnet-base-v2` converts chunks into vectors for semantic search.
- **Storage:** ChromaDB saves the chunks, embeddings, and source metadata for future questions.

**2. Question answering — finding and explaining the answer**

```text
   Your Question
        ↓
  Semantic Search
        ↓
 Relevant Document Chunks
        ↓
 Groq-hosted Language Model
        ↓
 Answer + Clickable Sources
```

The system searches **only the signed-in user's documents**, checks whether the retrieved chunks pass a configurable relevance threshold, and sends the relevant text to the language model as context. By default it retrieves up to **8 chunks** and uses a **0.65 cosine-distance cutoff** (a relevance heuristic, not an accuracy score). If it cannot find a sufficiently relevant match, it can return a *"not found in the documentation"* response instead of generating an answer.

## Tech Stack

| Part | Technology | Purpose |
| --- | --- | --- |
| Frontend | React, Axios | Uploads, chat, document list, source viewer |
| Backend | Python, FastAPI | APIs, authentication, document processing |
| PDF & web extraction | pdfplumber, httpx, BeautifulSoup | Read text from supported sources |
| RAG pipeline | LangChain | Text splitting and model integrations |
| Embedding model | Hugging Face `all-mpnet-base-v2` | Turn text into searchable vectors |
| Vector database | ChromaDB | Store and retrieve relevant document chunks |
| Language model | Groq API (default: `openai/gpt-oss-20b`) | Generate context-based answers |
| Application database | SQLite | Users, document records, saved chats |
| Authentication | JWT, password hashing | Sign-in and user-specific access |

## Run It Locally

### Prerequisites

- **Python 3.11**
- **Node.js** (a recent LTS version) and npm
- A **[Groq API key](https://console.groq.com/keys)**
- Internet access for dependency installation, the first embedding-model download, and Groq API requests

These commands use **Windows PowerShell**. Open two terminals: one for the backend and one for the frontend.

### Step 1 — Get the project

```powershell
git clone https://github.com/Adarsh-Beriwala/DocuSphere-AI.git
cd DocuSphere-AI
```

### Step 2 — Set up the backend (Terminal 1)

```powershell
cd docusphere-backend
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Open `docusphere-backend/.env` and set:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
JWT_SECRET=your_random_secret_here
```

Generate a secure JWT secret with:

```powershell
.\.venv\Scripts\python.exe -c "import secrets; print(secrets.token_urlsafe(48))"
```

Copy the generated value into `JWT_SECRET`. **Never commit your `.env` file or API key.**

Start the backend:

```powershell
.\.venv\Scripts\python.exe run_server.py
```

- API server: <http://127.0.0.1:8000>
- API documentation: <http://127.0.0.1:8000/docs>

### Step 3 — Start the frontend (Terminal 2)

From the **repository root**, run:

```powershell
cd docusphere-frontend
npm install
npm start
```

Open **<http://localhost:3000>** in your browser.

## Using DocuSphere

1. **Create an account** or sign in.
2. **Upload a text-based PDF** or enter a public webpage URL.
3. **Wait for ingestion** to finish; the document will appear in your document list.
4. **Ask a question** about the uploaded content.
5. **Open a citation** to inspect the matching source excerpt or PDF page.
6. **Return later** to see your saved documents and chat history.

**Supported inputs:** text-based PDFs up to **10 MB / 150 pages**, and public HTML/text webpages up to **1 MB**.

**First run tip:** The embedding model downloads the first time it is needed, so initial document processing may take longer.

## Where Is My Data Stored?

The project uses two local databases, with different jobs:

- **SQLite:** user accounts (hashed passwords), document records, and chat history.
- **ChromaDB:** extracted text chunks, vector embeddings, and document metadata.

Both are stored under `docusphere-backend/data/`, which is excluded from Git. Indexed text remains available after a normal backend restart as long as those files remain intact. **Original PDF files are not retained as a separate permanent file library.**

Document searches use the authenticated user's identity to filter retrieved chunks.

## Project Structure

```text
DocuSphere-AI/
├── docusphere-backend/   # FastAPI, authentication, RAG, databases
├── docusphere-frontend/  # React interface
├── README.md
└── .gitignore
```

For the available API routes and request formats, open the **[interactive API docs](http://127.0.0.1:8000/docs)** after starting the backend.

---

**DocuSphere AI** — Find relevant information in your documents, ask questions naturally, and inspect the sources behind the answers.
