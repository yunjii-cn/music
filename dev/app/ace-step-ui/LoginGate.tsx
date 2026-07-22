import React, { useEffect, useState } from 'react';
import { useAuth } from './context/AuthContext';
import type { UMLoginPayload } from './services/api';

// 官网统一登录页（构建时可用 VITE_UM_LOGIN_URL 覆盖，默认音乐官网登录页）
const UM_LOGIN_URL =
  (import.meta.env.VITE_UM_LOGIN_URL as string | undefined) ||
  'https://music.yunjii.cn/login';

// 会话存储键
const STATE_KEY = 'yunji_login_state'; // 防 CSRF 的随机 state
const VISITED_KEY = 'yunji_login_visited'; // 标记已跳转过，避免回跳失败死循环
const MANUAL_LOGOUT_KEY = 'yunji_manual_logout'; // 主动退出标记，避免退出后立即自动重登

type GateStatus = 'redirecting' | 'processing' | 'error';

/**
 * 启动前端网页登录门控。
 *
 * 流程（跨域 / localhost 场景，沿用官网登录页约定）：
 *   1. 未登录时，整页 302 跳到官网登录页：
 *        music.yunjii.cn/login?embed=1&redirect=<本应用地址>&state=<随机串>
 *      - embed=1 隐藏官网顶栏，看起来就是一张登录页
 *      - redirect 指向本应用自己（启动器打开的音乐工作台），登录后回跳回来
 *      - state 用于防 CSRF
 *   2. 官网登录成功后，回跳到 redirect 并在 URL query 带上 yunji_user
 *      （base64 JSON，含 social_uid/openid、nickname、faceimg、token 等 UM 信息）
 *   3. 本门控读取并解码 yunji_user，调用后端 /api/auth/um 换本地 JWT，
 *      登录成功后才渲染真正的应用（<App />）。
 *
 * 参考：官网登录页已调试好，回跳地址即上面的 redirect（localhost 场景 token 在
 *      URL query 里没问题；公网域名回跳需谨慎，可改用 code 换 token 方案）。
 */
