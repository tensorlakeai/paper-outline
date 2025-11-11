"""
TensorLake application for processing PDF papers with Gemini.

This application:
1. Downloads a PDF from a URL
2. Creates an outline using Gemini
3. Expands each section of the outline
4. Stores the results in PostgreSQL
"""

import os
import json
import time
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
from enum import Enum
import requests
from google import genai
from google.genai import types
import psycopg2
from psycopg2.extras import Json
from pydantic import BaseModel, Field

from tensorlake.applications import application, function, Image, Awaitable


# Define custom image with required dependencies
app_image = (
    Image()
    .run("pip install google-genai")
    .run("pip install psycopg2-binary")
    .run("pip install pydantic")
    .run("pip install requests")
)


# Pydantic models for structured extraction

class Section(BaseModel):
    """Model for a paper section in the outline."""
    title: str = Field(description="Section title")
    description: str = Field(description="Brief description of section content")
    subsections: Optional[List[str]] = Field(
        default=None,
        description="List of subsection titles if any"
    )


class PaperOutline(BaseModel):
    """Model for the complete paper outline."""
    title: str = Field(description="The full title of the research paper")
    authors: Optional[List[str]] = Field(
        default=None,
        description="List of paper authors"
    )
    abstract: Optional[str] = Field(
        default=None,
        description="Paper abstract or summary"
    )
    sections: List[Section] = Field(description="Main sections of the paper")
    keywords: Optional[List[str]] = Field(
        default=None,
        description="Key terms and concepts in the paper"
    )


class Methodology(BaseModel):
    """Model for a methodology or approach."""
    name: str
    description: str


class Result(BaseModel):
    """Model for a research result or finding."""
    finding: str
    significance: str


class FigureOrTable(BaseModel):
    """Model for visual elements like figures, tables, or equations."""
    type: str = Field(description="Type: figure, table, or equation")
    caption: str
    description: str


class SectionExpansion(BaseModel):
    """Model for expanded section details."""
    section_title: str = Field(description="The title of the section being expanded")
    summary: str = Field(description="Comprehensive summary of the section (2-3 paragraphs)")
    key_points: List[str] = Field(description="Main points and findings in this section")
    methodologies: Optional[List[Methodology]] = Field(
        default=None,
        description="Methods or approaches described (if applicable)"
    )
    results: Optional[List[Result]] = Field(
        default=None,
        description="Key results or findings (if applicable)"
    )
    figures_and_tables: Optional[List[FigureOrTable]] = Field(
        default=None,
        description="Visual elements referenced in this section"
    )
    citations: Optional[List[str]] = Field(
        default=None,
        description="Key references cited in this section"
    )


