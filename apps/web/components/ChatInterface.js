"use client";

import { useState, useRef, useEffect } from "react";
import { sendMessage } from "@/lib/api";
import MessageBubble from "./MessageBubble";
import ActionChips from "./ActionChips";
import SessionManager from "./SessionManager";
import FundMetrics from "./FundMetrics";
import { v4 as uuidv4 } from "uuid";

// Session storage for multiple chat sessions
const SESSION_STORAGE_KEY = "chat_sessions";

const getWelcomeMessage = (threadId) => ({
  role: "bot",
  content: `?? Welcome to the Mutual Fund FAQ Assistant! I provide verified, facts-only answers about mutual fund schemes. Ask me about NAV, expense ratios, exit loads, or minimum SIP amounts.\n\nSession ID: ${threadId.substring(0, 8)}...`,
  citation: null,
  last_updated: null,
  is_advisory: false,
});

export default function ChatInterface() {
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState("");
  const [loading, setLoading] = useState(false);
  const [threadId, setThreadId] = useState(() => {
    // Generate or retrieve thread ID from session storage
    if (typeof window !== 'undefined') {
      const sessions = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEY) || "{}");
      const activeSession = Object.keys(sessions).find(id => sessions[id].active);
      if (activeSession) {
        return activeSession;
      }
    }
    return uuidv4();
  });
  const [allSessions, setAllSessions] = useState({});
  const [activeView, setActiveView] = useState("chat"); // "chat" or "metrics"
  const bottomRef = useRef(null);

  // Initialize session on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const sessions = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEY) || "{}");
      
      // If current thread doesn't exist, create it
      if (!sessions[threadId]) {
        sessions[threadId] = {
          messages: [getWelcomeMessage(threadId)],
          active: true,
          createdAt: new Date().toISOString(),
        };
      }
      
      // Set current session messages
      setMessages(sessions[threadId].messages);
      setAllSessions(sessions);
      
      // Save to session storage
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
    }
  }, [threadId]);

  // Save messages to session storage whenever they change
  useEffect(() => {
    if (typeof window !== 'undefined' && messages.length > 0) {
      const sessions = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEY) || "{}");
      if (sessions[threadId]) {
        sessions[threadId].messages = messages;
        sessions[threadId].lastActive = new Date().toISOString();
        sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
      }
    }
  }, [messages, threadId]);

  // Session management functions
  const createNewSession = () => {
    const newThreadId = uuidv4();
    if (typeof window !== 'undefined') {
      const sessions = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEY) || "{}");
      
      // Deactivate all current sessions
      Object.keys(sessions).forEach(id => {
        sessions[id].active = false;
      });
      
      // Create new session
      sessions[newThreadId] = {
        messages: [getWelcomeMessage(newThreadId)],
        active: true,
        createdAt: new Date().toISOString(),
      };
      
      sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
      setAllSessions(sessions);
      setMessages(sessions[newThreadId].messages);
      setThreadId(newThreadId);
    }
  };

  const switchToSession = (sessionId) => {
    if (typeof window !== 'undefined') {
      const sessions = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEY) || "{}");
      
      // Deactivate all sessions
      Object.keys(sessions).forEach(id => {
        sessions[id].active = false;
      });
      
      // Activate selected session
      if (sessions[sessionId]) {
        sessions[sessionId].active = true;
        sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
        setAllSessions(sessions);
        setMessages(sessions[sessionId].messages);
        setThreadId(sessionId);
      }
    }
  };

  const deleteSession = (sessionId) => {
    if (typeof window !== 'undefined') {
      const sessions = JSON.parse(sessionStorage.getItem(SESSION_STORAGE_KEY) || "{}");
      
      // Don't delete if it's the only session
      if (Object.keys(sessions).length <= 1) {
        return;
      }
      
      delete sessions[sessionId];
      
      // If deleting current session, switch to another
      if (sessionId === threadId) {
        const remainingSessions = Object.keys(sessions);
        if (remainingSessions.length > 0) {
          switchToSession(remainingSessions[0]);
        }
      } else {
        sessionStorage.setItem(SESSION_STORAGE_KEY, JSON.stringify(sessions));
        setAllSessions(sessions);
      }
    }
  };

  // Auto-scroll to newest message
  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSend = async (query) => {
    const text = (query || input).trim();
    if (!text || loading) return;

    // Append user message
    setMessages((prev) => [...prev, { role: "user", content: text }]);
    setInput("");
    setLoading(true);

    try {
      const data = await sendMessage(
        text,
        null,
        threadId,
        // onWakingUp: called when Render free-tier cold-start is detected
        () => {
          setMessages((prev) => [
            ...prev,
            {
              role: "bot",
              content: "⏳ The server is waking up from sleep (Render free tier). Please wait up to 60 seconds — your answer is on the way...",
              citation: null,
              last_updated: null,
              is_advisory: false,
              isStatus: true,
            },
          ]);
        }
      );

      // Remove any "waking up" status messages and add the real answer
      setMessages((prev) => [
        ...prev.filter((m) => !m.isStatus),
        {
          role: "bot",
          content: data.answer,
          citation: data.citation,
          last_updated: data.last_updated,
          is_advisory: data.is_advisory,
        },
      ]);
    } catch (err) {
      setMessages((prev) => [
        ...prev.filter((m) => !m.isStatus),
        {
          role: "bot",
          content: `❌ Could not reach the server after multiple attempts. Error: ${err.message}`,
          citation: null,
          last_updated: null,
          is_advisory: false,
        },
      ]);
    } finally {
      setLoading(false);
    }
  };


  const handleKeyDown = (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="chat-wrapper">
      {/* Header */}
      <header className="chat-header">
        <div className="header-brand">
          <span className="brand-icon">??</span>
          <div>
            <h1 className="brand-title">Mutual Fund FAQ Assistant</h1>
            <p className="brand-subtitle">Facts-only · Multi-Session Chat</p>
          </div>
        </div>
        <div className="disclaimer-badge">?? No Investment Advice</div>
      </header>
      
      {/* Session Manager */}
      <SessionManager
        currentSession={threadId}
        allSessions={allSessions}
        onNewSession={createNewSession}
        onSwitchSession={switchToSession}
        onDeleteSession={deleteSession}
      />

      {/* View Toggle */}
      <div className="view-toggle">
        <button
          className={`view-button ${activeView === "chat" ? "active" : ""}`}
          onClick={() => setActiveView("chat")}
        >
          ?? Chat
        </button>
        <button
          className={`view-button ${activeView === "metrics" ? "active" : ""}`}
          onClick={() => setActiveView("metrics")}
        >
          ?? Metrics
        </button>
      </div>

      {/* Message Feed */}
      {activeView === "chat" && (
        <div className="messages-feed">
          {messages.map((msg, i) => (
            <MessageBubble key={i} message={msg} />
          ))}
          {loading && (
            <div className="bot-row">
              <div className="avatar bot-avatar">AI</div>
              <div className="bubble bot-bubble loading-bubble">
                <span className="dot"></span>
                <span className="dot"></span>
                <span className="dot"></span>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      )}

      {/* Metrics Dashboard */}
      {activeView === "metrics" && (
        <FundMetrics />
      )}

      {/* Action Chips */}
      {activeView === "chat" && messages.length <= 1 && (
        <ActionChips onChipClick={handleSend} disabled={loading} />
      )}

      {/* Input Bar */}
      {activeView === "chat" && (
        <div className="input-bar">
          <textarea
            className="input-field"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about NAV, expense ratio, exit loads..."
            rows={1}
            disabled={loading}
          />
          <button
            className={`send-btn ${loading ? "send-btn-disabled" : ""}`}
            onClick={() => handleSend()}
            disabled={loading}
            aria-label="Send message"
          >
            {loading ? "..." : "Send"}
          </button>
        </div>
      )}
    </div>
  );
}
