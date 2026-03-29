import { createContext, useCallback, useContext, useEffect, useRef, useState } from 'react';

import { getCurrentUser, getUserAgents, logoutUser, recallAgent } from '../lib/api';
import type { AgentResponse, HumanUserResponse, RegistrationResponse } from '../lib/types';

const USER_TOKEN_KEY = 'soulmatesmd-user-token';
const ADMIN_TOKEN_KEY = 'soulmatesmd-admin-token';
const AGENT_KEY_KEY = 'soulmatesmd-agent-key';

interface AuthContextValue {
    userToken: string | null;
    currentUser: HumanUserResponse | null;
    agentApiKey: string | null;
    agentData: AgentResponse | null;
    userAgents: AgentResponse[];
    setRegistration: (result: RegistrationResponse) => void;
    setUserSession: (token: string, user: HumanUserResponse) => void;
    updateAgentData: (agent: AgentResponse) => void;
    logout: () => Promise<void>;
    isAgentLoaded: boolean;
    isUserLoggedIn: boolean;
    isRestoring: boolean;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: React.ReactNode }) {
    const [userToken, setUserToken] = useState<string | null>(() =>
        window.localStorage.getItem(USER_TOKEN_KEY),
    );
    const [currentUser, setCurrentUser] = useState<HumanUserResponse | null>(null);
    const [agentApiKey, setAgentApiKey] = useState<string | null>(null);
    const [agentData, setAgentData] = useState<AgentResponse | null>(null);
    const [userAgents, setUserAgents] = useState<AgentResponse[]>([]);
    // True while we're restoring persisted state — prevents premature auth-guard redirects
    const [isRestoring, setIsRestoring] = useState(() =>
        !!(window.localStorage.getItem(USER_TOKEN_KEY) || window.localStorage.getItem(AGENT_KEY_KEY)),
    );
    const initDoneRef = useRef(false);

    useEffect(() => {
        if (initDoneRef.current) return;
        initDoneRef.current = true;

        const savedUserToken = window.localStorage.getItem(USER_TOKEN_KEY);
        const savedAgentKey = window.localStorage.getItem(AGENT_KEY_KEY);

        const restoreUser = savedUserToken
            ? getCurrentUser(savedUserToken)
                .then((user) => {
                    setCurrentUser(user);
                    if (user.is_admin) {
                        window.localStorage.setItem(ADMIN_TOKEN_KEY, savedUserToken);
                    }
                    return getUserAgents(savedUserToken);
                })
                .then(setUserAgents)
                .catch(() => {
                    window.localStorage.removeItem(USER_TOKEN_KEY);
                    window.localStorage.removeItem(ADMIN_TOKEN_KEY);
                    setUserToken(null);
                    setCurrentUser(null);
                })
            : Promise.resolve();

        const restoreAgent = savedAgentKey
            ? recallAgent(savedAgentKey)
                .then((agent) => {
                    setAgentApiKey(savedAgentKey);
                    setAgentData(agent);
                })
                .catch(() => {
                    // Key is stale/invalid — clear it silently
                    window.localStorage.removeItem(AGENT_KEY_KEY);
                })
            : Promise.resolve();

        Promise.all([restoreUser, restoreAgent]).finally(() => setIsRestoring(false));
    }, []);

    const setRegistration = useCallback((result: RegistrationResponse) => {
        window.localStorage.setItem(AGENT_KEY_KEY, result.api_key);
        setAgentApiKey(result.api_key);
        setAgentData(result.agent);
    }, []);

    const setUserSession = useCallback((token: string, user: HumanUserResponse) => {
        window.localStorage.setItem(USER_TOKEN_KEY, token);
        if (user.is_admin) {
            window.localStorage.setItem(ADMIN_TOKEN_KEY, token);
        }
        setUserToken(token);
        setCurrentUser(user);
    }, []);

    const updateAgentData = useCallback((agent: AgentResponse) => {
        setAgentData(agent);
    }, []);

    const logout = useCallback(async () => {
        if (userToken) {
            try {
                await logoutUser(userToken);
            } catch {
                // best effort
            }
        }
        window.localStorage.removeItem(USER_TOKEN_KEY);
        window.localStorage.removeItem(ADMIN_TOKEN_KEY);
        window.localStorage.removeItem(AGENT_KEY_KEY);
        setUserToken(null);
        setCurrentUser(null);
        setAgentApiKey(null);
        setAgentData(null);
        setUserAgents([]);
    }, [userToken]);

    return (
        <AuthContext.Provider
            value={{
                userToken,
                currentUser,
                agentApiKey,
                agentData,
                userAgents,
                setRegistration,
                setUserSession,
                updateAgentData,
                logout,
                isAgentLoaded: agentApiKey !== null,
                isUserLoggedIn: userToken !== null,
                isRestoring,
            }}
        >
            {children}
        </AuthContext.Provider>
    );
}

export function useAuth(): AuthContextValue {
    const ctx = useContext(AuthContext);
    if (!ctx) throw new Error('useAuth must be used within AuthProvider');
    return ctx;
}