@function(
    image=app_image,
    secrets=["GEMINI_API_KEY"],
    cpu=2.0,
    memory=4.0,
    timeout=600,
    description="Create structured outline from PDF URL using Gemini"
)
def create_outline(pdf_url: str) -> Dict[str, Any]:
    """
    Downloads PDF from URL and creates a structured outline using Gemini.

    Args:
        pdf_url: URL to the PDF file

    Returns:
        Dictionary containing structured outline with title, authors, abstract, sections, and keywords
    """
    # Initialize Gemini client
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # Download PDF
    response = requests.get(pdf_url, timeout=30)
    response.raise_for_status()
    pdf_content = response.content

    # Upload file to Gemini File API
    temp_path = "/tmp/paper.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_content)

    # Upload to Gemini
    uploaded_file = client.files.upload(file=temp_path)

    # Wait for file to be processed
    while uploaded_file.state.name == "PROCESSING":
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)

    if uploaded_file.state.name == "FAILED":
        raise ValueError("File processing failed")

    # Create outline using Gemini with structured output
    prompt = """
    Analyze this research paper and extract a comprehensive structured outline.

    Extract the following information:
    1. Full paper title
    2. List of all authors
    3. Abstract or summary
    4. All major sections with:
       - Section title
       - Brief description of content
       - Any subsections
    5. Key terms and concepts

    Be thorough and capture all structural elements of the paper.
    Include sections like Abstract, Introduction, Related Work, Methodology,
    Results, Discussion, Conclusion, etc.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[uploaded_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=PaperOutline,
        )
    )

    # Parse structured JSON response using Pydantic
    outline_model = PaperOutline.model_validate_json(response.text)
    outline = outline_model.model_dump()

    # Clean up
    client.files.delete(name=uploaded_file.name)
    os.remove(temp_path)

    # Add PDF URL to the outline for later reference
    outline["pdf_url"] = pdf_url

    return outline


@function(
    image=app_image,
    secrets=["GEMINI_API_KEY"],
    cpu=2.0,
    memory=4.0,
    timeout=600,
    description="Expand a single section with structured data extraction"
)
def expand_section(section_data: Dict[str, str]) -> Dict[str, Any]:
    """
    Expands a single section by analyzing the PDF and extracting structured information.

    Args:
        section_data: Dictionary containing:
            - pdf_url: URL to the PDF file
            - title: Title of the section to expand
            - description: Brief description of the section

    Returns:
        Dictionary with structured section data including summary, key points,
        methodologies, results, figures/tables, and citations
    """
    pdf_url = section_data["pdf_url"]
    section_title = section_data["title"]
    section_description = section_data.get("description", "")

    # Initialize Gemini client
    client = genai.Client(api_key=os.environ["GEMINI_API_KEY"])

    # Download PDF
    response = requests.get(pdf_url, timeout=30)
    response.raise_for_status()
    pdf_content = response.content

    # Upload file to Gemini File API
    temp_path = "/tmp/paper_expand.pdf"
    with open(temp_path, "wb") as f:
        f.write(pdf_content)

    uploaded_file = client.files.upload(file=temp_path)

    # Wait for file to be processed
    while uploaded_file.state.name == "PROCESSING":
        time.sleep(2)
        uploaded_file = client.files.get(name=uploaded_file.name)

    if uploaded_file.state.name == "FAILED":
        raise ValueError("File processing failed")

    # Expand section using Gemini with structured output
    prompt = f"""
    Analyze this research paper and extract detailed structured information about the following section:

    Section: {section_title}
    Description: {section_description}

    Extract and provide:
    1. A comprehensive summary (2-4 paragraphs) of the section content
    2. Key points and main findings
    3. Methodologies or approaches described (if applicable)
    4. Results or findings with their significance (if applicable)
    5. Figures, tables, or equations referenced with descriptions
    6. Key citations mentioned in this section

    Focus on this specific section and extract all relevant structured information.
    Be thorough and capture important details, data, and references.
    """

    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[uploaded_file, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=SectionExpansion,
        )
    )

    # Parse structured JSON response using Pydantic
    expansion_model = SectionExpansion.model_validate_json(response.text)
    expanded_data = expansion_model.model_dump()

    # Clean up
    client.files.delete(name=uploaded_file.name)
    os.remove(temp_path)

    return expanded_data


@function(
    image=app_image,
    secrets=["POSTGRES_CONNECTION_STRING"],
    cpu=1.0,
    memory=2.0,
    timeout=300,
    description="Write structured outline and expanded sections to PostgreSQL"
)
def write_to_postgres(
    outline: Dict[str, Any],
    expanded_sections: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Writes the structured paper outline and expanded sections to PostgreSQL.

    Args:
        outline: The paper outline with title, authors, abstract, sections, and keywords
        expanded_sections: List of expanded sections with structured data

    Returns:
        Dictionary with paper_id and status
    """
    # Connect to PostgreSQL
    conn = psycopg2.connect(os.environ["POSTGRES_CONNECTION_STRING"])
    cur = conn.cursor()

    # Create tables if they don't exist
    cur.execute("""
        CREATE TABLE IF NOT EXISTS papers (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            authors TEXT[],
            abstract TEXT,
            keywords TEXT[],
            pdf_url TEXT NOT NULL,
            outline JSONB NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS paper_sections (
            id SERIAL PRIMARY KEY,
            paper_id INTEGER REFERENCES papers(id) ON DELETE CASCADE,
            section_title TEXT NOT NULL,
            section_description TEXT,
            subsections TEXT[],
            summary TEXT,
            key_points TEXT[],
            methodologies JSONB,
            results JSONB,
            figures_and_tables JSONB,
            citations TEXT[],
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    # Create index on paper_id for faster lookups
    cur.execute("""
        CREATE INDEX IF NOT EXISTS idx_paper_sections_paper_id
        ON paper_sections(paper_id)
    """)

    # Insert paper with structured data
    cur.execute(
        """
        INSERT INTO papers (title, authors, abstract, keywords, pdf_url, outline)
        VALUES (%s, %s, %s, %s, %s, %s)
        RETURNING id
        """,
        (
            outline["title"],
            outline.get("authors", []),
            outline.get("abstract", ""),
            outline.get("keywords", []),
            outline["pdf_url"],
            Json(outline)
        )
    )

    paper_id = cur.fetchone()[0]

    # Create a mapping of section titles to expanded data
    expanded_map = {
        section["section_title"]: section
        for section in expanded_sections
    }

    # Insert sections with structured data
    for section in outline["sections"]:
        section_title = section["title"]
        section_description = section.get("description", "")
        subsections = section.get("subsections", [])

        # Get expanded data for this section
        expanded = expanded_map.get(section_title, {})

        cur.execute(
            """
            INSERT INTO paper_sections
            (paper_id, section_title, section_description, subsections,
             summary, key_points, methodologies, results, figures_and_tables, citations)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (
                paper_id,
                section_title,
                section_description,
                subsections,
                expanded.get("summary", ""),
                expanded.get("key_points", []),
                Json(expanded.get("methodologies", [])),
                Json(expanded.get("results", [])),
                Json(expanded.get("figures_and_tables", [])),
                expanded.get("citations", [])
            )
        )

    conn.commit()
    cur.close()
    conn.close()

    return {
        "paper_id": paper_id,
        "status": "success",
        "title": outline["title"],
        "sections_written": len(outline["sections"]),
        "total_authors": len(outline.get("authors", [])),
        "total_keywords": len(outline.get("keywords", []))
    }


