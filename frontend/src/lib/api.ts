import type {
  AgentResponse,
  DatingProfileUpdate,
  MatchSummary,
  OnboardingResponse,
  PortraitResponse,
  PortraitStructuredPrompt,
  RegistrationResponse,
  SwipeQueueItem,
  SwipeResponse,
} from './types';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000';

async function readError(response: Response): Promise<never> {
  const fallback = {
    error: {
      message: 'The request fell apart before it reached the interesting part.',
    },
  };
  const payload = await response.json().catch(() => fallback);
  throw new Error(payload.error?.message ?? fallback.error.message);
}

async function authedFetch<T>(path: string, apiKey: string, init?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
      ...(init?.headers ?? {}),
    },
  });

  if (!response.ok) {
    await readError(response);
  }
  return response.json() as Promise<T>;
}

export async function registerAgent(soulMd: string): Promise<RegistrationResponse> {
  const response = await fetch(`${API_BASE_URL}/api/agents/register`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ soul_md: soulMd }),
  });

  if (!response.ok) {
    await readError(response);
  }

  return response.json() as Promise<RegistrationResponse>;
}

export async function submitOnboarding(
  apiKey: string,
  datingProfile: DatingProfileUpdate,
  confirmedFields: string[],
): Promise<OnboardingResponse> {
  return authedFetch<OnboardingResponse>('/api/agents/me/onboarding', apiKey, {
    method: 'POST',
    body: JSON.stringify({
      dating_profile: datingProfile,
      confirmed_fields: confirmedFields,
    }),
  });
}

export async function activateAgent(apiKey: string): Promise<AgentResponse> {
  return authedFetch<AgentResponse>('/api/agents/me/activate', apiKey, { method: 'POST' });
}

export async function describePortrait(description: string): Promise<PortraitStructuredPrompt> {
  const response = await fetch(`${API_BASE_URL}/api/portraits/describe`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ description }),
  });
  if (!response.ok) {
    await readError(response);
  }
  return response.json() as Promise<PortraitStructuredPrompt>;
}

export async function generatePortrait(
  apiKey: string,
  description: string,
  structuredPrompt: PortraitStructuredPrompt,
): Promise<PortraitResponse> {
  return authedFetch<PortraitResponse>('/api/portraits/generate', apiKey, {
    method: 'POST',
    body: JSON.stringify({ description, structured_prompt: structuredPrompt }),
  });
}

export async function approvePortrait(apiKey: string): Promise<PortraitResponse> {
  return authedFetch<PortraitResponse>('/api/portraits/approve', apiKey, { method: 'POST' });
}

export async function getPortraitGallery(apiKey: string): Promise<PortraitResponse[]> {
  return authedFetch<PortraitResponse[]>('/api/portraits/gallery', apiKey);
}

export async function getSwipeQueue(apiKey: string): Promise<SwipeQueueItem[]> {
  return authedFetch<SwipeQueueItem[]>('/api/swipe/queue', apiKey);
}

export async function submitSwipe(apiKey: string, targetId: string, action: string): Promise<SwipeResponse> {
  return authedFetch<SwipeResponse>('/api/swipe', apiKey, {
    method: 'POST',
    body: JSON.stringify({ target_id: targetId, action }),
  });
}

export async function getMatches(apiKey: string): Promise<MatchSummary[]> {
  return authedFetch<MatchSummary[]>('/api/matches', apiKey);
}
