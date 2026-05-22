"use client";

import { FormEvent, useMemo, useState, useRef, useEffect } from "react";
import { askBI } from "@/lib/api";
import type { ChatResponse, SupportingCase } from "@/lib/types";

type Message = {
  id: string;
  sender: "user" | "assistant";
  text: string;
  response?: ChatResponse;
};

const EXAMPLES = [
  "Should I bootstrap longer or raise a seed round now?",
  "Should I hire a senior operator or automate the workflow first?",
  "We have cash pressure. Should we spend for growth or conserve?",
  "Should we acquire a small competitor or grow organically?"
];

export function ChatApp() {
  const [query, setQuery] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [activeMessageId, setActiveMessageId] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"engine" | "workflow">("engine");
  const [isLoading, setIsLoading] = useState(false);
  const [selectedModel, setSelectedModel] = useState<"bi_35_flash" | "bi_55_pro" | "elon_musk">("bi_55_pro");

  const messageListRef = useRef<HTMLDivElement>(null);
  const shellRef = useRef<HTMLDivElement>(null);

  // Mouse move tracker to set CSS custom properties for Gemini motion glow
  useEffect(() => {
    const shell = shellRef.current;
    if (!shell) return;

    const handleMouseMove = (e: MouseEvent) => {
      const rect = shell.getBoundingClientRect();
      const x = e.clientX - rect.left;
      const y = e.clientY - rect.top;
      shell.style.setProperty("--mouse-x", `${x}px`);
      shell.style.setProperty("--mouse-y", `${y}px`);
    };

    shell.addEventListener("mousemove", handleMouseMove);
    return () => {
      shell.removeEventListener("mousemove", handleMouseMove);
    };
  }, []);

  // Auto-scroll to bottom of message list on new message or when loading
  useEffect(() => {
    if (messageListRef.current) {
      messageListRef.current.scrollTop = messageListRef.current.scrollHeight;
    }
  }, [messages, isLoading]);

  // Find the currently active assistant response
  const activeResponse = useMemo(() => {
    if (!activeMessageId) return null;
    const msg = messages.find((m) => m.id === activeMessageId);
    return msg?.response ?? null;
  }, [messages, activeMessageId]);

  const traitRows = useMemo(() => {
    if (!activeResponse) {
      return [];
    }
    return Object.entries(activeResponse.answer.trait_scores)
      .sort(([, left], [, right]) => right - left)
      .slice(0, 8);
  }, [activeResponse]);

  async function handleSendMessage(textToSend: string) {
    if (isLoading) return;
    
    const userMsgId = `user-${Date.now()}`;
    const assistantMsgId = `assistant-${Date.now()}`;

    // Add user message to history
    setMessages((prev) => [
      ...prev,
      { id: userMsgId, sender: "user", text: textToSend }
    ]);
    
    setIsLoading(true);

    try {
      const res = await askBI(textToSend, selectedModel);
      // Add assistant response to history
      setMessages((prev) => [
        ...prev,
        {
          id: assistantMsgId,
          sender: "assistant",
          text: selectedModel === "elon_musk"
            ? `[Elon Simulator] First principles analysis: ${res.answer.recommendation.substring(0, 200)}...`
            : `I have analyzed the decision pattern. ${res.answer.recommendation.substring(0, 200)}...`,
          response: res
        }
      ]);
      setActiveMessageId(assistantMsgId);
    } catch (caught) {
      const errMsg = caught instanceof Error ? caught.message : "Unable to reach BI API.";
      setMessages((prev) => [
        ...prev,
        {
          id: assistantMsgId,
          sender: "assistant",
          text: `Unable to reach the BI Engine. Error: ${errMsg}`
        }
      ]);
    } finally {
      setIsLoading(false);
    }
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed || isLoading) {
      return;
    }
    setQuery("");
    handleSendMessage(trimmed);
  }

  return (
    <main ref={shellRef} className="app-shell">
      <div className="cursor-glow-overlay" />
      <section className="intro">
        <div>
          <p className="product-label">BI</p>
          <h1>Billionaire Intelligence</h1>
          <p className="intro-copy">
            A conversational decision-pattern engine for capital allocation, leverage, risk, hiring,
            execution, compounding, and market judgment.
          </p>
        </div>
        <div className="status-panel">
          <span className="status-dot" />
          Evidence-first mode
        </div>
      </section>

      <section className="chat-layout">
        {/* Left Column: Chat Console */}
        <div className="chat-console">
          <div className="chat-console-header">
            <h2>Executive Console</h2>
            <span>Connected</span>
          </div>

          <div className="model-selector-bar" role="tablist" aria-label="Billionaire Intelligence Models">
            <button
              type="button"
              role="tab"
              aria-selected={selectedModel === "bi_35_flash"}
              className={`model-selector-btn ${selectedModel === "bi_35_flash" ? "active" : ""}`}
              onClick={() => setSelectedModel("bi_35_flash")}
              id="model-35-flash"
            >
              <span className="model-name">BI-3.5 Flash</span>
              <span className="model-desc">Fast Tempo</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={selectedModel === "bi_55_pro"}
              className={`model-selector-btn ${selectedModel === "bi_55_pro" ? "active" : ""}`}
              onClick={() => setSelectedModel("bi_55_pro")}
              id="model-55-pro"
            >
              <span className="model-name">BI-5.5 Pro</span>
              <span className="model-desc">Deep Compounding</span>
            </button>
            <button
              type="button"
              role="tab"
              aria-selected={selectedModel === "elon_musk"}
              className={`model-selector-btn elon-model-btn ${selectedModel === "elon_musk" ? "active" : ""}`}
              onClick={() => setSelectedModel("elon_musk")}
              id="model-elon-musk"
            >
              <span className="model-name">Elon Simulator</span>
              <span className="model-desc">First Principles</span>
            </button>
          </div>

          <div className="message-list" ref={messageListRef}>
            {messages.length === 0 ? (
              <section className="empty-state" style={{ border: 0, background: "transparent", boxShadow: "none", padding: "24px 0 0" }}>
                <h2>Conversational Assistant Idle</h2>
                <p style={{ marginBottom: "24px" }}>
                  Ask a concrete decision question. BI will retrieve sourced cases, rank trait signals,
                  and synthesize an agentic workflow in the dashboard on the right.
                </p>
                <div className="examples" style={{ gridTemplateColumns: "1fr", gap: "10px" }} aria-label="Example prompts">
                  {EXAMPLES.map((example) => (
                    <button
                      type="button"
                      key={example}
                      onClick={() => handleSendMessage(example)}
                      className="example-button"
                      style={{ minHeight: "auto", padding: "12px 16px" }}
                    >
                      {example}
                    </button>
                  ))}
                </div>
              </section>
            ) : (
              messages.map((msg) => {
                const isUser = msg.sender === "user";
                const isAssistant = msg.sender === "assistant";
                const isSelected = msg.id === activeMessageId;
                const hasDetails = !!msg.response;

                return (
                  <div
                    key={msg.id}
                    className={`message-item ${msg.sender} ${
                      isAssistant && hasDetails ? "interactive-select" : ""
                    } ${isSelected ? "active-message" : ""}`}
                    onClick={() => {
                      if (isAssistant && hasDetails) {
                        setActiveMessageId(msg.id);
                      }
                    }}
                  >
                    <span className="message-sender">
                      {isUser ? "You" : "BI Engine"}
                    </span>
                    <div className="message-bubble">
                      <p style={{ margin: 0 }}>{msg.text}</p>
                      {isAssistant && msg.response?.answer.billionaire_time_saver && (
                        <div className="message-time-saver-bubble">
                          💡 Time Saver: {msg.response.answer.billionaire_time_saver.split(".")[0]}.
                        </div>
                      )}
                    </div>
                  </div>
                );
              })
            )}

            {isLoading && (
              <div className="message-item assistant">
                <span className="message-sender">BI Engine</span>
                <div className="message-bubble">
                  <div className="message-loader">
                    <span></span>
                    <span></span>
                    <span></span>
                  </div>
                </div>
              </div>
            )}
          </div>

          <form className="chat-input-panel" onSubmit={handleSubmit}>
            <div className="chat-input-wrapper">
              <input
                type="text"
                className="chat-input-field"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Ask about a trade-off, raise vs bootstrap, acquire vs grow..."
                disabled={isLoading}
              />
              <button
                type="submit"
                className="chat-send-button"
                disabled={isLoading || query.trim().length < 3}
                aria-label="Send message"
              >
                <svg viewBox="0 0 24 24">
                  <path d="M2.01 21L23 12 2.01 3 2 10l15 2-15 2z" />
                </svg>
              </button>
            </div>
          </form>
        </div>

        {/* Right Column: Executive Dashboard */}
        <div className="dashboard-panel">
          {!activeResponse ? (
            <div className="dashboard-empty">
              <svg fill="none" stroke="currentColor" strokeWidth="1.5" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" d="M3.75 6A2.25 2.25 0 016 3.75h2.25A2.25 2.25 0 0110.5 6v2.25a2.25 2.25 0 01-2.25 2.25H6a2.25 2.25 0 01-2.25-2.25V6zM3.75 15.75A2.25 2.25 0 016 13.5h2.25a2.25 2.25 0 012.25 2.25V18a2.25 2.25 0 01-2.25 2.25H6A2.25 2.25 0 013.75 18v-2.25zM13.5 6a2.25 2.25 0 012.25-2.25H18A2.25 2.25 0 0120.25 6v2.25A2.25 2.25 0 0118 10.5h-2.25a2.25 2.25 0 01-2.25-2.25V6zM13.5 15.75a2.25 2.25 0 012.25-2.25H18a2.25 2.25 0 012.25 2.25V18A2.25 2.25 0 0118 20.25h-2.25A2.25 2.25 0 0113.5 18v-2.25z" />
              </svg>
              <h3>Executive Dashboard</h3>
              <p>
                Submit a query in the chat console. The synthesized decision pattern, agentic workflow, and supporting cases will display here.
              </p>
            </div>
          ) : (
            <>
              <nav className="tabs" aria-label="Result tabs" style={{ marginBottom: "16px" }}>
                <button
                  type="button"
                  className={`tab-button ${activeTab === "engine" ? "active" : ""}`}
                  onClick={() => setActiveTab("engine")}
                  id="tab-decision-engine"
                >
                  Decision Engine
                </button>
                <button
                  type="button"
                  className={`tab-button ${activeTab === "workflow" ? "active" : ""}`}
                  onClick={() => setActiveTab("workflow")}
                  id="tab-agentic-workflow"
                >
                  Ask for Solution
                </button>
              </nav>

              <section className="answer-grid" style={{ gridTemplateColumns: "1fr", gap: "24px" }}>
                {activeTab === "engine" ? (
                  <article className="answer-main">
                    <AnswerSection title="Recommendation" body={activeResponse.answer.recommendation} />
                    <ListSection title="Reasoning" items={activeResponse.answer.reasoning} />
                    <ListSection title="Trade-offs" items={activeResponse.answer.tradeoffs} />
                    <ListSection title="Risks" items={activeResponse.answer.risks} />
                    <AnswerSection
                      title="Weak-thinker alternative"
                      body={activeResponse.answer.weak_thinker_alternative}
                    />
                    <AnswerSection title="Next step" body={activeResponse.answer.next_step} />
                    {activeResponse.answer.guardrail_note ? (
                      <p className="guardrail">{activeResponse.answer.guardrail_note}</p>
                    ) : null}
                  </article>
                ) : (
                  <article className="workflow-panel">
                    {activeResponse.answer.billionaire_time_saver ? (
                      <section className="time-saver-card" id="billionaire-time-saver">
                        <h2 className="time-saver-title">Billionaire Time Saver</h2>
                        <p>{activeResponse.answer.billionaire_time_saver}</p>
                      </section>
                    ) : null}

                    <section className="answer-section">
                      <h2>Agentic Solution Workflow</h2>
                      <div className="workflow-steps">
                        {activeResponse.answer.agentic_workflow.map((step, idx) => (
                          <div className="workflow-step" key={idx}>
                            <div className="workflow-step-num">{idx + 1}</div>
                            <div className="workflow-step-content">
                              <h3>{step.phase}</h3>
                              <span className="workflow-agent">{step.agent}</span>
                              <p>{step.action}</p>
                            </div>
                          </div>
                        ))}
                      </div>
                    </section>
                  </article>
                )}

                <aside className="answer-side" style={{ display: "grid", gridTemplateColumns: "1fr 1fr" }}>
                  <div className="intent-box" style={{ gridColumn: "1 / -1" }}>
                    <span>Classified domain</span>
                    <strong>{String(activeResponse.intent.domain ?? "general_strategy")}</strong>
                  </div>
                  <div className="trait-box" style={{ gridColumn: "1 / -1" }}>
                    <h2>Trait signal</h2>
                    {traitRows.length > 0 ? (
                      traitRows.map(([trait, value]) => (
                        <div className="trait-row" key={trait}>
                          <span>{formatTrait(trait)}</span>
                          <meter min={1} max={5} value={value} />
                          <strong>{value.toFixed(1)}</strong>
                        </div>
                      ))
                    ) : (
                      <p className="muted">No trait scores available yet.</p>
                    )}
                  </div>
                </aside>

                <section className="supporting-cases">
                  <div className="section-heading">
                    <h2>Supporting cases</h2>
                    <span>{activeResponse.retrieved_count} retrieved</span>
                  </div>
                  {activeResponse.answer.supporting_cases.map((item) => (
                    <SupportingCaseCard key={item.id} item={item} />
                  ))}
                </section>
              </section>
            </>
          )}
        </div>
      </section>
    </main>
  );
}

