"""
Example usage of the Paper Outline TensorLake application.

This script demonstrates how to:
1. Submit a paper processing request
2. Monitor the request status
3. Retrieve and display results
4. Query the database for processed papers
"""

import time
import requests
import psycopg2
from psycopg2.extras import RealDictCursor

# Configuration
TENSORLAKE_API_KEY = "your_tensorlake_api_key"  # Get from TensorLake dashboard
APPLICATION_NAME = "process_paper"
PDF_URL = "https://arxiv.org/pdf/1706.03762.pdf"  # "Attention Is All You Need" paper


def submit_paper_processing(pdf_url: str) -> str:
    """
    Submit a paper processing request to TensorLake.

    Args:
        pdf_url: URL to the PDF file

    Returns:
        Request ID for tracking
    """
    response = requests.post(
        f"https://api.tensorlake.ai/applications/{APPLICATION_NAME}",
        json={"pdf_url": pdf_url},
        headers={"Authorization": f"Bearer {TENSORLAKE_API_KEY}"}
    )

    response.raise_for_status()
    request_id = response.json()["request_id"]

    print(f"Submitted paper processing request: {request_id}")
    return request_id


def check_request_status(request_id: str) -> dict:
    """
    Check the status of a processing request.

    Args:
        request_id: The request ID to check

    Returns:
        Request status information
    """
    response = requests.get(
        f"https://api.tensorlake.ai/requests/{request_id}",
        headers={"Authorization": f"Bearer {TENSORLAKE_API_KEY}"}
    )

    response.raise_for_status()
    return response.json()


def wait_for_completion(request_id: str, max_wait: int = 1800) -> dict:
    """
    Wait for a request to complete and return the result.

    Args:
        request_id: The request ID to monitor
        max_wait: Maximum time to wait in seconds (default 30 minutes)

    Returns:
        Final result from the request
    """
    start_time = time.time()

    while time.time() - start_time < max_wait:
        status_info = check_request_status(request_id)
        status = status_info["status"]

        print(f"Status: {status}")

        if status == "completed":
            print("\nProcessing completed!")
            return status_info["output"]

        if status == "failed":
            error = status_info.get("error", "Unknown error")
            raise Exception(f"Processing failed: {error}")

        # Wait before checking again
        time.sleep(10)

    raise TimeoutError(f"Request did not complete within {max_wait} seconds")


def query_paper_from_db(paper_id: int, conn_string: str):
    """
    Query and display paper information from PostgreSQL.

    Args:
        paper_id: The paper ID to query
        conn_string: PostgreSQL connection string
    """
    conn = psycopg2.connect(conn_string)
    cur = conn.cursor(cursor_factory=RealDictCursor)

    # Get paper info
    cur.execute("""
        SELECT id, title, authors, abstract, keywords, pdf_url, created_at
        FROM papers
        WHERE id = %s
    """, (paper_id,))

    paper = cur.fetchone()

    if not paper:
        print(f"Paper {paper_id} not found")
        return

    print("\n" + "=" * 80)
    print("PAPER INFORMATION")
    print("=" * 80)
    print(f"ID: {paper['id']}")
    print(f"Title: {paper['title']}")
    print(f"Authors: {', '.join(paper['authors'])}")
    print(f"Keywords: {', '.join(paper['keywords'])}")
    print(f"\nAbstract:\n{paper['abstract']}")
    print(f"\nPDF URL: {paper['pdf_url']}")
    print(f"Created: {paper['created_at']}")

    # Get sections
    cur.execute("""
        SELECT section_title, summary, key_points,
               methodologies, results, citations
        FROM paper_sections
        WHERE paper_id = %s
        ORDER BY id
    """, (paper_id,))

    sections = cur.fetchall()

    print("\n" + "=" * 80)
    print("SECTIONS")
    print("=" * 80)

    for section in sections:
        print(f"\n### {section['section_title']}")
        print(f"\nSummary:\n{section['summary']}")

        if section['key_points']:
            print("\nKey Points:")
            for point in section['key_points']:
                print(f"  - {point}")

        if section['methodologies']:
            print("\nMethodologies:")
            for method in section['methodologies']:
                print(f"  - {method.get('name', 'N/A')}: {method.get('description', '')}")

        if section['results']:
            print("\nResults:")
            for result in section['results']:
                print(f"  - {result.get('finding', 'N/A')}")
                print(f"    Significance: {result.get('significance', 'N/A')}")

        if section['citations']:
            print(f"\nCitations: {len(section['citations'])} references")

        print("\n" + "-" * 80)

    cur.close()
    conn.close()


def main():
    """Main execution flow."""
    print("Paper Outline Application - Example Usage")
    print("=" * 80)

    # Step 1: Submit processing request
    print(f"\n1. Submitting paper for processing: {PDF_URL}")
    request_id = submit_paper_processing(PDF_URL)

    # Step 2: Wait for completion
    print("\n2. Waiting for processing to complete...")
    result = wait_for_completion(request_id)

    # Step 3: Display results
    print("\n3. Processing Results:")
    print("-" * 80)
    print(f"Paper ID: {result['paper_id']}")
    print(f"Title: {result['title']}")
    print(f"Status: {result['status']}")
    print(f"Sections Written: {result['sections_written']}")
    print(f"Total Authors: {result['total_authors']}")
    print(f"Total Keywords: {result['total_keywords']}")

    # Step 4: Query database (optional)
    # Uncomment and provide your connection string to query the database
    # POSTGRES_CONNECTION_STRING = "postgresql://user:password@host:port/database"
    # query_paper_from_db(result['paper_id'], POSTGRES_CONNECTION_STRING)


if __name__ == "__main__":
    main()
