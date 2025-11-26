# DocSage 

<div align="center">
  <img src="image.png" alt="DocSage Logo" width="150"/>
  
  **Intelligent Document Processing with AI-Powered Analytics**
  
  *Local, zero-cost alternative to AWS Textract + Bedrock*
</div>

---

**DocSage** is a **local, zero-cost platform** for AI-powered document intelligence that sits on top of an Intelligent Document Processing (IDP) pipeline. DocSage features an intelligent AI agent that processes documents and answers questions using natural language.

It ingests PDF documents (e.g., invoices, bank statements, forms), extracts structured data, and lets you **ask natural language questions** like:

- "What did I spend on rent in the last 3 months?"
- "Which vendors are above $5,000 this quarter?"
- "Show me anomalies in monthly spend and the supporting documents."

The implementation is designed to **mirror how this would run on AWS** (Textract, Bedrock, S3, RDS, OpenSearch), but uses **100% free, local tools** instead.

---

## Why this project exists

I built this to practice end-to-end architecture for an intelligent document processing system similar to what you'd run on AWS (Textract + Bedrock + RDS + OpenSearch), but using 100% local, free tools. My learning focus was:

- **Designing a tool-using LLM agent** wired into SQL, metrics, and RAG
- **Building an IDP pipeline** (OCR, classification, field extraction) for financial docs
- **Structuring a FastAPI + Streamlit system** that's easy to "lift-and-shift" to AWS

That makes the learning goal explicit instead of implicit.

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
   - All structured data is stored in **PostgreSQL** (via Docker Compose) by default.
   - SQLite is available as an optional alternative for development.
   - Derived metrics (e.g., monthly totals, category breakdowns, vendor stats) are computed and exposed as reusable "metrics functions".

3. **RAG + Vector Search**
   - Document chunks and summaries are embedded with a free `sentence-transformers` model.
   - Embeddings are stored in a local **FAISS** index (no external vector DB).
   - This enables the agent to retrieve **supporting documents** for its answers.

