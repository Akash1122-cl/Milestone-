"""
test_api.py — Comprehensive test suite for Mutual Fund FAQ API
Tests: CORS headers, /health, /api/chat/query (advisory + factual), and /api/metrics endpoints
Run with: pytest tests/test_api.py -v
"""

import pytest
from fastapi.testclient import TestClient
import sys
import os

# Ensure the api root is in path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

# Patch env vars BEFORE importing main so Chroma/Gemini init doesn't fail
os.environ.setdefault("CHROMA_API_KEY", "test-key")
os.environ.setdefault("CHROMA_TENANT", "test-tenant")
os.environ.setdefault("CHROMA_DATABASE", "test-db")
os.environ.setdefault("GEMINI_API_KEY", "test-gemini-key")

from unittest.mock import patch, MagicMock

# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def client():
    """Create a TestClient with mocked external dependencies."""
    mock_chroma_client = MagicMock()
    mock_collection = MagicMock()
    mock_collection.name = "mock_collection"
    mock_collection.query.return_value = {
        "documents": [["Expense ratio of HDFC Mid-Cap Opportunities Fund is 0.77%."]],
        "metadatas": [[{"source_url": "https://groww.in/mutual-funds/hdfc-mid-cap-opportunities-fund", "last_updated": "2026-04-26"}]],
        "distances": [[0.12]],
    }
    mock_chroma_client.get_or_create_collection.return_value = mock_collection

    mock_genai_response = MagicMock()
    mock_genai_response.text = "The expense ratio for HDFC Mid-Cap Opportunities Fund is 0.77%."

    mock_genai_client = MagicMock()
    mock_genai_client.models.generate_content.return_value = mock_genai_response

    with patch("chromadb.CloudClient", return_value=mock_chroma_client), \
         patch("google.genai.Client", return_value=mock_genai_client):
        from main import app
        yield TestClient(app)


# ─── Health Check ─────────────────────────────────────────────────────────────

class TestHealthCheck:
    def test_health_returns_200(self, client):
        resp = client.get("/health")
        assert resp.status_code == 200

    def test_health_returns_status_ok(self, client):
        resp = client.get("/health")
        assert resp.json() == {"status": "healthy"}


# ─── CORS Headers ─────────────────────────────────────────────────────────────

