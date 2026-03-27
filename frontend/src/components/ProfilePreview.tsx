import type { DatingProfile, SectionData } from '../lib/types';

type ProfilePreviewProps = {
  profile: DatingProfile;
};

const SECTION_LABELS: Array<{ key: keyof DatingProfile; label: string }> = [
  { key: 'basics', label: 'Basics' },
  { key: 'physical', label: 'Physical' },
  { key: 'preferences', label: 'Preferences' },
  { key: 'favorites', label: 'Favorites' },
  { key: 'about_me', label: 'About Me' },
  { key: 'icebreakers', label: 'Icebreakers' },
];

function formatLabel(value: string): string {
  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

function renderValue(value: string | string[]) {
  if (Array.isArray(value)) {
    return (
      <ul className="mt-2 space-y-1 text-sm text-stone-300">
        {value.map((item) => (
          <li key={item} className="rounded-2xl border border-white/10 bg-black/10 px-3 py-2">
            {item}
          </li>
        ))}
      </ul>
    );
  }

  return <p className="mt-2 text-sm leading-6 text-stone-300">{value}</p>;
}

export function ProfilePreview({ profile }: ProfilePreviewProps) {
  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <p className="text-sm uppercase tracking-[0.2em] text-coral">Seeded dating profile</p>
      <h2 className="mt-2 font-display text-3xl text-paper">Profile Preview</h2>
      <div className="mt-6 space-y-4">
        {SECTION_LABELS.map(({ key, label }) => {
          if (key === 'low_confidence_fields') {
            return null;
          }
          const section = profile[key] as SectionData;
          return (
            <details key={String(key)} className="rounded-3xl border border-white/10 bg-black/10 p-4" open>
              <summary className="cursor-pointer list-none text-lg font-semibold text-paper">{label}</summary>
              <div className="mt-4 grid gap-4 md:grid-cols-2">
                {Object.entries(section).map(([fieldName, value]) => (
                  <div key={fieldName} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                    <p className="text-xs uppercase tracking-[0.18em] text-mist">{formatLabel(fieldName)}</p>
                    {renderValue(value)}
                  </div>
                ))}
              </div>
            </details>
          );
        })}
      </div>
    </section>
  );
}
