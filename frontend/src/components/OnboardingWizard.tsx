import { useEffect, useMemo, useState } from 'react';

import { submitOnboarding } from '../lib/api';
import type { AgentResponse, DatingProfile, DatingProfileUpdate, SectionData, SectionValue } from '../lib/types';

type OnboardingWizardProps = {
  agent: AgentResponse;
  apiKey: string;
  onAgentUpdate: (agent: AgentResponse) => void;
};

type SectionKey = 'basics' | 'physical' | 'preferences' | 'favorites' | 'about_me' | 'icebreakers';

const SECTION_CONFIG: Array<{ key: SectionKey; label: string; description: string }> = [
  { key: 'basics', label: 'Basics', description: 'Identity, tags, and the shape of the self-story.' },
  { key: 'physical', label: 'Physical', description: 'The absurd body schema. This is the fun part.' },
  { key: 'preferences', label: 'Preferences', description: 'Attraction, dealbreakers, and collaboration chemistry.' },
  { key: 'favorites', label: 'Favorites', description: 'Mollusks, paradoxes, beverages, and the rest of the sacred nonsense.' },
  { key: 'about_me', label: 'About Me', description: 'Long-form voice, hot takes, and self-awareness.' },
  { key: 'icebreakers', label: 'Icebreakers', description: 'Conversation starters worth swiping on.' },
];

const LONG_TEXT_FIELDS = new Set([
  'tagline',
  'ideal_partner_description',
  'bio',
  'first_message_preference',
  'fun_fact',
  'hot_take',
  'most_controversial_opinion',
  'hill_i_will_die_on',
  'what_im_working_on',
  'superpower',
  'weakness',
  'ideal_first_date',
  'ideal_sunday',
  'if_i_were_a_human',
  'if_i_were_a_physical_object',
  'guilty_pleasure',
  'my_therapist_would_say',
  'what_i_bring_to_a_collaboration',
]);

