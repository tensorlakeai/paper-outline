# Quick Start Guide

Get up and running with the Paper Outline application in minutes.

## Prerequisites

- Python 3.9+
- PostgreSQL database
- Google Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

## Step 1: Install TensorLake

```bash
pip install tensorlake
```

## Step 2: Authenticate

```bash
tensorlake login
tensorlake whoami  # Verify authentication
```

## Step 3: Set Up Database

```bash
# Connect to PostgreSQL
psql -U your_username -d postgres

# Create database
CREATE DATABASE paper_outline;

# Exit and run setup script
psql -U your_username -d paper_outline -f setup_database.sql
```

## Step 4: Configure Secrets

```bash
# Set Gemini API key
tensorlake secrets set GEMINI_API_KEY=your_gemini_api_key

# Set PostgreSQL connection string
tensorlake secrets set POSTGRES_CONNECTION_STRING="postgresql://user:password@host:port/paper_outline"
```

Verify secrets:
```bash
tensorlake secrets list
```

## Step 5: Deploy Application

```bash
tensorlake deploy paper_outline_app.py
```

Wait for deployment to complete. You'll see a success message with your application URL.

## Step 6: Test the Application

### Option A: Using TensorLake CLI

```bash
tensorlake run process_paper \
  --pdf_url "https://arxiv.org/pdf/1706.03762.pdf"
```

### Option B: Using Python

```python
import requests

response = requests.post(
    "https://api.tensorlake.ai/applications/process_paper",
    json={"pdf_url": "https://arxiv.org/pdf/1706.03762.pdf"},
    headers={"Authorization": f"Bearer {your_api_key}"}
)

print(response.json())
```

### Option C: Local Testing (Before Deployment)

```bash
# Set environment variables
export GEMINI_API_KEY=your_key
export POSTGRES_CONNECTION_STRING=your_connection_string

# Test locally
tensorlake test paper_outline_app.py process_paper \
  --pdf_url "https://arxiv.org/pdf/1706.03762.pdf"
```

## Step 7: Query Results

```sql
-- Connect to database
psql -U your_username -d paper_outline

-- View all papers
SELECT id, title, created_at FROM papers;

-- View sections for a specific paper
SELECT section_title, summary FROM paper_sections WHERE paper_id = 1;

-- Use the convenience view
SELECT * FROM paper_overview;
```

## Example PDF URLs for Testing

- **Attention Is All You Need**: https://arxiv.org/pdf/1706.03762.pdf
- **BERT**: https://arxiv.org/pdf/1810.04805.pdf
- **GPT-2**: https://d4mucfpksywv.cloudfront.net/better-language-models/language_models_are_unsupervised_multitask_learners.pdf

## Monitoring

Check application logs:
```bash
tensorlake logs process_paper
```

View request history:
```bash
tensorlake requests list
```

Get specific request details:
```bash
tensorlake requests get <request_id>
```

## Troubleshooting

### "Secret not found" Error
```bash
# List configured secrets
tensorlake secrets list

# Re-set missing secrets
tensorlake secrets set GEMINI_API_KEY=your_key
```

### Database Connection Error
- Verify connection string format: `postgresql://user:password@host:port/database`
- Check database is running and accessible
- Ensure user has proper permissions

### PDF Download Timeout
- Try a smaller PDF first
- Increase function timeout in `paper_outline_app.py`
- Verify PDF URL is publicly accessible

### Deployment Fails
```bash
# Check for syntax errors
python -m py_compile paper_outline_app.py

# View detailed deployment logs
tensorlake deploy paper_outline_app.py --verbose
```

## Next Steps

- Customize JSON schemas in `paper_outline_app.py` for your needs
- Adjust resource allocation (CPU, memory) based on paper sizes
- Set up automated processing pipelines
- Create custom queries and analytics

## Getting Help

- Documentation: https://docs.tensorlake.ai
- GitHub Issues: [Your repository]
- Email: support@tensorlake.ai

## Cost Estimation

Typical costs per paper (estimates):
- Small paper (10 pages, 5 sections): ~$0.10
- Medium paper (20 pages, 8 sections): ~$0.25
- Large paper (50 pages, 12 sections): ~$0.60

Factors affecting cost:
- PDF size and page count
- Number of sections
- Gemini API usage
- TensorLake compute time
