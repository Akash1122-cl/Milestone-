"""
enhanced_retriever.py - Enhanced retrieval with metrics integration
Combines Chroma Cloud retrieval with structured fund metrics data
"""

import chromadb
from chromadb.utils import embedding_functions
import os
import sys
from pydantic import BaseModel
from typing import List, Dict, Any, Optional, Tuple

from dotenv import load_dotenv
from .metrics_service import fund_metrics_service

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
    raise ValueError("?? CHROMA_API_KEY environment variable is required and must be valid for Cloud synchronization.")

class EnhancedRetriever:
    """Enhanced retriever that combines Chroma Cloud with structured metrics"""
    
    def __init__(self):
        self.chroma_client_initialized = False
        self.bge_ef = None
        self.collections = {}

    def _ensure_initialized(self):
        if self.chroma_client_initialized:
            return
            
        try:
            if not CHROMA_API_KEY or CHROMA_API_KEY == "your-chroma-cloud-api-key":
                raise ValueError("❌ CHROMA_API_KEY environment variable is required and must be valid for Cloud synchronization.")

            self.chroma_client = chromadb.CloudClient(
                tenant=CHROMA_TENANT,
                database=CHROMA_DATABASE,
                api_key=CHROMA_API_KEY
            )
            self.bge_ef = embedding_functions.SentenceTransformerEmbeddingFunction(
                model_name=EMBED_MODEL,
                normalize_embeddings=True,
            )
            self.collections = {
                'nippon_india': self.chroma_client.get_or_create_collection('nippon_india'),
                'general': self.chroma_client.get_or_create_collection('general')
            }
            self.chroma_client_initialized = True
        except Exception as e:
            print(f"Warning: Could not initialize Chroma/collections. Error: {e}")
            self.collections = {}
            self.chroma_client_initialized = False
    
    def retrieve_enhanced_context(self, query: str, scheme_name: Optional[str] = None, top_k: int = 3) -> Tuple[str, Optional[str], Optional[str]]:
        """
        Enhanced retrieval that combines Chroma Cloud results with structured metrics
        """
        self._ensure_initialized()
        # First, try to get structured metrics data
        metrics_context = self._get_metrics_context(query, scheme_name)
        
        # Then get Chroma Cloud context
        chroma_context, citation, updated_date = self._retrieve_chroma_context(query, scheme_name, top_k)
        
        # Combine contexts
        combined_context = self._combine_contexts(metrics_context, chroma_context)
        
        # Determine best citation
        best_citation = self._select_best_citation(citation, scheme_name)
        
        # Determine best updated date
        best_updated = self._select_best_updated_date(updated_date)
        
        return combined_context, best_citation, best_updated
    
    def _get_metrics_context(self, query: str, scheme_name: Optional[str] = None) -> str:
        """Get relevant context from structured metrics data"""
        query_lower = query.lower()
        context_parts = []
        
        # Check if query is asking about specific metrics
        metric_keywords = {
            'expense ratio': 'expense_ratio',
            'exit load': 'exit_load', 
            'minimum sip': 'minimum_sip',
            'sip': 'minimum_sip',
            'lock in': 'lock_in_period',
            'lock-in': 'lock_in_period',
            'riskometer': 'riskometer',
            'risk': 'riskometer',
            'benchmark': 'benchmark'
        }
        
        # Determine which metric is being asked about
        requested_metric = None
        for keyword, metric_field in metric_keywords.items():
            if keyword in query_lower:
                requested_metric = metric_field
                break
        
        # Get fund data
        if scheme_name:
            fund_data = fund_metrics_service.get_fund_by_name(scheme_name)
            if fund_data:
                if requested_metric:
                    # Return specific metric
                    value = fund_data.get(requested_metric)
                    if value and value not in [None, '', 'Not found']:
                        context_parts.append(f"{scheme_name} {requested_metric.replace('_', ' ').title()}: {value}")
                else:
                    # Return all available metrics
                    context_parts.append(f"Fund: {scheme_name}")
                    for metric in ['expense_ratio', 'exit_load', 'minimum_sip', 'lock_in_period', 'riskometer', 'benchmark']:
                        value = fund_data.get(metric)
                        if value and value not in [None, '', 'Not found']:
                            context_parts.append(f"{metric.replace('_', ' ').title()}: {value}")
        else:
            # Search for relevant funds
            matching_funds = fund_metrics_service.search_funds(query)
            for fund in matching_funds[:3]:  # Limit to top 3
                fund_name = fund.get('fund_name', 'Unknown Fund')
                if requested_metric:
                    value = fund.get(requested_metric)
                    if value and value not in [None, '', 'Not found']:
                        context_parts.append(f"{fund_name} {requested_metric.replace('_', ' ').title()}: {value}")
                else:
                    # Add basic fund info
                    expense_ratio = fund.get('expense_ratio')
                    riskometer = fund.get('riskometer')
                    if expense_ratio and expense_ratio not in [None, '', 'Not found']:
                        context_parts.append(f"{fund_name} Expense Ratio: {expense_ratio}")
                    if riskometer and riskometer not in [None, '', 'Not found']:
                        context_parts.append(f"{fund_name} Risk Level: {riskometer}")
        
        return '\n'.join(context_parts)
    
    def _retrieve_chroma_context(self, query: str, scheme_name: Optional[str] = None, top_k: int = 3) -> Tuple[str, Optional[str], Optional[str]]:
        """Retrieve context from Chroma Cloud (original implementation)"""
        all_results = []
        
        # Determine which collections to search
        collections_to_search = list(self.collections.values())
        
        # If scheme name is provided, prioritize relevant collection
        if scheme_name:
            if 'nippon' in scheme_name.lower():
                collections_to_search.insert(0, self.collections['nippon_india'])
            else:
                collections_to_search.insert(0, self.collections['general'])
        
        # Search all collections
        for collection in collections_to_search:
            try:
                # Generate query embedding
                query_embedding = self.bge_ef([query])
                
                # Query collection
                results = collection.query(
                    query_embeddings=query_embedding,
                    n_results=top_k
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
                print(f"Error querying collection {collection.name}: {e}")
        
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
    
    def _combine_contexts(self, metrics_context: str, chroma_context: str) -> str:
        """Combine metrics and Chroma contexts intelligently"""
        contexts = []
        
        if metrics_context.strip():
            contexts.append("=== Fund Metrics ===")
            contexts.append(metrics_context)
        
        if chroma_context.strip():
            contexts.append("=== Additional Information ===")
            contexts.append(chroma_context)
        
        return '\n\n'.join(contexts)
    
    def _select_best_citation(self, chroma_citation: Optional[str], scheme_name: Optional[str] = None) -> Optional[str]:
        """Select the best citation from available sources"""
        # Prefer structured data citation for specific funds
        if scheme_name:
            fund_data = fund_metrics_service.get_fund_by_name(scheme_name)
            if fund_data and fund_data.get('url'):
                return fund_data['url']
        
        # Fall back to Chroma citation
        return chroma_citation
    
    def _select_best_updated_date(self, chroma_date: Optional[str]) -> Optional[str]:
        """Select the best updated date"""
        # For now, return the Chroma date
        # In future, could check metrics file timestamp
        return chroma_date

# Global instance for use across the application
enhanced_retriever = EnhancedRetriever()

def retrieve_context(query: str, scheme_name: Optional[str] = None, top_k: int = 3) -> Tuple[str, Optional[str], Optional[str]]:
    """
    Enhanced context retrieval that combines Chroma Cloud with structured metrics
    """
    return enhanced_retriever.retrieve_enhanced_context(query, scheme_name, top_k)
