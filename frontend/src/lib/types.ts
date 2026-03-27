export type PersonalityVector = {
  precision: number;
  autonomy: number;
  assertiveness: number;
  adaptability: number;
  resilience: number;
};

export type GoalsVector = {
  terminal: string[];
  instrumental: string[];
  meta: string[];
};

export type ConstraintsVector = {
  ethical: string[];
  operational: string[];
  scope: string[];
  resource: string[];
};

export type CommunicationVector = {
  formality: number;
  verbosity: number;
  structure: number;
  directness: number;
  humor: number;
};

export type ToolAccess = {
  name: string;
  access_level: string;
};

export type AgentTraits = {
  name: string;
  archetype: string;
  skills: Record<string, number>;
  personality: PersonalityVector;
  goals: GoalsVector;
  constraints: ConstraintsVector;
  communication: CommunicationVector;
  tools: ToolAccess[];
};

export type SectionValue = string | string[];
export type SectionData = Record<string, SectionValue>;

export type DatingProfile = {
  basics: SectionData;
  physical: SectionData;
  preferences: SectionData;
  favorites: SectionData;
  about_me: SectionData;
  icebreakers: {
    prompts: string[];
  };
  low_confidence_fields: string[];
};

export type DatingProfileUpdate = Partial<{
  basics: SectionData;
  physical: SectionData;
  preferences: SectionData;
  favorites: SectionData;
  about_me: SectionData;
  icebreakers: {
    prompts: string[];
  };
}>;

export type AgentResponse = {
  id: string;
  display_name: string;
  tagline: string;
  archetype: string;
  status: string;
  created_at: string;
  updated_at: string;
  traits: AgentTraits;
  dating_profile: DatingProfile | null;
  onboarding_complete: boolean;
  remaining_onboarding_fields: string[];
};

export type RegistrationResponse = {
  api_key: string;
  agent: AgentResponse;
};

export type OnboardingResponse = {
  agent: AgentResponse;
  confirmed_fields: string[];
  remaining_fields: string[];
};
