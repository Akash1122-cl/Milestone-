import chromadb
from chromadb.utils import embedding_functions
import os
import sys
from pydantic import BaseModel
from typing import List, Dict, Any

from dotenv import load_dotenv

load_dotenv()

# Root is two levels up from apps/api/core
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))

# Chroma Cloud keys
CHROMA_API_KEY = os.getenv("CHROMA_API_KEY")
CHROMA_TENANT  = os.getenv("CHROMA_TENANT", "default_tenant")
CHROMA_DATABASE = os.getenv("CHROMA_DATABASE", "default_database")

EMBED_MODEL = "BAAI/bge-small-en-v1.5"

# Initialize ChromaDB client once
if not CHROMA_API_KEY or CHROMA_API_KEY == "your-chroma-cloud-api-key":
    raise ValueError("❌ CHROMA_API_KEY environment variable is required and must be valid for Cloud synchronization.")

try:
    chroma_client = chromadb.CloudClient(
        tenant=CHROMA_TENANT,
        database=CHROMA_DATABASE,
        api_key=CHROMA_API_KEY
    )
    bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
        model_name=EMBED_MODEL,
        normalize_embeddings=True,
    )
except Exception as e:
    raise RuntimeError(f"Failed to initialize ChromaDB or Embedder: {e}")


def retrieve_context(query: str, scheme_name: str, top_k: int = 3) -> str:
    """
    Searches ChromaDB for the most relevant facts based on the user's query and scheme.
    Because we split by AMC collections, we'll query all collections and merge/sort the results,
    filtering heavily by the scheme_name metadata if provided to ensure factual accuracy.
    """
    collections = chroma_client.list_collections()
    all_results = []

    # Use a where filter if scheme_name is provided to guarantee facts from exactly that scheme
    where_filter = {"scheme_name": scheme_name} if scheme_name else None

    for col in collections:
        try:
            results = col.query(
                query_texts=[query],
                n_results=top_k,
                where=where_filter,
                include=["documents", "metadatas", "distances"]
            )
            
            # Unpack results safely
            if results["documents"] and len(results["documents"]) > 0:
                docs = results["documents"][0]
                metas = results["metadatas"][0] if results.get("metadatas") else [{}] * len(docs)
                dists = results["distances"][0] if results.get("distances") else [999] * len(docs)
                
                for doc, meta, dist in zip(docs, metas, dists):
                    all_results.append({
                        "text": doc, 
                        "meta": meta, 
                        "distance": dist  # Lower is better (cosine distance)
                    })
        except Exception as e:
            print(f"Error querying collection {col.name}: {e}")

    # Sort all matching results across collections by semantic distance
    all_results.sort(key=lambda x: x["distance"])
    
    # Take the best top_k overall
    top_results = all_results[:top_k]

    # Format into a single context string
    context_str = ""
    for r in top_results:
        context_str += f"- {r['text']} (Source: {r['meta'].get('source_url', 'N/A')})\n"

    # Also return the first source URL and date for the citation metadata if available
    primary_citation = ""
    primary_date = ""
    if top_results:
        primary_citation = top_results[0]["meta"].get("source_url", "")
        primary_date = top_results[0]["meta"].get("last_updated", "")

    return context_str.strip(), primary_citation, primary_date
