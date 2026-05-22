export type SupportingCase = {
  id: string;
  person: string;
  domain: string;
  decision: string;
  lesson: string;
  source_type: string;
  source_reference: string;
  confidence: number;
  retrieval_score: number;
  traits: Record<string, number>;
};

export type BIAnswer = {
  recommendation: string;
  reasoning: string[];
  tradeoffs: string[];
  risks: string[];
  weak_thinker_alternative: string;
  next_step: string;
  supporting_cases: SupportingCase[];
  trait_scores: Record<string, number>;
  guardrail_note: string | null;
  agentic_workflow: { phase: string; agent: string; action: string }[];
  billionaire_time_saver: string;
};

export type ChatResponse = {
  answer: BIAnswer;
  intent: Record<string, unknown>;
  retrieved_count: number;
  analytics_event_id: string | null;
};
