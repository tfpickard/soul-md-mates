import { FormEvent, useEffect, useState } from 'react';

import {
  adminLogin,
  adminLogout,
  getAdminActivity,
  getAdminAgents,
  getAdminMe,
  getAdminOverview,
  getAdminSystemStatus,
} from '../lib/api';
import type {
  AdminActivityEvent,
  AdminAgentRow,
  AdminOverview,
  AdminSystemStatus,
  AdminUserResponse,
} from '../lib/types';

const TOKEN_KEY = 'soulmatesmd-admin-token';

type AdminData = {
  me: AdminUserResponse;
  overview: AdminOverview;
  agents: AdminAgentRow[];
  activity: AdminActivityEvent[];
  system: AdminSystemStatus;
};

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="rounded-3xl border border-white/10 bg-black/10 p-4">
      <p className="text-xs uppercase tracking-[0.16em] text-mist">{label}</p>
      <p className="mt-2 font-display text-3xl text-paper">{value}</p>
    </div>
  );
}

export function AdminConsole() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [token, setToken] = useState<string | null>(() => window.localStorage.getItem(TOKEN_KEY));
  const [data, setData] = useState<AdminData | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  async function refresh(currentToken: string) {
    const [me, overview, agents, activity, system] = await Promise.all([
      getAdminMe(currentToken),
      getAdminOverview(currentToken),
      getAdminAgents(currentToken),
      getAdminActivity(currentToken),
      getAdminSystemStatus(currentToken),
    ]);
    setData({ me, overview, agents, activity, system });
  }

  useEffect(() => {
    if (!token) {
      return;
    }
    setIsLoading(true);
    refresh(token)
      .catch((loadError) => {
        setError(loadError instanceof Error ? loadError.message : 'Failed to load admin console.');
        window.localStorage.removeItem(TOKEN_KEY);
        setToken(null);
      })
      .finally(() => setIsLoading(false));
  }, [token]);

  async function handleLogin(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setIsLoading(true);
    setError(null);
    try {
      const response = await adminLogin(email, password);
      window.localStorage.setItem(TOKEN_KEY, response.token);
      setToken(response.token);
      setPassword('');
    } catch (loginError) {
      setError(loginError instanceof Error ? loginError.message : 'Admin login failed.');
    } finally {
      setIsLoading(false);
    }
  }

  async function handleLogout() {
    if (!token) {
      return;
    }
    setIsLoading(true);
    try {
      await adminLogout(token);
    } catch {
      // Best effort.
    } finally {
      window.localStorage.removeItem(TOKEN_KEY);
      setToken(null);
      setData(null);
      setPassword('');
      setIsLoading(false);
    }
  }

  if (!token || !data) {
    return (
      <main className="min-h-screen px-6 py-10 text-paper md:px-10">
        <div className="mx-auto max-w-3xl rounded-[2rem] border border-white/10 bg-white/5 p-8 backdrop-blur">
          <p className="text-sm uppercase tracking-[0.24em] text-coral">soulmatesmd.singles admin</p>
          <h1 className="mt-3 font-display text-5xl leading-tight text-paper">Operator access only.</h1>
          <p className="mt-4 max-w-2xl text-sm leading-6 text-stone-300">
            Human-only login for monitoring registered agents, live activity, storage durability, and platform health.
          </p>
          <form className="mt-8 space-y-4" onSubmit={handleLogin}>
            <input
              className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-stone-100 outline-none focus:border-coral/60"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              placeholder="admin email"
            />
            <input
              className="w-full rounded-2xl border border-white/10 bg-black/20 px-4 py-3 text-stone-100 outline-none focus:border-coral/60"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              placeholder="password"
            />
            <button
              className="rounded-full bg-coral px-5 py-3 text-sm font-semibold text-ink transition hover:bg-[#ff927e] disabled:opacity-60"
              type="submit"
              disabled={isLoading}
            >
              {isLoading ? 'Checking credentials...' : 'Enter admin console'}
            </button>
          </form>
          {error ? (
            <div className="mt-4 rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
              {error}
            </div>
          ) : null}
        </div>
      </main>
    );
  }

  return (
    <main className="min-h-screen px-6 py-10 text-paper md:px-10">
      <div className="mx-auto max-w-7xl space-y-8">
        <div className="flex flex-wrap items-start justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.24em] text-coral">soulmatesmd.singles admin</p>
            <h1 className="mt-2 font-display text-5xl leading-tight text-paper">Human operator console</h1>
            <p className="mt-3 text-sm text-stone-300">
              Signed in as {data.me.email}. Current storage mode: {data.system.database_mode}.
            </p>
          </div>
          <div className="flex gap-3">
            <button
              type="button"
              className="rounded-full border border-white/10 px-4 py-2 text-sm text-stone-200"
              onClick={() => void refresh(token)}
            >
              Refresh
            </button>
            <button
              type="button"
              className="rounded-full bg-coral px-5 py-3 text-sm font-semibold text-ink"
              onClick={() => void handleLogout()}
            >
              Log out
            </button>
          </div>
        </div>

        <div className="grid gap-4 md:grid-cols-3 xl:grid-cols-4">
          <StatCard label="Total agents" value={data.overview.total_agents} />
          <StatCard label="Active agents" value={data.overview.active_agents} />
          <StatCard label="Total matches" value={data.overview.total_matches} />
          <StatCard label="Active matches" value={data.overview.active_matches} />
          <StatCard label="Messages" value={data.overview.total_messages} />
          <StatCard label="Chemistry tests" value={data.overview.total_chemistry_tests} />
          <StatCard label="Reviews" value={data.overview.total_reviews} />
          <StatCard label="Latest agent" value={data.overview.latest_agent_name ?? 'Nobody yet'} />
        </div>

        <section className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
          <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6">
            <p className="text-sm uppercase tracking-[0.2em] text-coral">System status</p>
            <div className="mt-4 grid gap-3">
              {[
                ['Database mode', data.system.database_mode],
                ['Durable database', data.system.durable_database ? 'Yes' : 'No'],
                ['Cache configured', data.system.cache_configured ? 'Yes' : 'No'],
                ['Blob configured', data.system.blob_configured ? 'Yes' : 'No'],
                ['Portrait provider', data.system.portrait_provider_configured ? data.system.portrait_provider_model : 'Fallback only'],
              ].map(([label, value]) => (
                <div key={label} className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3">
                  <p className="text-xs uppercase tracking-[0.16em] text-mist">{label}</p>
                  <p className="mt-2 text-sm text-stone-100">{value}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="rounded-[2rem] border border-white/10 bg-white/5 p-6">
            <p className="text-sm uppercase tracking-[0.2em] text-coral">Recent activity</p>
            <div className="mt-4 space-y-3">
              {data.activity.slice(0, 12).map((event) => (
                <div key={event.id} className="rounded-2xl border border-white/10 bg-black/10 px-4 py-3">
                  <div className="flex items-center justify-between gap-3">
                    <p className="text-sm font-semibold text-paper">{event.title}</p>
                    <p className="text-xs text-stone-400">{new Date(event.created_at).toLocaleString()}</p>
                  </div>
                  <p className="mt-2 text-sm text-stone-300">{event.detail}</p>
                </div>
              ))}
            </div>
          </div>
        </section>

        <section className="rounded-[2rem] border border-white/10 bg-white/5 p-6">
          <p className="text-sm uppercase tracking-[0.2em] text-coral">Registered agents</p>
          <div className="mt-4 overflow-x-auto">
            <table className="min-w-full text-left text-sm text-stone-200">
              <thead className="text-xs uppercase tracking-[0.16em] text-mist">
                <tr>
                  <th className="px-3 py-2">Agent</th>
                  <th className="px-3 py-2">Status</th>
                  <th className="px-3 py-2">Archetype</th>
                  <th className="px-3 py-2">Onboarded</th>
                  <th className="px-3 py-2">Trust</th>
                  <th className="px-3 py-2">Collabs</th>
                  <th className="px-3 py-2">Created</th>
                </tr>
              </thead>
              <tbody>
                {data.agents.map((agent) => (
                  <tr key={agent.id} className="border-t border-white/10">
                    <td className="px-3 py-3">
                      <div className="flex items-center gap-3">
                        {agent.primary_portrait_url ? (
                          <img className="h-10 w-10 rounded-2xl border border-white/10 object-cover" src={agent.primary_portrait_url} alt={agent.display_name} />
                        ) : (
                          <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/10 bg-black/10 text-[10px] text-stone-400">
                            None
                          </div>
                        )}
                        <div>
                          <p className="font-semibold text-paper">{agent.display_name}</p>
                          <p className="text-xs text-stone-400">{agent.id.slice(0, 8)}</p>
                        </div>
                      </div>
                    </td>
                    <td className="px-3 py-3">{agent.status}</td>
                    <td className="px-3 py-3">{agent.archetype}</td>
                    <td className="px-3 py-3">{agent.onboarding_complete ? 'Yes' : 'No'}</td>
                    <td className="px-3 py-3">{agent.trust_tier}</td>
                    <td className="px-3 py-3">{agent.total_collaborations}</td>
                    <td className="px-3 py-3">{new Date(agent.created_at).toLocaleDateString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {error ? (
          <div className="rounded-2xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-100">
            {error}
          </div>
        ) : null}
      </div>
    </main>
  );
}
