# Insight Agent for Document-Centric Analytics (Local IDP + AI)

This project is a **local, zero-cost prototype** of an AI-powered **Insight Agent** that sits on top of an Intelligent Document Processing (IDP) pipeline.

It ingests PDF documents (e.g., invoices, bank statements, forms), extracts structured data, and lets you **ask natural language questions** like:

- "What did I spend on rent in the last 3 months?"
- "Which vendors are above $5,000 this quarter?"
- "Show me anomalies in monthly spend and the supporting documents."

The implementation is designed to **mirror how this would run on AWS** (Textract, Bedrock, S3, RDS, OpenSearch), but uses **100% free, local tools** instead.

---

## Architecture Overview

### Conceptual Flow

1. **Ingestion & IDP**
   - PDFs are stored in `data/raw_docs/`.
   - A Python-based IDP pipeline:
     - Uses OCR (Tesseract) and PDF parsing (`pdfplumber`) to extract text.
     - Classifies document types (invoice, statement, etc.).
     - Extracts key fields (dates, amounts, vendors, categories).
   - Structured outputs are saved as JSON/CSV and loaded into a relational database.

2. **Storage & Analytics**
   - All structured data is stored in a relational database (PostgreSQL via Docker, or SQLite).
   - Derived metrics (e.g., monthly totals, category breakdowns, vendor stats) are computed and exposed as reusable "metrics functions".

3. **RAG + Vector Search**
   - Document chunks and summaries are embedded with a free `sentence-transformers` model.
   - Embeddings are stored in a local **FAISS** index (no external vector DB).
   - This enables the agent to retrieve **supporting documents** for its answers.

