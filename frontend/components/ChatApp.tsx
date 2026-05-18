"use client";

import { FormEvent, useMemo, useState } from "react";
import { askBI } from "@/lib/api";
import type { ChatResponse, SupportingCase } from "@/lib/types";

const EXAMPLES = [
  "Should I bootstrap longer or raise a seed round now?",
  "Should I hire a senior operator or automate the workflow first?",
  "We have cash pressure. Should we spend for growth or conserve?",
  "Should we acquire a small competitor or grow organically?"
];

export function ChatApp() {
  const [query, setQuery] = useState("");
  const [response, setResponse] = useState<ChatResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const traitRows = useMemo(() => {
    if (!response) {
      return [];
    }
    return Object.entries(response.answer.trait_scores)
      .sort(([, left], [, right]) => right - left)
      .slice(0, 8);
  }, [response]);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const trimmed = query.trim();
    if (!trimmed) {
      return;
    }
    setIsLoading(true);
    setError(null);
    try {
      setResponse(await askBI(trimmed));
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to reach BI API.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <main className="app-shell">
      <section className="intro">
        <div>
          <p className="product-label">BI</p>
          <h1>Billionaire Intelligence</h1>
          <p className="intro-copy">
            A decision-pattern engine for capital allocation, leverage, risk, hiring,
            execution, compounding, and market judgment.
          </p>
        </div>
        <div className="status-panel">
          <span className="status-dot" />
          Evidence-first mode
        </div>
      </section>

      <section className="workspace">
        <form className="ask-panel" onSubmit={handleSubmit}>
          <label htmlFor="query">Decision question</label>
          <textarea
            id="query"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="What would a top founder or investor do here?"
            rows={5}
          />
          <div className="ask-actions">
            <button type="submit" disabled={isLoading || query.trim().length < 3}>
              {isLoading ? "Thinking..." : "Ask BI"}
            </button>
            <span>Returns recommendation, trade-offs, risks, and evidence.</span>
          </div>
        </form>

        <div className="examples" aria-label="Example prompts">
          {EXAMPLES.map((example) => (
            <button
              type="button"
              key={example}
              onClick={() => setQuery(example)}
              className="example-button"
            >
              {example}
            </button>
          ))}
        </div>

        {error ? <div className="error-state">{error}</div> : null}

        {!response && !error ? (
          <section className="empty-state">
            <h2>Ask a concrete decision question.</h2>
            <p>
              BI retrieves sourced decision cases, ranks trait patterns, and keeps the
              answer grounded in supporting evidence.
            </p>
          </section>
        ) : null}

        {response ? (
          <section className="answer-grid">
            <article className="answer-main">
              <AnswerSection title="Recommendation" body={response.answer.recommendation} />
              <ListSection title="Reasoning" items={response.answer.reasoning} />
              <ListSection title="Trade-offs" items={response.answer.tradeoffs} />
              <ListSection title="Risks" items={response.answer.risks} />
              <AnswerSection
                title="Weak-thinker alternative"
                body={response.answer.weak_thinker_alternative}
              />
              <AnswerSection title="Next step" body={response.answer.next_step} />
              {response.answer.guardrail_note ? (
                <p className="guardrail">{response.answer.guardrail_note}</p>
              ) : null}
            </article>

            <aside className="answer-side">
              <div className="intent-box">
                <span>Classified domain</span>
                <strong>{String(response.intent.domain ?? "general_strategy")}</strong>
              </div>
              <div className="trait-box">
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
                <span>{response.retrieved_count} retrieved</span>
              </div>
              {response.answer.supporting_cases.map((item) => (
                <SupportingCaseCard key={item.id} item={item} />
              ))}
            </section>
          </section>
        ) : null}
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