class TestCORSHeaders:
    """
    BUG: The backend allows_credentials=True with allow_origins=["*"].
    This combination is forbidden by the CORS spec — browsers will block it.
    Fix: Replace "*" with explicit Vercel origins.
    """

    def test_cors_origin_vercel_allowed(self, client):
        resp = client.options(
            "/api/chat/query",
            headers={
                "Origin": "https://web-gamma-weld-29.vercel.app",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code in (200, 204), (
            f"CORS preflight rejected for Vercel origin. Status: {resp.status_code}"
        )
        acao = resp.headers.get("access-control-allow-origin", "")
        assert acao != "", "Missing Access-Control-Allow-Origin header — CORS blocked!"

    def test_cors_origin_localhost_allowed(self, client):
        resp = client.options(
            "/api/chat/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type",
            },
        )
        assert resp.status_code in (200, 204)

    def test_cors_headers_present_on_post(self, client):
        resp = client.post(
            "/api/chat/query",
            json={"thread_id": "t1", "query": "What is the expense ratio for HDFC Mid Cap Fund?"},
            headers={"Origin": "https://web-gamma-weld-29.vercel.app"},
        )
        acao = resp.headers.get("access-control-allow-origin", "")
        assert acao != "", (
            "CORS header missing on POST response — frontend will receive a network error!"
        )


# ─── Chat Endpoint ─────────────────────────────────────────────────────────────

class TestChatQuery:
    def test_factual_query_returns_200(self, client):
        resp = client.post(
            "/api/chat/query",
            json={
                "thread_id": "test-thread-1",
                "query": "What is the expense ratio for HDFC Mid Cap Fund?",
            },
        )
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"

    def test_factual_query_response_schema(self, client):
        resp = client.post(
            "/api/chat/query",
            json={
                "thread_id": "test-thread-2",
                "query": "What is the expense ratio for HDFC Mid Cap Fund?",
            },
        )
        body = resp.json()
        assert "answer" in body, "Response missing 'answer' field"
        assert "citation" in body, "Response missing 'citation' field"
        assert "last_updated" in body, "Response missing 'last_updated' field"
        assert "is_advisory" in body, "Response missing 'is_advisory' field"

    def test_factual_query_is_advisory_false(self, client):
        resp = client.post(
            "/api/chat/query",
            json={
                "thread_id": "test-thread-3",
                "query": "What is the exit load for Quant Small Cap Fund?",
            },
        )
        assert resp.json()["is_advisory"] is False

    def test_advisory_query_refusal(self, client):
        resp = client.post(
            "/api/chat/query",
            json={
                "thread_id": "test-thread-4",
                "query": "Should I invest in HDFC or Nippon?",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["is_advisory"] is True
        assert body["answer"] != "", "Refusal message should not be empty"

    def test_advisory_query_no_citation(self, client):
        resp = client.post(
            "/api/chat/query",
            json={
                "thread_id": "test-thread-5",
                "query": "Which is the best mutual fund?",
            },
        )
        body = resp.json()
        assert body["is_advisory"] is True
        assert body["citation"] is None

    def test_missing_thread_id_returns_422(self, client):
        resp = client.post(
            "/api/chat/query",
            json={"query": "What is the NAV?"},
        )
        assert resp.status_code == 422, "Should return 422 for missing required thread_id"

    def test_empty_query_handled(self, client):
        resp = client.post(
            "/api/chat/query",
            json={"thread_id": "test-thread-6", "query": ""},
        )
        # Should either return 200 with some answer or 422 — not crash
        assert resp.status_code in (200, 422)

    def test_answer_is_non_empty_string(self, client):
        resp = client.post(
            "/api/chat/query",
            json={
                "thread_id": "test-thread-7",
                "query": "What is the minimum SIP for Nippon India Large Cap Fund?",
            },
        )
        body = resp.json()
        assert isinstance(body["answer"], str)
        assert len(body["answer"]) > 0, "Answer should not be empty"


# ─── Advisory Guardrail Unit Tests ────────────────────────────────────────────

class TestAdvisoryGuardrail:
    def test_is_advisory_returns_true_for_should_i(self):
        from core.generator import is_advisory_query
        assert is_advisory_query("Should I invest in this fund?") is True

    def test_is_advisory_returns_true_for_best(self):
        from core.generator import is_advisory_query
        assert is_advisory_query("What is the best mutual fund?") is True

    def test_is_advisory_returns_true_for_recommend(self):
        from core.generator import is_advisory_query
        assert is_advisory_query("Can you recommend a good fund?") is True

    def test_is_advisory_returns_false_for_factual(self):
        from core.generator import is_advisory_query
        assert is_advisory_query("What is the expense ratio for HDFC Mid Cap Fund?") is False

    def test_is_advisory_returns_false_for_exit_load(self):
        from core.generator import is_advisory_query
        assert is_advisory_query("What is the exit load for Quant Small Cap Fund?") is False

    def test_is_advisory_case_insensitive(self):
        from core.generator import is_advisory_query
        assert is_advisory_query("SHOULD I INVEST HERE?") is True


# ─── Metrics Endpoints ────────────────────────────────────────────────────────

class TestMetricsEndpoints:
    def test_get_all_funds_returns_200(self, client):
        resp = client.get("/api/metrics/funds")
        assert resp.status_code == 200

    def test_get_summary_returns_200(self, client):
        resp = client.get("/api/metrics/summary")
        assert resp.status_code == 200

    def test_expense_ratio_comparison_returns_200(self, client):
        resp = client.get("/api/metrics/expense-ratio-comparison")
        assert resp.status_code == 200