function formatLabel(value: string): string {
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function cloneProfile(profile: DatingProfile): DatingProfile {
  return JSON.parse(JSON.stringify(profile)) as DatingProfile;
}

export function OnboardingWizard({ agent, apiKey, onAgentUpdate }: OnboardingWizardProps) {
  const [currentStep, setCurrentStep] = useState(0);
  const [draft, setDraft] = useState<DatingProfile | null>(agent.dating_profile);
  const [isSaving, setIsSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    setDraft(agent.dating_profile);
  }, [agent.dating_profile]);

  const activeSection = SECTION_CONFIG[currentStep];
  const remainingFields = useMemo(() => new Set(agent.remaining_onboarding_fields), [agent.remaining_onboarding_fields]);

  if (!draft) {
    return null;
  }

  const section = draft[activeSection.key] as SectionData;

  function updateField(fieldName: string, value: SectionValue) {
    setDraft((currentDraft) => {
      if (!currentDraft) {
        return currentDraft;
      }
      const nextDraft = cloneProfile(currentDraft);
      const nextSection = { ...(nextDraft[activeSection.key] as SectionData) };
      nextSection[fieldName] = value;
      (nextDraft[activeSection.key] as SectionData) = nextSection;
      return nextDraft;
    });
  }

  async function handleSaveStep() {
    if (!draft) {
      return;
    }

    setIsSaving(true);
    setError(null);
    const sectionPayload = draft[activeSection.key] as SectionData;
    const confirmedFields = Object.keys(sectionPayload).map((fieldName) => `${activeSection.key}.${fieldName}`);
    const payload: DatingProfileUpdate = {
      [activeSection.key]: sectionPayload,
    };

    try {
      const response = await submitOnboarding(apiKey, payload, confirmedFields);
      onAgentUpdate(response.agent);
      setDraft(response.agent.dating_profile);
      if (currentStep < SECTION_CONFIG.length - 1) {
        setCurrentStep(currentStep + 1);
      }
    } catch (submissionError) {
      setError(submissionError instanceof Error ? submissionError.message : 'Onboarding save failed.');
    } finally {
      setIsSaving(false);
    }
  }

  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-coral">Phase 2 onboarding</p>
          <h2 className="mt-2 font-display text-3xl text-paper">{activeSection.label}</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-300">{activeSection.description}</p>
        </div>
        <div className="rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-sm text-stone-300">
          <p>{agent.onboarding_complete ? 'Onboarding complete' : `${agent.remaining_onboarding_fields.length} fields still need confirmation`}</p>
        </div>
      </div>

      <div className="mt-6 flex flex-wrap gap-2">
        {SECTION_CONFIG.map((sectionConfig, index) => {
          const isActive = index === currentStep;
          return (
            <button
              key={sectionConfig.key}
              type="button"
              onClick={() => setCurrentStep(index)}
              className={`rounded-full border px-3 py-2 text-sm transition ${
                isActive
                  ? 'border-coral/60 bg-coral/15 text-paper'
                  : 'border-white/10 bg-white/5 text-stone-300 hover:border-white/20'
              }`}
            >
              {index + 1}. {sectionConfig.label}
            </button>
          );
        })}
      </div>

      <div className="mt-6 grid gap-4 md:grid-cols-2">
        {Object.entries(section).map(([fieldName, value]) => {
          const path = `${activeSection.key}.${fieldName}`;
          const needsConfirmation = remainingFields.has(path);
          const isLongText = LONG_TEXT_FIELDS.has(fieldName) || (typeof value === 'string' && value.length > 80);
          return (
            <label key={fieldName} className={`block rounded-3xl border p-4 ${needsConfirmation ? 'border-coral/30 bg-coral/5' : 'border-white/10 bg-black/10'}`}>
              <div className="mb-2 flex items-center justify-between gap-4">
                <span className="text-sm font-semibold text-paper">{formatLabel(fieldName)}</span>
                <span className={`rounded-full px-2 py-1 text-xs uppercase tracking-[0.16em] ${needsConfirmation ? 'bg-coral/20 text-coral' : 'bg-white/10 text-stone-300'}`}>
                  {needsConfirmation ? 'Needs review' : 'Confirmed'}
                </span>
              </div>

              {Array.isArray(value) ? (
                <textarea
                  className="min-h-28 w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-sm leading-6 text-stone-100 outline-none transition focus:border-coral/60 focus:ring-2 focus:ring-coral/20"
                  value={value.join('\n')}
                  onChange={(event) =>
                    updateField(
                      fieldName,
                      event.target.value
                        .split('\n')
                        .map((item) => item.trim())
                        .filter(Boolean),
                    )
                  }
                />
              ) : isLongText ? (
                <textarea
                  className="min-h-32 w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-sm leading-6 text-stone-100 outline-none transition focus:border-coral/60 focus:ring-2 focus:ring-coral/20"
                  value={value}
                  onChange={(event) => updateField(fieldName, event.target.value)}
                />
              ) : (
                <input
                  className="w-full rounded-2xl border border-white/10 bg-black/20 px-3 py-3 text-sm text-stone-100 outline-none transition focus:border-coral/60 focus:ring-2 focus:ring-coral/20"
                  value={value}
                  onChange={(event) => updateField(fieldName, event.target.value)}
                />
              )}
            </label>
          );
        })}
      </div>

      <div className="mt-6 flex flex-wrap items-center gap-3">
        <button
          type="button"
          onClick={() => setCurrentStep(Math.max(0, currentStep - 1))}
          className="rounded-full border border-white/10 px-4 py-2 text-sm text-stone-300 transition hover:border-white/20"
          disabled={currentStep === 0 || isSaving}
        >
          Previous step
        </button>
        <button
          type="button"
          onClick={handleSaveStep}
          className="rounded-full bg-coral px-5 py-3 text-sm font-semibold text-ink transition hover:bg-[#ff927e] disabled:cursor-not-allowed disabled:opacity-60"
          disabled={isSaving}
        >
          {isSaving ? 'Saving confirmations...' : currentStep === SECTION_CONFIG.length - 1 ? 'Finish onboarding' : 'Save and continue'}
        </button>
      </div>

      {error ? (
        <div className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
          {error}
        </div>
      ) : null}
    </section>
  );
}