export default function LoginGate({ children }: { children: React.ReactNode }): React.ReactElement {
  const { isAuthenticated, isValidating, loginWithUM } = useAuth();
  const [status, setStatus] = useState<GateStatus>('redirecting');
  const [error, setError] = useState<string | null>(null);

  // base64（兼容标准 / urlsafe / 缺填充）解码为 UTF-8 字符串
  function b64DecodeUtf8(b64: string): string {
    let s = b64.replace(/-/g, '+').replace(/_/g, '/');
    while (s.length % 4) s += '=';
    const bin = atob(s);
    const bytes = Uint8Array.from(bin, (c) => c.charCodeAt(0));
    return new TextDecoder().decode(bytes);
  }

  // 解码官网回跳 URL 里的 yunji_user（base64 JSON）
  function decodeYunjiUser(b64: string): Record<string, unknown> | null {
    try {
      const obj = JSON.parse(b64DecodeUtf8(b64));
      return obj && typeof obj === 'object' ? obj : null;
    } catch {
      return null;
    }
  }

  // 从对象里按候选键顺序取第一个非空字符串值
  function pickStr(obj: Record<string, unknown>, keys: string[]): string {
    for (const k of keys) {
      const v = obj[k];
      if (typeof v === 'string' && v.trim()) return v.trim();
    }
    return '';
  }

  // 把 yunji_user 对象映射成后端 /api/auth/um 需要的 UMLoginPayload
  // 兼容官网登录页/微信各种可能的字段命名，避免昵称或头像漏传导致
  // 登录后显示成兜底用户名 + 默认首字母头像。
  function toUMLoginPayload(obj: Record<string, unknown>): UMLoginPayload {
    const socialUid = pickStr(obj, ['social_uid', 'openid', 'uid', 'unionid', 'wx_openid']);
    const nickname = pickStr(obj, [
      'nickname',
      'nickName',
      'name',
      'wx_nickname',
      'display_name',
      'displayName',
      'uname',
      'username',
    ]);
    const faceimg = pickStr(obj, [
      'faceimg',
      'face_img',
      'avatar',
      'avatar_url',
      'avatarUrl',
      'headimgurl',
      'headimg',
      'head_img',
      'headImgUrl',
      'pic',
      'photo',
      'userAvatar',
      'img',
    ]);
    return { social_uid: socialUid, nickname, faceimg, raw: obj };
  }

  // 拼接官网登录页地址：embed=1 隐藏顶栏，redirect=回跳地址，state=防 CSRF
  function buildLoginUrl(redirect: string): string {
    const url = new URL(UM_LOGIN_URL);
    url.searchParams.set('embed', '1');
    url.searchParams.set('redirect', redirect);
    const state = Math.random().toString(36).slice(2) + Date.now().toString(36);
    try {
      sessionStorage.setItem(STATE_KEY, state);
    } catch {
      /* sessionStorage 不可用时忽略，state 校验降级为不校验 */
    }
    url.searchParams.set('state', state);
    return url.toString();
  }

  // 重新跳转到官网登录页（用于手动重试 / 退出后重新登录）
  function goLogin() {
    // 清掉「主动退出」标记，让回跳的 yunji_user 能被正常处理
    try {
      sessionStorage.removeItem(MANUAL_LOGOUT_KEY);
    } catch {
      /* ignore */
    }
    const clean = window.location.pathname + window.location.hash;
    const loginUrl = buildLoginUrl(window.location.origin + clean);
    setStatus('redirecting');
    setError(null);
    window.location.href = loginUrl;
  }

  useEffect(() => {
    // 正在向后端校验已恢复的 token → 先等结果，不跳转也不放行
    if (isValidating) return;
    // 已登录 → 直接进入应用
    if (isAuthenticated) return;

    // 主动退出：logout() 已走 UM 单点登出（清了 UM 服务端 session +
    // um_sso_token 共享 cookie）并回跳到这里。此时停在「已退出」页，
    // 给用户明确的已登出确认；不自动跳登录。用户主动点「重新登录」时
    // goLogin 会清掉这个标记，且因 UM cookie 已清，会要求重新扫码。
    let manualLogout = false;
    try {
      manualLogout = !!sessionStorage.getItem(MANUAL_LOGOUT_KEY);
    } catch {
      /* ignore */
    }
    if (manualLogout) {
      setStatus('loggedout');
      setError(null);
      return;
    }

    const params = new URLSearchParams(window.location.search);
    const yunjiUser = params.get('yunji_user');
    const returnedState = params.get('state');

    let savedState: string | null = null;
    try {
      savedState = sessionStorage.getItem(STATE_KEY);
      sessionStorage.removeItem(STATE_KEY);
    } catch {
      /* ignore */
    }

    // 情况 A：官网登录成功回跳，URL 带 yunji_user
    if (yunjiUser) {
      const obj = decodeYunjiUser(yunjiUser);
      const stateOk = !returnedState || !savedState || returnedState === savedState;
      if (obj && stateOk) {
        setStatus('processing');
        setError(null);
        loginWithUM(toUMLoginPayload(obj))
          .then(() => {
            // 清理 URL 里的凭证，避免泄漏 / 刷新重放
            const clean = window.location.pathname + window.location.hash;
            window.history.replaceState({}, document.title, clean);
            try {
              sessionStorage.removeItem(VISITED_KEY);
            } catch {
              /* ignore */
            }
          })
          .catch((err) => {
            setStatus('error');
            setError(String((err && (err as Error)?.message) || err));
          });
        return;
      }
    }

    // 情况 B：回跳过（带 state 或已有访问标记）但没有 yunji_user
    //      → 视为取消/失败，显示门控卡 + 重试，避免无限重定向
    let visited = false;
    try {
      visited = !!sessionStorage.getItem(VISITED_KEY);
    } catch {
      /* ignore */
    }
    if (returnedState || visited) {
      setStatus('error');
      setError(error || '登录未完成，请重试。');
      return;
    }

    // 情况 C：首次进入且未登录 → 整页跳官网登录页
    const clean = window.location.pathname + window.location.hash;
    try {
      sessionStorage.setItem(VISITED_KEY, '1');
    } catch {
      /* ignore */
    }
    const loginUrl = buildLoginUrl(window.location.origin + clean);
    setStatus('redirecting');
    setError(null);
    window.location.href = loginUrl;
  }, [isAuthenticated, isValidating, loginWithUM]);

  // 校验期间即使有残留 token 也不放行，等后端确认后再决定
  if (isAuthenticated && !isValidating) {
    return <>{children}</>;
  }

  const statusText = isValidating
    ? '正在验证登录…'
    : status === 'redirecting'
      ? '正在跳转到云集登录…'
      : status === 'processing'
        ? '登录成功，正在进入工作台…'
        : status === 'loggedout'
          ? '你已退出登录'
          : '登录未完成';

  return (
    <div style={styles.overlay}>
      <style>{`@keyframes yunji-spin{to{transform:rotate(360deg)}}`}</style>
      <div style={styles.card}>
        <div style={styles.logo} aria-hidden>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M9 18V5l12-2v13" />
            <circle cx="6" cy="18" r="3" />
            <circle cx="18" cy="16" r="3" />
          </svg>
        </div>
        <div style={styles.title}>
          {status === 'loggedout'
            ? '云集智能音乐创意台'
            : (
              <>
                登录 <span style={{ color: '#8B5CF6' }}>云集智能音乐创意台</span>
              </>
            )}
        </div>

        {status === 'loggedout' ? (
          <div style={styles.logoutBadge} aria-hidden>
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
          </div>
        ) : status !== 'error' ? (
          <div style={styles.spinner} />
        ) : (
          <div style={styles.errorIcon} aria-hidden>
            <svg width="30" height="30" viewBox="0 0 24 24" fill="none" stroke="#ff6b6b" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="9" />
              <path d="M12 8v5M12 16h.01" />
            </svg>
          </div>
        )}

        {status === 'loggedout' ? (
          <>
            <div style={styles.logoutTitle}>你已退出登录</div>
            <div style={styles.logoutSub}>随时回来，继续你的音乐创作</div>
          </>
        ) : (
          <div style={styles.status}>{statusText}</div>
        )}

        {(status === 'error' || status === 'loggedout') && (
          <button style={styles.primaryBtn} onClick={goLogin}>
            {status === 'loggedout' ? '重新登录' : '重新登录'}
          </button>
        )}

        {error && status === 'error' && <div style={styles.error}>{error}</div>}

        {status !== 'loggedout' && (
          <>
            <div style={styles.hint}>
              登录即代表同意 <a href="#" style={styles.link}>用户协议</a> 和{' '}
              <a href="#" style={styles.link}>隐私政策</a>
            </div>

            <a
              href={UM_LOGIN_URL}
              target="_blank"
              rel="noopener"
              style={styles.manualLink}
            >
              或手动打开登录页
            </a>
          </>
        )}
      </div>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  overlay: {
    position: 'fixed',
    inset: 0,
    background: '#0a0a0f',
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    zIndex: 9999,
    fontFamily: '"Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
  },
  card: {
    position: 'relative',
    background: '#14141c',
    border: '1px solid #26263a',
    borderRadius: 20,
    padding: '40px 28px 28px',
    width: 380,
    maxWidth: 'calc(100vw - 32px)',
    textAlign: 'center',
    boxShadow: '0 20px 60px rgba(0,0,0,0.55), 0 0 0 1px rgba(139,92,246,0.15) inset',
  },
  logo: {
    width: 56,
    height: 56,
    borderRadius: 14,
    margin: '0 auto 18px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
    boxShadow: '0 0 24px rgba(139,92,246,0.45)',
  },
  title: { fontSize: 21, fontWeight: 700, marginBottom: 22, color: '#ece9f5' },
  spinner: {
    width: 34,
    height: 34,
    margin: '0 auto 18px',
    border: '3px solid rgba(139,92,246,0.25)',
    borderTopColor: '#8B5CF6',
    borderRadius: '50%',
    animation: 'yunji-spin 0.8s linear infinite',
  },
  errorIcon: { margin: '0 auto 16px' },
  logoutBadge: {
    width: 64,
    height: 64,
    borderRadius: '50%',
    margin: '0 auto 18px',
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
    boxShadow: '0 0 28px rgba(139,92,246,0.5)',
  },
  logoutTitle: { fontSize: 19, fontWeight: 700, color: '#ece9f5', marginBottom: 8 },
  logoutSub: { fontSize: 13, color: '#9a96b3', marginBottom: 24, lineHeight: 1.6 },
  status: { fontSize: 15, color: '#cfcae0', marginBottom: 20 },
  primaryBtn: {
    padding: '10px 28px',
    background: '#8B5CF6',
    border: 'none',
    color: '#fff',
    borderRadius: 10,
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
    marginBottom: 14,
  },
  hint: { fontSize: 12, color: '#6f6b88', marginTop: 8, lineHeight: 1.6 },
  link: { color: '#8B5CF6', textDecoration: 'none' },
  error: { fontSize: 12, color: '#ff6b6b', marginTop: 10, wordBreak: 'break-word' },
  manualLink: {
    display: 'inline-block',
    marginTop: 18,
    fontSize: 12,
    color: '#9a96b3',
    textDecoration: 'none',
  },
};
