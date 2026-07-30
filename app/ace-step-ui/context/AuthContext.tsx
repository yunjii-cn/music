import React, { createContext, useContext, useState, useEffect, useCallback, ReactNode } from 'react';
import { authApi, User, UMLoginPayload } from '../services/api';

interface AuthContextType {
  user: User | null;
  token: string | null;
  isLoading: boolean;
  isValidating: boolean;
  isAuthenticated: boolean;
  needsLogin: boolean;
  setupUser: (username: string) => Promise<void>;
  updateUsername: (username: string) => Promise<void>;
  loginWithUM: (umUser: UMLoginPayload) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

const TOKEN_KEY = 'acestep_token';
const USER_KEY = 'acestep_user';

// UM 单点登出收口页（与登录页对称，构建时可用 VITE_UM_LOGOUT_URL 覆盖）。
// 跳转参数：redirect=<回跳地址>&embed=1。UM 会清服务端 session + um_sso_token
// 共享 cookie，再回跳 redirect（启动器首页，已登出态、URL 不带 yunji_user）。
const UM_LOGOUT_URL =
  (import.meta.env.VITE_UM_LOGOUT_URL as string | undefined) ||
  'https://music.yunjii.cn/um/logout.php';

export function AuthProvider({ children }: { children: ReactNode }): React.ReactElement {
  // Restore any existing session synchronously from localStorage (persisted
  // after a successful UM login) so returning users don't see a login flash.
  const [user, setUser] = useState<User | null>(() => {
    const raw = localStorage.getItem(USER_KEY);
    try {
      return raw ? (JSON.parse(raw) as User) : null;
    } catch {
      return null;
    }
  });
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY));
  const [isLoading, setIsLoading] = useState(true);
  const [needsLogin, setNeedsLogin] = useState(false);
  // True while we are verifying a restored token against the backend. Starts
  // true only when there is a token to check, so first-time users don't wait.
  const [isValidating, setIsValidating] = useState<boolean>(
    () => !!localStorage.getItem(TOKEN_KEY),
  );

  const isAuthenticated = !!user && !!token;

  // On mount: verify any restored token with the backend (GET /api/auth/me).
  // A stale / expired / tampered token is cleared so the LoginGate can send the
  // user through the official 云集 login page (music.yunjii.cn) again. This
  // prevents a lingering localStorage token from silently bypassing the gate.
  useEffect(() => {
    const restored = localStorage.getItem(TOKEN_KEY);
    if (!restored) {
      // No session at all → gate will redirect to the login page.
      setNeedsLogin(true);
      setIsValidating(false);
      setIsLoading(false);
      return;
    }

    let cancelled = false;
    authApi
      .me(restored)
      .then(({ user: userData }) => {
        if (cancelled) return;
        // Token is valid → keep the session and refresh the user record.
        setUser(userData);
        setToken(restored);
        localStorage.setItem(USER_KEY, JSON.stringify(userData));
        setNeedsLogin(false);
      })
      .catch(() => {
        if (cancelled) return;
        // Token invalid / expired → drop it and require a fresh login.
        setUser(null);
        setToken(null);
        localStorage.removeItem(TOKEN_KEY);
        localStorage.removeItem(USER_KEY);
        setNeedsLogin(true);
      })
      .finally(() => {
        if (cancelled) return;
        setIsValidating(false);
        setIsLoading(false);
      });

    return () => {
      cancelled = true;
    };
  }, []);

  const setupUser = useCallback(async (username: string): Promise<void> => {
    const { user: userData, token: newToken } = await authApi.setup(username);
    setUser(userData);
    setToken(newToken);
    setNeedsLogin(false);
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
  }, []);

  const updateUsername = useCallback(async (username: string): Promise<void> => {
    if (!token) throw new Error('Not authenticated');
    const { user: userData, token: newToken } = await authApi.updateUsername(username, token);
    setUser(userData);
    setToken(newToken);
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
  }, [token]);

  // Sign in via the official 云集 login page: it posts the UM user info here
  // after a successful scan-code login, and we exchange it for a local JWT.
  const loginWithUM = useCallback(async (umUser: UMLoginPayload): Promise<void> => {
    const { user: userData, token: newToken } = await authApi.umLogin(umUser);
    setUser(userData);
    setToken(newToken);
    setNeedsLogin(false);
    localStorage.setItem(TOKEN_KEY, newToken);
    localStorage.setItem(USER_KEY, JSON.stringify(userData));
  }, []);

  const logout = useCallback((): void => {
    // 先注销本地后端 session（fire-and-forget，随后整页跳转会中断该请求也无妨）
    authApi.logout().catch(() => {});
    // 打「主动退出」标记：UM 登出后回跳启动器时，LoginGate 据此停在
    // 「已退出」页而不是立刻又跳登录，给用户一个明确的已退出确认。
    // sessionStorage 在同标签页跨域往返（跳 UM 再回来）后仍然保留。
    try {
      sessionStorage.setItem('yunji_manual_logout', '1');
    } catch {
      /* sessionStorage 不可用时忽略，最坏情况退回停在门控页 */
    }
    // 清本地态（token/user）
    setUser(null);
    setToken(null);
    localStorage.removeItem(TOKEN_KEY);
    localStorage.removeItem(USER_KEY);
    // 走 UM 单点登出：清 UM 服务端 session + um_sso_token 共享 cookie，
    // 然后回跳启动器首页（已登出态）。这样退出是真的退出——UM 侧 cookie 被清，
    // 重新登录会要求重新扫码，不会再「退出即重登」。
    try {
      const redirect = window.location.origin + '/';
      const url = new URL(UM_LOGOUT_URL);
      url.searchParams.set('redirect', redirect);
      url.searchParams.set('embed', '1');
      window.location.href = url.toString();
    } catch {
      /* URL 构造/跳转失败时退回纯前端登出：本地态已清，门控会停在已退出页 */
    }
  }, []);

  const refreshUser = useCallback(async (): Promise<void> => {
    if (!token) return;
    try {
      const { user: userData } = await authApi.me(token);
      setUser(userData);
      localStorage.setItem(USER_KEY, JSON.stringify(userData));
    } catch (error) {
      console.error('Failed to refresh user:', error);
    }
  }, [token]);

  const value: AuthContextType = {
    user,
    token,
    isLoading,
    isValidating,
    isAuthenticated,
    needsLogin,
    setupUser,
    updateUsername,
    loginWithUM,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
