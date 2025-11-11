-- Database setup script for Paper Outline application
-- Run this script to create the database and tables

-- Create database (run as superuser)
-- CREATE DATABASE paper_outline;

-- Connect to the database
-- \c paper_outline

-- Create papers table
CREATE TABLE IF NOT EXISTS papers (
    id SERIAL PRIMARY KEY,
    title TEXT NOT NULL,
    authors TEXT[],
    abstract TEXT,
    keywords TEXT[],
    pdf_url TEXT NOT NULL,
    outline JSONB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create paper_sections table
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
);

-- Create indexes for better query performance
CREATE INDEX IF NOT EXISTS idx_paper_sections_paper_id ON paper_sections(paper_id);
CREATE INDEX IF NOT EXISTS idx_papers_created_at ON papers(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_papers_authors ON papers USING GIN(authors);
CREATE INDEX IF NOT EXISTS idx_papers_keywords ON papers USING GIN(keywords);

-- Create a full-text search index on paper titles
CREATE INDEX IF NOT EXISTS idx_papers_title_fts ON papers USING GIN(to_tsvector('english', title));

-- Create a full-text search index on section summaries
CREATE INDEX IF NOT EXISTS idx_sections_summary_fts ON paper_sections USING GIN(to_tsvector('english', summary));

-- Create view for easy querying
CREATE OR REPLACE VIEW paper_overview AS
SELECT
    p.id,
    p.title,
    p.authors,
    array_length(p.authors, 1) as author_count,
    p.keywords,
    array_length(p.keywords, 1) as keyword_count,
    COUNT(ps.id) as section_count,
    p.created_at
FROM papers p
LEFT JOIN paper_sections ps ON p.id = ps.paper_id
GROUP BY p.id, p.title, p.authors, p.keywords, p.created_at;

-- Grant permissions (adjust username as needed)
-- GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO your_username;
-- GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO your_username;

-- Example queries
-- ================

-- Get all papers with section counts
-- SELECT * FROM paper_overview ORDER BY created_at DESC;

-- Search papers by keyword
-- SELECT title, keywords FROM papers WHERE 'transformer' = ANY(keywords);

-- Get all sections for a paper
-- SELECT section_title, summary, key_points
-- FROM paper_sections
-- WHERE paper_id = 1;

-- Full-text search on titles
-- SELECT title, authors
-- FROM papers
-- WHERE to_tsvector('english', title) @@ to_tsquery('english', 'attention & transformer');

-- Get papers with methodologies
-- SELECT p.title, ps.section_title, ps.methodologies
-- FROM papers p
-- JOIN paper_sections ps ON p.id = ps.paper_id
-- WHERE ps.methodologies IS NOT NULL AND jsonb_array_length(ps.methodologies) > 0;

-- Get papers with results
-- SELECT p.title, ps.section_title, ps.results
-- FROM papers p
-- JOIN paper_sections ps ON p.id = ps.paper_id
-- WHERE ps.results IS NOT NULL AND jsonb_array_length(ps.results) > 0;
