/**
 * Centralized API Service for TARA — Transformer-based Audio & Response Assistant
 * Connects React frontend with FastAPI backend
 */

export interface PredictionResponse {
  intent: string;
  raw_intent?: string;
  confidence: number;
  response: string;
  below_threshold?: boolean;
  sentiment?: {
    label: "Positive" | "Neutral" | "Negative";
    score: number;
    confidence: number;
  };
  app?: string;
  threshold?: number;
  session_id?: string;
}

export interface HealthResponse {
  status: string;
  app: string;
  model_ready: boolean;
}

// Base URL of the TARA FastAPI backend.
// Resolution order: NEXT_PUBLIC_API_URL env var (.env.local for local dev,
// Vercel project settings for production) -> local dev fallback below.
// NOTE: NEXT_PUBLIC_* values are inlined at build time, so the dev server
// must be restarted after changing .env.local.
export const API_BASE_URL = (
  process.env.NEXT_PUBLIC_API_URL || "http://127.0.0.1:8000"
).replace(/\/$/, "");

/**
 * Check if the backend AI core is active and model is loaded
 */
export async function checkBackendHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/health`, {
    method: "GET",
    headers: { Accept: "application/json" },
    signal: signal || AbortSignal.timeout(5000),
  });

  if (!response.ok) {
    throw new Error(`Health check failed with status ${response.status}`);
  }

  return response.json();
}

/**
 * Send user query to the Deep Learning intent classifier
 */
export async function predictIntent(
  message: string,
  sessionId?: string,
  signal?: AbortSignal
): Promise<PredictionResponse> {
  const clean = message.trim();
  if (!clean) {
    throw new Error("Message cannot be empty.");
  }

  const body: Record<string, string> = { message: clean };
  if (sessionId) {
    body.session_id = sessionId;
  }

  const response = await fetch(`${API_BASE_URL}/predict`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(body),
    signal: signal || AbortSignal.timeout(12000),
  });

  if (!response.ok) {
    let errorDetail = `Backend returned ${response.status}`;
    try {
      const errJson = await response.json();
      if (typeof errJson.detail === "string") {
        errorDetail = errJson.detail;
      }
    } catch {
      // Ignore JSON parse error on non-JSON response
    }
    throw new Error(errorDetail);
  }

  const data: PredictionResponse = await response.json();
  return data;
}
