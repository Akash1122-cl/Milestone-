/**
 * api.js — API connector for the Mutual Fund FAQ Assistant
 * Sends queries to the FastAPI backend and returns structured responses.
 */

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000";

/**
 * Sends a user query to the FastAPI backend with retry logic.
 * Render free-tier instances sleep after inactivity — the first request
 * may take up to 60 seconds to respond (cold start). We retry up to 2x.
 *
 * @param {string} query - The user's question.
 * @param {string|null} schemeName - Optional fund name filter.
 * @param {string} threadId - Unique conversation thread ID.
 * @param {function} onWakingUp - Optional callback called on 1st timeout to show status.
 * @returns {Promise<{answer: string, citation: string|null, last_updated: string|null, is_advisory: boolean}>}
 */
export async function sendMessage(query, schemeName = null, threadId = "default-thread", onWakingUp = null) {
  const MAX_RETRIES = 2;
  const TIMEOUT_MS = 60000; // 60s — enough for Render cold-start

  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    const controller = new AbortController();
    const timer = setTimeout(() => controller.abort(), TIMEOUT_MS);

    try {
      const response = await fetch(`${API_BASE}/api/chat/query`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          thread_id: threadId,
          query,
          scheme_name: schemeName,
        }),
        signal: controller.signal,
      });

      clearTimeout(timer);

      if (!response.ok) {
        const errText = await response.text().catch(() => response.statusText);
        throw new Error(`API Error ${response.status}: ${errText}`);
      }

      return response.json();
    } catch (err) {
      clearTimeout(timer);

      const isTimeout = err.name === "AbortError" || err.message?.includes("abort");
      const isNetworkError = err.name === "TypeError" || isTimeout;

      if (isNetworkError && attempt < MAX_RETRIES) {
        // Notify UI that the server is waking up (Render cold-start)
        if (attempt === 0 && onWakingUp) {
          onWakingUp();
        }
        // Wait before retrying (exponential backoff)
        await new Promise((r) => setTimeout(r, (attempt + 1) * 3000));
        continue;
      }

      throw err;
    }
  }
}