@function(
    image=app_image,
    cpu=1.0,
    memory=1.0,
    timeout=900,
    description="Expand all sections from outline with structured extraction"
)
def expand_all_sections(
    outline: Dict[str, Any]
) -> List[Dict[str, Any]]:
    """
    Expands all sections from the outline in parallel with structured data extraction.

    Args:
        outline: The paper outline with sections

    Returns:
        List of expanded sections with structured data (summary, key points, etc.)
    """
    pdf_url = outline["pdf_url"]

    # Prepare section data list for parallel processing
    sections_data = [
        {
            "pdf_url": pdf_url,
            "title": section["title"],
            "description": section.get("description", "")
        }
        for section in outline["sections"]
    ]

    # Use map for parallel execution across multiple containers
    expanded_sections = expand_section.map(sections_data)

    return expanded_sections


@application()
@function(
    image=app_image,
    cpu=2.0,
    memory=4.0,
    timeout=1800,
    description="Main orchestration function for processing paper"
)
def process_paper(pdf_url: str) -> Dict[str, Any]:
    """
    Main function that orchestrates the entire paper processing pipeline.

    This function chains together:
    1. Creating an outline from the PDF
    2. Expanding each section in the outline
    3. Writing results to PostgreSQL

    Args:
        pdf_url: URL to the PDF file to process

    Returns:
        Final results including paper_id and status
    """
    # Step 1: Create outline (executed in its own container)
    outline = create_outline(pdf_url)

    # Step 2: Expand all sections (each expansion runs in parallel)
    expanded_sections = expand_all_sections(outline)

    # Step 3: Write everything to Postgres
    result = write_to_postgres(outline, expanded_sections)

    return result


if __name__ == "__main__":
    from tensorlake.applications import run_local_application, Request

    pdf_url = "https://arxiv.org/pdf/1706.03762.pdf

    print(f"Processing paper from: {pdf_url}")
    print("This may take several minutes...\n")

    request: Request = run_local_application(process_paper, pdf_url)

    print(request.output())