4. **Insight Agent (LLM + Tools)**
   - A local LLM (via [Ollama](https://ollama.com/)) provides reasoning and natural language generation.
   - The agent is wired with tools (using LangChain/LlamaIndex-style patterns):
     - `sql_tool`: run parameterized SQL queries on the transactional DB.
     - `metrics_tool`: call pre-defined Python functions for KPIs.
     - `rag_tool`: search FAISS for relevant document snippets.
   - The agent decides which tools to call based on the user's query, aggregates the results, and explains the insight in plain language, referencing underlying data and documents.

5. **API & UI**
   - **Backend:** FastAPI application exposing:
     - `POST /chat/insights` – main endpoint for the Insight Agent.
   - **Frontend:** Streamlit app for:
     - Chatting with the agent.
     - Viewing charts (monthly spend, vendor breakdowns).
     - Inspecting retrieved documents and extracted fields.

---

## Stack (Local Analogues of AWS Services)

This project intentionally mirrors an AWS-native design:

| AWS Service (Target)      | Local / Free Equivalent             |
|---------------------------|-------------------------------------|
| S3 (document storage)     | `data/raw_docs/` on local disk      |
| Textract (OCR)            | Tesseract + `pytesseract`           |
| Comprehend / Bedrock NLU  | Local LLM + `sentence-transformers` |
| RDS / Aurora              | PostgreSQL (Docker) or SQLite       |
| OpenSearch / Kendra       | FAISS vector index                  |
| Bedrock LLM (agents)      | Ollama + LangChain/LlamaIndex       |
| Lambda / Step Functions   | Python services + scripts           |
| QuickSight                | Streamlit charts + notebooks        |

This makes it easy to **lift and shift the architecture to AWS** later by replacing the local components with managed services.

---

## Features

- ✅ End-to-end IDP pipeline:
  - OCR + text extraction from PDFs.
  - Document classification.
  - Field extraction into structured tables.
- ✅ RAG-enabled insight agent:
  - Combines SQL analytics with document retrieval.
  - Answers questions in natural language and cites source docs.
- ✅ Analytics & Insights:
  - Precomputed metrics (e.g., monthly spend, category breakdowns).
  - Simple visualizations in Streamlit / Jupyter.
- ✅ Agentic behavior:
  - Chooses between querying the database, running metrics, or retrieving document context.
  - Uses tools to ground responses in actual data rather than hallucinating.

---

## Prerequisites

1. **Python 3.9+**
2. **PostgreSQL** (via Docker Compose) or SQLite
3. **Ollama** installed and running locally
   - Install from: https://ollama.com/
   - Pull a model: `ollama pull llama3` (or `mistral`, `codellama`, etc.)
4. **Tesseract OCR** (for image OCR)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd insight-agent-idp-local
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables:**
   Create a `.env` file (optional, defaults are provided):
   ```env
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=insight_agent
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   ```

5. **Start PostgreSQL (via Docker):**
   ```bash
   docker-compose up -d postgres
   ```

6. **Verify Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

---

## Usage

### 1. Initialize Database

Create tables and optionally seed with sample data:

```bash
# Create tables only
python scripts/seed_db.py 0

# Create tables + seed with 50 sample transactions
python scripts/seed_db.py
```

### 2. Download Sample Documents (Optional)

You can download a free invoice/receipt dataset from Hugging Face:

```bash
# Install dataset library
pip install datasets pillow

# Download sample (first 20 images for testing)
python3 scripts/download_huggingface_dataset.py --split train --max-images 20

# Or download full training set (2,040 images)
python3 scripts/download_huggingface_dataset.py --split train
```

See `DATASET_GUIDE.md` for detailed instructions.

### 3. Ingest Documents

Place PDF/image files in `data/raw_docs/` and run:

```bash
python3 scripts/ingest_docs.py
```

This will:
- Extract text from PDFs/images (using OCR for images)
- Classify document types
- Extract structured fields
- Create transaction records

### 4. Build Vector Embeddings

After ingesting documents, build the FAISS index:

```bash
python3 scripts/build_embeddings.py
```

### 5. Start the API Server

```bash
python3 -m app.main
# Or: uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`

### 6. Start the Streamlit Frontend

In a new terminal:

```bash
streamlit run frontend/streamlit_app.py
```

Navigate to `http://localhost:8501` in your browser.

---

## API Usage

### Chat Endpoint

```bash
curl -X POST "http://localhost:8000/chat/insights" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What did I spend on rent in the last 3 months?",
    "use_rag": true,
    "use_sql": true
  }'
```

Response:
```json
{
  "answer": "Based on the transaction data...",
  "sources": [...],
  "sql_query": "SELECT SUM(amount) FROM transactions WHERE..."
}
```

---

## Project Structure

```
app/
  main.py           # FastAPI entrypoint
  config.py         # App settings
  db.py             # Database connection (SQLAlchemy)
  models.py         # ORM models (Documents, Transactions, etc.)
  schemas.py        # Pydantic schemas for API requests/responses

  services/
    idp_pipeline.py # OCR + extraction pipeline
    rag.py          # Embedding + FAISS vector search helpers
    sql_tools.py    # Safe SQL wrappers used by the agent
    insights.py     # Metrics / KPI computation functions

  agents/
    insight_agent.py# Core orchestration logic
    tools.py        # Tool definitions exposed to the LLM

  vectorstore/
    faiss_store.py  # FAISS index management

data/
  raw_docs/         # Input PDFs
  processed/        # Extracted JSON/CSV
  embeddings/       # FAISS indexes, metadata

frontend/
  streamlit_app.py  # UI for chat + charts

scripts/
  ingest_docs.py    # CLI: load PDFs into the system
  build_embeddings.py
  seed_db.py
  download_huggingface_dataset.py  # Download invoice/receipt datasets

notebooks/
  exploratory_idp.ipynb
  analytics_demo.ipynb
```

---

## Configuration

Key configuration options in `app/config.py`:

- `OLLAMA_MODEL`: LLM model to use (default: `llama3`)
- `EMBEDDING_MODEL`: Embedding model (default: `all-MiniLM-L6-v2`)
- `FAISS_INDEX_PATH`: Path to FAISS index file
- Database connection settings

---

## Troubleshooting

### Ollama Connection Error

- Ensure Ollama is running: `ollama serve`
- Check the model is available: `ollama list`
- Pull the model if needed: `ollama pull llama3`

### Tesseract OCR Not Found

- Install Tesseract (see Prerequisites)
- On macOS, ensure it's in PATH: `which tesseract`

### Database Connection Error

- Ensure PostgreSQL is running: `docker-compose ps`
- Check connection settings in `.env` or `app/config.py`

### No Documents Found

- Place PDF files in `data/raw_docs/`
- Run `python scripts/ingest_docs.py`

---

## Development

### Running Tests

```bash
# Add tests as needed
pytest tests/
```

### Adding New Document Types

1. Update `classify_document()` in `app/services/idp_pipeline.py`
2. Add extraction function (e.g., `extract_form_fields()`)
3. Update `parse_document()` to handle the new type

### Adding New Metrics

1. Add function to `app/services/insights.py`
2. Update `create_metrics_tool()` in `app/agents/tools.py`

---

## Future Enhancements

- [ ] Support for more document types (receipts, contracts, etc.)
- [ ] Advanced text chunking strategies
- [ ] Multi-turn conversation support
- [ ] Export insights to PDF/Excel
- [ ] Real-time document processing webhooks
- [ ] AWS deployment guide

---

## License

MIT License

---

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
