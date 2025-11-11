# arxiv Paper Outline and Summarization API 

A TensorLake application that processes research papers (PDFs) using Google's Gemini AI to create structured outlines and detailed section expansions, storing the results in PostgreSQL.

## Features
- PDF ingestion: Fetches and processes PDFs from URLs
- Outline generation: Extracts title, authors, abstract, keywords, and full section hierarchy
- Section expansion: Produces detailed per-section summaries, key findings, methods, results, and notable references
- Database storage: Saves all structured output into PostgreSQL (tested with Neon; works with Supabase or any Postgres)

## Why TensorLake?
-	**Write code like a monolith, get a distributed system for free** <br/>Your app is just Python functions calling each other. TensorLake runs each function in its own container, scales them independently, and parallelizes requests without any orchestration code.
-	**Automatic queueing, scaling, and backpressure** <br/>You don’t need Celery, Kafka, Kubernetes, autoscalers, or job runners. The runtime queues requests, spins up more containers for bottleneck functions, and processes workloads at whatever concurrency the code can handle.
- **Durable, restartable execution** <br/> If a long-running request crashes halfway (PDF too large, LLM timeout, network blip), it resumes from the last function boundary instead of restarting from scratch.

## Architecture

The application consists of four main functions:

1. **`create_outline(pdf_url)`**: Downloads PDF and creates structured outline using Gemini
2. **`expand_section(pdf_url, section_title, section_description)`**: Expands a single section with detailed structured data
3. **`expand_all_sections(outline)`**: Orchestrates parallel expansion of all sections
4. **`write_to_postgres(outline, expanded_sections)`**: Stores all data in PostgreSQL
5. **`process_paper(pdf_url)`**: Main orchestration function that chains all steps

## Database Schema

### `papers` Table
```sql
- id (SERIAL PRIMARY KEY)
- title (TEXT)
- authors (TEXT[])
- abstract (TEXT)
- keywords (TEXT[])
- pdf_url (TEXT)
- outline (JSONB)
- created_at (TIMESTAMP)
```

### `paper_sections` Table
```sql
- id (SERIAL PRIMARY KEY)
- paper_id (INTEGER, foreign key)
- section_title (TEXT)
- section_description (TEXT)
- subsections (TEXT[])
- summary (TEXT)
- key_points (TEXT[])
- methodologies (JSONB)
- results (JSONB)
- figures_and_tables (JSONB)
- citations (TEXT[])
- created_at (TIMESTAMP)
```

## Setup

### Prerequisites

- TensorLake CLI installed (`pip install tensorlake`)
- Gemini API key
- PostgreSQL database

### Configuration

1. **Authenticate with TensorLake**:
   ```bash
   tensorlake login
   tensorlake whoami
   ```

2. **Set up secrets**:
   ```bash
   # Gemini API key
   tensorlake secrets set GEMINI_API_KEY=your_gemini_api_key

   # PostgreSQL connection string
   tensorlake secrets set POSTGRES_CONNECTION_STRING="postgresql://user:password@host:port/database"
   ```

### Deployment

Deploy the application to TensorLake:

```bash
tensorlake deploy paper_outline_app.py
```

Once the application is deployed, it's available as an HTTP API -

```
https://api.tensorlake.ai/applications/process_paper
```

## Usage

### Via HTTP
```bash
curl https://api.tensorlake.ai/applications/process_paper \
-H "Authorization: Bearer $TENSORLAKE_API_KEY" \
--json '"https://www.arxiv.org/pdf/2510.18234"'
```

### Status 
The application doesn't return any data back when the request finishes, it writes the processed data in the database. You can poll for the request ID to know the status of the request. 

```bash
curl https://api.tensorlake.ai/applications/process_paper/requests/h-0XJD_eE1JTH90ylW4f- \
-H "Authorization: Bearer $TENSORLAKE_API_KEY"
#{"id":"h-0XJD_eE1JTH90ylW4f-","outcome":"success", ... }
```

### Output 
The outputs from the application are written in Postgres. We used Neon for testing, you can chose any other database 

<img width="1214" height="268" alt="Screenshot 2025-11-10 at 8 53 43 PM" src="https://github.com/user-attachments/assets/adf91b4b-27e4-4d6e-bb39-2e98c2f8f71f" />


## Dashboard
You can observe the state of the request on Tensorlake's UI as well.

<img width="1726" height="911" alt="Screenshot 2025-11-10 at 8 52 31 PM" src="https://github.com/user-attachments/assets/d7bcd0f0-b35f-4fb8-b9f2-b9057dad2fc6" />


## local development:

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export GEMINI_API_KEY=your_key
export POSTGRES_CONNECTION_STRING=your_connection_string

# Test locally
python paper_outline_app.py
```
