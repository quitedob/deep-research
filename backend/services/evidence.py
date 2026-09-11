"""Shared citation presentation for streams and persisted reports."""

def citation_evidence(citations):
    """A citation is a source, not a measured confidence score."""
    return [
        {
            "id": citation.get("id"),
            "source_type": "document" if "arxiv.org" in citation.get("source_url", "") else "web",
            "source_title": citation.get("title", ""),
            "source_url": citation.get("source_url", ""),
            "content": citation.get("title", ""),
            "snippet": citation.get("title", ""),
            "relevance_score": None,
            "confidence_score": None,
        }
        for citation in citations
    ]