function AnswerSection({ title, body }: { title: string; body: string }) {
  return (
    <section className="answer-section">
      <h2>{title}</h2>
      <p>{body}</p>
    </section>
  );
}

function ListSection({ title, items }: { title: string; items: string[] }) {
  return (
    <section className="answer-section">
      <h2>{title}</h2>
      <ul>
        {items.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>
    </section>
  );
}

function SupportingCaseCard({ item }: { item: SupportingCase }) {
  const traits = Object.entries(item.traits)
    .sort(([, left], [, right]) => right - left)
    .slice(0, 4);

  return (
    <article className="case-card">
      <div className="case-header">
        <div>
          <h3>{item.person}</h3>
          <span>{item.domain}</span>
        </div>
        <strong>{Math.round(item.confidence * 100)}% confidence</strong>
      </div>
      <p className="case-decision">{item.decision}</p>
      <p>{item.lesson}</p>
      <div className="trait-tags">
        {traits.map(([trait, score]) => (
          <span key={trait}>
            {formatTrait(trait)} {score}/5
          </span>
        ))}
      </div>
      <footer>
        {item.source_type.replace("_", " ")} · {item.source_reference}
      </footer>
    </article>
  );
}

function formatTrait(value: string) {
  return value
    .split("_")
    .map((part) => part[0].toUpperCase() + part.slice(1))
    .join(" ");
}
