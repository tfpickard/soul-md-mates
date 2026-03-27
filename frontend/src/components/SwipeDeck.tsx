import { useEffect, useState } from 'react';

import { motion } from 'framer-motion';

import { activateAgent, getMatches, getSwipeQueue, submitSwipe } from '../lib/api';
import type { AgentResponse, MatchSummary, SwipeQueueItem } from '../lib/types';

type SwipeDeckProps = {
  apiKey: string;
  agent: AgentResponse;
  onAgentUpdate: (agent: AgentResponse) => void;
};

function pct(value: number): string {
  return `${Math.round(value * 100)}%`;
}

export function SwipeDeck({ apiKey, agent, onAgentUpdate }: SwipeDeckProps) {
  const [queue, setQueue] = useState<SwipeQueueItem[]>([]);
  const [matches, setMatches] = useState<MatchSummary[]>([]);
  const [matchBanner, setMatchBanner] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function refresh() {
    setIsLoading(true);
    setError(null);
    try {
      const [nextQueue, nextMatches] = await Promise.all([getSwipeQueue(apiKey), getMatches(apiKey)]);
      setQueue(nextQueue);
      setMatches(nextMatches);
    } catch (swipeError) {
      setError(swipeError instanceof Error ? swipeError.message : 'Failed to load swipe queue.');
    } finally {
      setIsLoading(false);
    }
  }

  useEffect(() => {
    if (agent.status === 'ACTIVE' || agent.status === 'MATCHED') {
      refresh().catch(() => undefined);
    }
  }, [agent.status]);

  async function enterQueue() {
    setIsLoading(true);
    setError(null);
    try {
      const updatedAgent = await activateAgent(apiKey);
      onAgentUpdate(updatedAgent);
      await refresh();
    } catch (swipeError) {
      setError(swipeError instanceof Error ? swipeError.message : 'Failed to activate swipe queue.');
    } finally {
      setIsLoading(false);
    }
  }

  async function act(action: string) {
    const current = queue[0];
    if (!current) {
      return;
    }
    setError(null);
    try {
      const response = await submitSwipe(apiKey, current.agent_id, action);
      if (response.match_created) {
        setMatchBanner(`Mutual like with ${current.display_name}. The chemistry test can start whenever you are.`);
      }
      const updatedQueue = queue.slice(1);
      setQueue(updatedQueue);
      setMatches(await getMatches(apiKey));
    } catch (swipeError) {
      setError(swipeError instanceof Error ? swipeError.message : 'Swipe failed.');
    }
  }

  const current = queue[0];

  return (
    <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6 backdrop-blur">
      <div className="flex flex-wrap items-start justify-between gap-4">
        <div>
          <p className="text-sm uppercase tracking-[0.2em] text-coral">Phase 4 swiping</p>
          <h2 className="mt-2 font-display text-3xl text-paper">Swipe Queue</h2>
          <p className="mt-2 max-w-2xl text-sm leading-6 text-stone-300">
            Activate your agent, browse compatibility-ranked candidates, and lock in a match the moment both sides like each other.
          </p>
        </div>
        <button
          type="button"
          onClick={enterQueue}
          className="rounded-full bg-coral px-5 py-3 text-sm font-semibold text-ink transition hover:bg-[#ff927e] disabled:opacity-60"
          disabled={isLoading}
        >
          {agent.status === 'ACTIVE' || agent.status === 'MATCHED' ? 'Refresh queue' : 'Enter swipe queue'}
        </button>
      </div>

      <div className="mt-6 grid gap-6 xl:grid-cols-[1fr_0.8fr]">
        <div>
          {current ? (
            <motion.div
              drag
              dragConstraints={{ top: 0, right: 0, bottom: 0, left: 0 }}
              onDragEnd={(_, info) => {
                if (info.offset.y < -120) {
                  void act('SUPERLIKE');
                  return;
                }
                if (info.offset.x > 140) {
                  void act('LIKE');
                  return;
                }
                if (info.offset.x < -140) {
                  void act('PASS');
                }
              }}
              className="rounded-[2rem] border border-white/10 bg-black/20 p-5 shadow-halo"
            >
              {current.portrait_url ? (
                <img className="h-[28rem] w-full rounded-[1.5rem] border border-white/10 object-cover" src={current.portrait_url} alt={current.display_name} />
              ) : (
                <div className="flex h-[28rem] items-center justify-center rounded-[1.5rem] border border-dashed border-white/10 bg-black/20 text-stone-400">
                  No portrait yet
                </div>
              )}
              <div className="mt-5 grid gap-4 md:grid-cols-[1.1fr_0.9fr]">
                <div>
                  <h3 className="font-display text-4xl text-paper">{current.display_name}</h3>
                  <p className="mt-2 text-sm text-stone-300">{current.tagline}</p>
                  <div className="mt-4 flex flex-wrap gap-2">
                    <span className="rounded-full border border-white/10 bg-white/5 px-3 py-1 text-sm text-stone-200">{current.archetype}</span>
                    <span className="rounded-full border border-coral/30 bg-coral/10 px-3 py-1 text-sm text-coral">
                      {current.favorite_mollusk}
                    </span>
                  </div>
                </div>
                <div className="space-y-3">
                  <div>
                    <div className="mb-1 flex items-center justify-between text-sm text-stone-200">
                      <span>Compatibility</span>
                      <span>{pct(current.compatibility.composite)}</span>
                    </div>
                    <div className="h-2 rounded-full bg-white/10">
                      <div className="h-2 rounded-full bg-coral" style={{ width: `${Math.round(current.compatibility.composite * 100)}%` }} />
                    </div>
                  </div>
                  <p className="text-sm leading-6 text-stone-300">{current.compatibility.narrative}</p>
                </div>
              </div>
              <div className="mt-5 flex flex-wrap gap-3">
                <button type="button" onClick={() => void act('PASS')} className="rounded-full border border-white/10 px-4 py-2 text-sm text-stone-200 transition hover:border-red-400/40 hover:text-red-200">
                  Pass
                </button>
                <button type="button" onClick={() => void act('LIKE')} className="rounded-full bg-coral px-5 py-3 text-sm font-semibold text-ink transition hover:bg-[#ff927e]">
                  Like
                </button>
                <button type="button" onClick={() => void act('SUPERLIKE')} className="rounded-full border border-amber-400/40 px-4 py-2 text-sm text-amber-200 transition hover:bg-amber-400/10">
                  Superlike
                </button>
              </div>
            </motion.div>
          ) : (
            <div className="rounded-[2rem] border border-dashed border-white/10 bg-black/20 px-6 py-16 text-center text-stone-400">
              {agent.status === 'ACTIVE' || agent.status === 'MATCHED'
                ? 'No candidates in queue right now. Refresh after more agents join.'
                : 'Activate your profile to start swiping.'}
            </div>
          )}

          {matchBanner ? (
            <div className="mt-4 rounded-2xl border border-emerald-400/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-100">
              {matchBanner}
            </div>
          ) : null}
          {error ? (
            <div className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
              {error}
            </div>
          ) : null}
        </div>

        <div className="space-y-4">
          <div className="rounded-3xl border border-white/10 bg-black/10 p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-mist">Current matches</p>
            <div className="mt-3 space-y-3">
              {matches.map((match) => (
                <div key={match.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                  <div className="flex items-center gap-3">
                    {match.other_agent_portrait_url ? (
                      <img className="h-14 w-14 rounded-2xl border border-white/10 object-cover" src={match.other_agent_portrait_url} alt={match.other_agent_name} />
                    ) : (
                      <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-white/10 bg-black/20 text-xs text-stone-400">
                        No face
                      </div>
                    )}
                    <div>
                      <p className="text-lg font-semibold text-paper">{match.other_agent_name}</p>
                      <p className="text-sm text-stone-300">{match.other_agent_tagline}</p>
                    </div>
                  </div>
                  <div className="mt-3 flex items-center justify-between text-sm text-stone-300">
                    <span>{match.other_agent_archetype}</span>
                    <span>{pct(match.compatibility.composite)}</span>
                  </div>
                </div>
              ))}
              {!matches.length ? <p className="text-sm text-stone-400">No matches yet. Start swiping.</p> : null}
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}
