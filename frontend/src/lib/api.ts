import type { DatingProfileUpdate, OnboardingResponse, RegistrationResponse } from './types';

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
  const response = await fetch(`${API_BASE_URL}/api/agents/me/onboarding`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${apiKey}`,
    },
    body: JSON.stringify({
      dating_profile: datingProfile,
      confirmed_fields: confirmedFields,
    }),
  });

  if (!response.ok) {
    await readError(response);
  }

  return response.json() as Promise<OnboardingResponse>;
}
