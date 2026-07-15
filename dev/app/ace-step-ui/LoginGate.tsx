import React, { useEffect, useState } from 'react';
import { useAuth } from './context/AuthContext';
import type { UMLoginPayload } from './services/api';

// 官网登录页地址（构建时可用 VITE_UM_LOGIN_URL 覆盖，默认音乐官网）
const UM_LOGIN_URL =
  (import.meta.env.VITE_UM_LOGIN_URL as string | undefined) ||
  'https://music.yunjii.cn/um/index.php';

/**
 * 启动前端网页登录门控。
 *
 * 未登录时展示音乐紫主题的门控页，内嵌「官网登录页」(music.yunjii.cn/um) 的
 * 微信扫码登录；官网登录成功后通过 postMessage 把 UM 用户信息回传到这里，
 * 再调用后端 /api/auth/um 换取本地 JWT，登录成功后才渲染真正的应用。
 *
 * 复用官网登录页已具备的 UM 扫码逻辑（web/um/connect.php → loginSuccess）。
 */
export default function LoginGate({ children }: { children: React.ReactNode }): React.ReactElement {
  const { isAuthenticated, loginWithUM } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const [iframeError, setIframeError] = useState(false);

  // 监听官网登录页（iframe 或 window.open 弹窗）发来的 loginSuccess 消息
  useEffect(() => {
    function onMessage(e: MessageEvent) {
      const data = e.data as { type?: string; user?: UMLoginPayload } | null;
      if (data && data.type === 'loginSuccess' && data.user) {
        loginWithUM(data.user)
          .then(() => setError(null))
          .catch((err) => setError(String((err && (err as Error).message) || err)));
      }
    }
    window.addEventListener('message', onMessage);
    return () => window.removeEventListener('message', onMessage);
  }, [loginWithUM]);

  if (isAuthenticated) {
    return <>{children}</>;
  }

  const openPopup = () => {
    setError(null);
    const w = window.open(UM_LOGIN_URL, 'yunji_login', 'width=420,height=560');
    if (!w) {
      setError('浏览器拦截了登录弹窗，请允许弹窗后重试，或直接使用上方扫码登录。');
    }
  };

  return (
    <div style={styles.overlay}>
      <div style={styles.card}>
        <div style={styles.logo}>🎵</div>
        <div style={styles.title}>
          登录 <span style={{ color: '#8B5CF6' }}>云集智能音乐创意台</span>
        </div>
        <div style={styles.subtitle}>微信扫一扫，登录你的创作账户</div>

        {iframeError ? (
          <div style={styles.qrFallback}>
            <div style={styles.qrNote}>登录页加载失败，请使用弹窗登录：</div>
            <button style={styles.primaryBtn} onClick={openPopup}>
              使用弹窗登录
            </button>
          </div>
        ) : (
          <div style={styles.qrWrap}>
            <iframe
              src={UM_LOGIN_URL}
              title="云集登录"
              width={340}
              height={460}
              style={{ border: 'none', borderRadius: 12, background: '#1c1c28' }}
              onError={() => setIframeError(true)}
            />
          </div>
        )}

        <div style={styles.popupRow}>
          <button style={styles.ghostBtn} onClick={openPopup}>
            无法加载？使用弹窗登录
          </button>
        </div>

        <div style={styles.hint}>
          扫码即代表同意 <a href="#" style={styles.link}>用户协议</a> 和{' '}
          <a href="#" style={styles.link}>隐私政策</a>
        </div>
        {error && <div style={styles.error}>{error}</div>}
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
    fontSize: 28,
    background: 'linear-gradient(135deg, #8B5CF6, #6D28D9)',
    boxShadow: '0 0 24px rgba(139,92,246,0.45)',
  },
  title: { fontSize: 21, fontWeight: 700, marginBottom: 6, color: '#ece9f5' },
  subtitle: { fontSize: 13, color: '#9a96b3', marginBottom: 18 },
  qrWrap: {
    background: '#1c1c28',
    border: '2px solid #8B5CF6',
    borderRadius: 14,
    padding: 12,
    display: 'inline-block',
    marginBottom: 12,
    boxShadow: '0 0 18px rgba(139,92,246,0.15)',
  },
  qrFallback: { marginBottom: 12 },
  qrNote: { fontSize: 13, color: '#9a96b3', marginBottom: 10 },
  primaryBtn: {
    padding: '10px 28px',
    background: '#8B5CF6',
    border: 'none',
    color: '#fff',
    borderRadius: 10,
    fontSize: 14,
    fontWeight: 600,
    cursor: 'pointer',
  },
  popupRow: { marginBottom: 4 },
  ghostBtn: {
    padding: '8px 18px',
    background: 'transparent',
    border: '1px solid #8B5CF6',
    color: '#8B5CF6',
    borderRadius: 10,
    fontSize: 13,
    cursor: 'pointer',
  },
  hint: { fontSize: 12, color: '#6f6b88', marginTop: 12, lineHeight: 1.6 },
  link: { color: '#8B5CF6', textDecoration: 'none' },
  error: { fontSize: 12, color: '#ff6b6b', marginTop: 12 },
};
