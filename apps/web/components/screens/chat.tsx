"use client";
import type { ScreenContracts } from "@/hooks/use-forge-controller";
import {
  ArrowRight,
  ArrowUpRight,
  BookOpen,
  ChartNoAxesCombined,
  Command,
  Database,
  FileText,
  LoaderCircle,
  Lock,
  Plus,
  ShieldCheck,
  Sparkles,
} from "lucide-react";
export default function ChatScreen({
  stats,
  newChat,
  messages,
  busy,
  org,
  ask,
  me,
  setSource,
  chatEnd,
  question,
  setQuestion,
}: ScreenContracts["chat"]) {
  return (
    <div className="chat-layout">
      <div className="chat-title">
        <div>
          <span className="assistant-icon">
            <Sparkles size={18} />
          </span>
          <strong>Knowledge assistant</strong>
          <span className="status ready">
            {stats?.provider_configured ? "AI connected" : "Extractive mode"}
          </span>
        </div>
        <button className="btn" onClick={newChat}>
          <Plus size={15} />
          New conversation
        </button>
      </div>
      <div className="chat-scroll">
        {!messages.length ? (
          <div className="chat-welcome">
            <div className="chat-symbol">
              <Sparkles size={32} />
            </div>
            <span className="eyebrow">CLARITY STARTS WITH A QUESTION</span>
            <h1>What would you like to know?</h1>
            <p>
              Explore your organization’s knowledge.
              <br />
              Every answer stays connected to its sources.
            </p>
            <div className="suggestion-grid">
              {[
                "What is our remote work policy?",
                "How do we deploy a new release?",
                "What are our product priorities?",
                "How should I report a security incident?",
              ].map((q, i) => (
                <button
                  key={q}
                  disabled={busy || org?.role === "viewer"}
                  onClick={() => ask(q)}
                >
                  <span>
                    {
                      [
                        <BookOpen key="b" size={17} />,
                        <Command key="c" size={17} />,
                        <ChartNoAxesCombined key="a" size={17} />,
                        <ShieldCheck key="s" size={17} />,
                      ][i]
                    }
                  </span>
                  {q}
                  <ArrowUpRight size={15} />
                </button>
              ))}
            </div>
            <div className="chat-trust">
              <Lock size={13} />
              Searching only documents you’re authorized to access
            </div>
          </div>
        ) : (
          <div className="message-list">
            {messages.map((m, i) => (
              <article className={"message " + m.role} key={m.id || i}>
                <span className={"message-avatar " + m.role}>
                  {m.role === "user" ? me.user.name[0] : <Sparkles size={17} />}
                </span>
                <div>
                  <strong>
                    {m.role === "user" ? "You" : "Knowledge assistant"}
                  </strong>
                  <div className="message-content">{m.content}</div>
                  {m.citations.length > 0 && (
                    <div className="citations">
                      <span className="citation-label">
                        <BookOpen size={13} /> Sources
                      </span>
                      {m.citations.map((c) => (
                        <button key={c.id} onClick={() => setSource(c)}>
                          <span>{c.number}</span>
                          <FileText size={13} />
                          {c.name}
                          <ArrowUpRight size={12} />
                        </button>
                      ))}
                    </div>
                  )}
                </div>
              </article>
            ))}
            {busy && (
              <div className="thinking">
                <Sparkles size={16} />
                <span>Finding the right context</span>
                <span className="dots">•••</span>
              </div>
            )}
            <div ref={chatEnd} />
          </div>
        )}
      </div>
      <form
        className="chat-composer"
        onSubmit={(e) => {
          e.preventDefault();
          ask();
        }}
      >
        <textarea
          aria-label="Ask your knowledge"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder={
            org?.role === "viewer"
              ? "Viewers can use Search. Conversations require a member role."
              : "Ask anything about your knowledge…"
          }
          disabled={org?.role === "viewer"}
          maxLength={4000}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !e.shiftKey) {
              e.preventDefault();
              ask();
            }
          }}
        />
        <div className="composer-bottom">
          <span>
            <Database size={13} />
            {stats?.ready || 0} indexed documents{" "}
            <span className="composer-dot">·</span>{" "}
            {stats?.provider_configured
              ? "Source-grounded AI"
              : "Extractive retrieval"}
          </span>
          <button
            className="send-btn"
            disabled={busy || !question.trim() || org?.role === "viewer"}
            aria-label="Send question"
          >
            {busy ? (
              <LoaderCircle size={18} className="spin" />
            ) : (
              <ArrowRight size={18} />
            )}
          </button>
        </div>
      </form>
      <p className="chat-disclaimer">
        Answers can be incomplete. Always verify the original sources.
      </p>
    </div>
  );
}