4. **AI Agent (LLM + Tools)**
   - DocSage features an intelligent AI agent that powers the system.
   - A local LLM (via [Ollama](https://ollama.com/)) provides reasoning and natural language generation.
   - The agent is wired with tools (using LangChain/LlamaIndex-style patterns):
     - `sql_tool`: run parameterized SQL queries on the transactional DB.
     - `metrics_tool`: call pre-defined Python functions for KPIs.
     - `rag_tool`: search FAISS for relevant document snippets.
   - The agent decides which tools to call based on the user's query, aggregates the results, and explains the insight in plain language, referencing underlying data and documents.

5. **API & UI**
   - **Backend:** FastAPI application exposing:
     - `POST /chat/insights` – main endpoint for DocSage's AI agent.
     - `GET /health` – health check endpoint.
     - `GET /docs` – interactive API documentation.
   - **Frontend:** Streamlit app with 8 comprehensive pages:
     - 📊 **Analytics Dashboard** – Time-series analytics, spending trends, vendor analysis, and forecasting.
     - 💬 **Chat** – Natural language interface to interact with DocSage.
     - 📄 **Documents** – Document management with visual overlays, interactive corrections, and real-time upload.
     - ⚠️ **Anomalies** – Automated anomaly detection (duplicates, unusual amounts, missing fields).
     - 🔍 **Document Comparison** – Side-by-side document comparison and price change tracking.
     - 📈 **Insights Report** – AI-generated natural language insights and recommendations.
     - 🔗 **Receipt Matching** – Automatic receipt-to-invoice matching with fuzzy matching.
     - 📤 **Export** – Export data to Excel and Markdown formats.

---

## Stack (Local Analogues of AWS Services)

This project intentionally mirrors an AWS-native design:

| AWS Service (Target)      | Local / Free Equivalent             |
|---------------------------|-------------------------------------|
| S3 (document storage)     | `data/raw_docs/` on local disk      |
| Textract (OCR)            | Tesseract + `pytesseract`           |
| Comprehend / Bedrock NLU  | Local LLM + `sentence-transformers` |
| RDS / Aurora              | PostgreSQL (Docker) - SQLite optional |
| OpenSearch / Kendra       | FAISS vector index                  |
| Bedrock LLM (agents)      | Ollama + LangChain/LlamaIndex       |
| Lambda / Step Functions   | Python services + scripts           |
| QuickSight                | Streamlit charts + notebooks        |

This makes it easy to **lift and shift the architecture to AWS** later by replacing the local components with managed services.

---

## Features

### Core IDP & Document Processing
- ✅ **End-to-end IDP pipeline:**
  - OCR + text extraction from PDFs and images (Tesseract + pdfplumber).
  - Document classification (invoices, receipts, statements).
  - Field extraction into structured tables with confidence scores.
  - Real-time document upload with drag-and-drop support.

### AI-Powered Analytics
- ✅ **RAG-enabled AI agent:**
  - DocSage's agent combines SQL analytics with document retrieval.
  - Answers questions in natural language and cites source docs.
  - Intelligent tool-using agent that chooses between SQL, metrics, and RAG.
- ✅ **Time-series analytics:**
  - Monthly spending trends with interactive charts.
  - Daily spending visualization (last 30 days).
  - Vendor trends over time.
  - Spending forecast using linear regression (3-month prediction).
- ✅ **Smart expense categorization:**
  - LLM-based automatic categorization into 12+ categories.
  - Categories: Office Supplies, Software, Travel, Meals, Services, etc.

### Document Intelligence
- ✅ **Visual document overlay:**
  - Highlight extracted fields on document images.
  - Color-coded fields with confidence scores.
  - Annotated document viewer.
- ✅ **Interactive document correction:**
  - Edit extracted data directly in the UI.
  - Track corrections with confidence scores.
  - Real-time updates after corrections.
- ✅ **Document comparison:**
  - Side-by-side comparison of documents.
  - Similar document finder.
  - Price change detection for recurring vendors.
  - Price trend charts.

### Anomaly Detection & Quality
- ✅ **Automated anomaly detection:**
  - Duplicate transaction detection.
  - Unusual amount flags (>2 standard deviations).
  - Missing field detection.
  - Date anomaly identification.
  - Severity levels (High, Medium, Low).

### Business Intelligence
- ✅ **Natural language insights generator:**
  - AI-generated reports using Ollama LLM.
  - Spending pattern analysis.
  - Cost optimization recommendations.
  - Markdown format with downloadable reports.
- ✅ **Receipt-to-invoice matching:**
  - Automatic matching with fuzzy matching.
  - Vendor name similarity scoring.
  - Amount and date tolerance matching.
  - Confidence scores for matches.

### Export & Reporting
- ✅ **Export functionality:**
  - Excel export with multiple sheets (Transactions, Vendors, Categories, Anomalies, Documents).
  - Summary reports in Markdown format.
  - Downloadable files with timestamps.

> 📖 **See [FEATURES.md](FEATURES.md) for detailed documentation of all features.**

---

## Prerequisites

1. **Python 3.9+**
2. **PostgreSQL** (via Docker Compose) - **Primary database**
   - SQLite is available as an optional alternative (set `USE_SQLITE=True` in `.env`)
3. **Docker** (required for PostgreSQL via Docker Compose)
   - Install from: https://www.docker.com/get-started
4. **Ollama** installed and running locally
   - Install from: https://ollama.com/
   - Pull a model: `ollama pull llama3` (or `mistral`, `codellama`, etc.)
5. **Tesseract OCR** (for image OCR)
   - macOS: `brew install tesseract`
   - Linux: `sudo apt-get install tesseract-ocr`
   - Windows: Download from [GitHub](https://github.com/UB-Mannheim/tesseract/wiki)

---

## Installation

1. **Clone the repository:**
   ```bash
   git clone <repository-url>
   cd docsage
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
   # PostgreSQL (default database)
   POSTGRES_USER=postgres
   POSTGRES_PASSWORD=postgres
   POSTGRES_DB=docsage
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   USE_SQLITE=False  # Set to True to use SQLite instead (not recommended for production)
   
   # Ollama LLM
   OLLAMA_BASE_URL=http://localhost:11434
   OLLAMA_MODEL=llama3
   ```

5. **Start PostgreSQL (via Docker Compose):**
   ```bash
   docker-compose up -d postgres
   ```
   
   **Note:** PostgreSQL is the default and recommended database. To use SQLite instead (not recommended for production), set `USE_SQLITE=True` in your `.env` file and skip this step.

6. **Create the database** (if it doesn't exist):
   ```bash
   docker-compose exec postgres psql -U postgres -c "CREATE DATABASE docsage;"
   ```
   
   Or if you prefer to create it manually, connect to PostgreSQL and run:
   ```sql
   CREATE DATABASE docsage;
   ```

7. **Verify Ollama is running:**
   ```bash
   curl http://localhost:11434/api/tags
   ```

---

## Usage

### 1. Initialize Database

**Important:** Make sure Docker is running and PostgreSQL is started before running these commands.

**First, run the database migration** (if upgrading from an older version):

```bash
# Activate virtual environment first
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Run migration
python scripts/migrate_database.py
```

Then create tables and optionally seed with sample data:

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
    idp_pipeline.py          # OCR + extraction pipeline
    rag.py                   # Embedding + FAISS vector search helpers
    sql_tools.py             # Safe SQL wrappers used by the agent
    insights.py              # Metrics / KPI computation functions
    anomaly_detection.py     # Anomaly detection and alerting
    categorization.py          # LLM-based expense categorization
    document_comparison.py   # Document comparison and price tracking
    document_visualization.py # Visual document overlay with annotations
    export_service.py        # Excel and Markdown export functionality
    insights_generator.py    # AI-generated natural language insights
    receipt_matching.py      # Receipt-to-invoice matching

  agents/
    insight_agent.py# DocSageAgent class - Core AI agent orchestration logic
    tools.py        # Tool definitions exposed to the LLM

  vectorstore/
    faiss_store.py  # FAISS index management

data/
  raw_docs/         # Input PDFs
  processed/        # Extracted JSON/CSV
  embeddings/       # FAISS indexes, metadata

frontend/
  streamlit_app.py  # Comprehensive UI with 8 pages: Analytics, Chat, Documents, Anomalies, Comparison, Insights, Receipt Matching, Export

scripts/
  ingest_docs.py                  # CLI: load PDFs into the system
  build_embeddings.py             # Build FAISS vector index
  seed_db.py                      # Initialize database and seed sample data
  migrate_database.py             # Database migration script (adds new tables/columns)
  download_huggingface_dataset.py # Download invoice/receipt datasets
  add_documents_from_folder.py    # Batch document ingestion
  diagnose_and_fix_transactions.py # Diagnostic and repair utilities

notebooks/
  exploratory_idp.ipynb
  analytics_demo.ipynb
```

---

## Configuration

Key configuration options in `app/config.py`:

- **Database (PostgreSQL is default):**
  - `POSTGRES_USER`, `POSTGRES_PASSWORD`, `POSTGRES_DB`, `POSTGRES_HOST`, `POSTGRES_PORT`: PostgreSQL connection settings
  - `USE_SQLITE`: Set to `True` to use SQLite instead (default: `False` - PostgreSQL is recommended)
- **LLM:**
- `OLLAMA_MODEL`: LLM model to use (default: `llama3`)
  - `OLLAMA_BASE_URL`: Ollama API endpoint (default: `http://localhost:11434`)
- **Vector Store:**
- `EMBEDDING_MODEL`: Embedding model (default: `all-MiniLM-L6-v2`)
- `FAISS_INDEX_PATH`: Path to FAISS index file
- **API:**
  - `API_HOST`: API host (default: `0.0.0.0`)
  - `API_PORT`: API port (default: `8000`)

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

- Place PDF/image files in `data/raw_docs/`
- Run `python scripts/ingest_docs.py`
- Supported formats: PDF, PNG, JPG, JPEG

### Database Migration Issues

- If you see errors about missing columns or tables, run: `python3 scripts/migrate_database.py`
- This adds new tables (`document_corrections`) and columns (`confidence_score`, `is_corrected`)

---

## Development

### Adding New Document Types

1. Update `classify_document()` in `app/services/idp_pipeline.py`
2. Add extraction function (e.g., `extract_form_fields()`)
3. Update `parse_document()` to handle the new type

### Adding New Metrics

1. Add function to `app/services/insights.py`
2. Update `create_metrics_tool()` in `app/agents/tools.py`

---

## Deployment

DocSage can be deployed for **free** using Railway or Render with free LLM APIs (Groq or Hugging Face).

### Quick Deploy to Railway (Free)

1. **Get a free Groq API key**: [console.groq.com](https://console.groq.com)
2. **Deploy to Railway**: Connect your GitHub repo at [railway.app](https://railway.app)
3. **Set environment variables**:
   - `LLM_PROVIDER=groq`
   - `GROQ_API_KEY=your_key`
   - Database credentials (Railway provides these automatically)

See **[DEPLOYMENT.md](DEPLOYMENT.md)** for detailed deployment instructions including:
- Railway deployment (recommended)
- Render deployment
- Docker Compose production setup
- Free LLM API setup (Groq, Hugging Face)
- Environment variable configuration

## Future Enhancements

- [ ] Advanced text chunking strategies
- [ ] Multi-turn conversation support
- [ ] PDF report generation (using reportlab)
- [ ] Real-time document processing webhooks
- [ ] AWS deployment guide
- [ ] Email integration for automatic document processing
- [ ] Multi-language support
- [ ] Advanced ML models for better extraction accuracy
- [ ] Budget tracking and alerts
- [ ] Approval workflows

---

## What I learned

- **How to design tools and guardrails** so an LLM can safely query a SQL DB
- **How to combine RAG + analytics** (FAISS + metrics functions + SQL) for grounded insights
- **How to mirror a managed-cloud architecture** with local components first

## Next steps

- Add GitHub Actions to run linting on each push
- Swap local components for AWS services (Textract, Bedrock, RDS) in a branch

---

## License

MIT License

---

## Contributing

Contributions welcome! Please open an issue or submit a pull request.
