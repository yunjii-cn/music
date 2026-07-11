/**
 * 云集智能音乐创意台 — 营销官网服务端
 *
 * 职责：
 *  1. 托管静态官网（public/）
 *  2. UM 扫码登录：/login/qr（生成二维码跳转）、/login/callback（换取用户信息）
 *  3. 登录态：/api/is-login、/logout
 *  4. 向浏览器暴露安全配置：/api/site-config（剔除 appkey）
 *
 * 复用视频站 vi.yunjii.cn 的 UM 对接协议（/um/connect.php）。
 */

const express = require('express');
const session = require('express-session');
const path = require('path');
const config = require('./config');

const app = express();
const PORT = config.server.port;

app.use(
  session({
    secret: process.env.SESSION_SECRET || 'yunji-music-site-2026',
    resave: false,
    saveUninitialized: false,
    cookie: { maxAge: 7 * 24 * 60 * 60 * 1000, secure: false },
  })
);

app.use(express.static(path.join(__dirname, 'public')));

/* ---------------------------------------------------------------
 * 向浏览器暴露配置（剔除服务端密钥 appkey）
 * ------------------------------------------------------------- */
app.get('/api/site-config', (req, res) => {
  const safe = JSON.parse(JSON.stringify(config));
  if (safe.um) delete safe.um.appkey;
  res.json(safe);
});

/* ---------------------------------------------------------------
 * UM 扫码登录 — 生成二维码跳转地址
 *  前端 iframe 加载 /login/qr → 服务端用 appkey 调 UM 拿到真实二维码URL → 302 跳转
 * ------------------------------------------------------------- */
app.get('/login/qr', async (req, res) => {
  try {
    const type = req.query.type || config.um.loginType;

    const umUrl =
      config.um.apiUrl.replace(/\/+$/, '') +
      '/um/connect.php?' +
      new URLSearchParams({
        id: 'web_qrcode_app_wrp',
        act: 'login',
        appid: config.um.appid,
        appkey: config.um.appkey,
        type,
        redirect_uri: config.um.callback,
        state: Math.random().toString(36).slice(2),
      }).toString();

    const resp = await fetch(umUrl);
    const data = await resp.json();

    if (data && data.code === 0 && data.url) {
      res.redirect(data.url);
    } else {
      res.status(500).send('获取登录二维码失败：' + (data && data.msg ? data.msg : '未知错误'));
    }
  } catch (e) {
    res.status(500).send('登录服务异常：' + e.message);
  }
});

/* ---------------------------------------------------------------
 * UM 回调 — 用 code 换取用户信息，写入 session，并通过 postMessage 通知父页面
 *  同时支持桌面端 ?from=client：登录后跳回客户端回传协议
 * ------------------------------------------------------------- */
app.get('/login/callback', async (req, res) => {
  try {
    const code = req.query.code;
    const fromClient = req.query.from === 'client';

    if (!code) {
      return res.status(400).send('缺少 code 参数');
    }

    const umUrl =
      config.um.apiUrl.replace(/\/+$/, '') +
      '/um/connect.php?' +
      new URLSearchParams({
        act: 'callback',
        appid: config.um.appid,
        appkey: config.um.appkey,
        code,
      }).toString();

    const resp = await fetch(umUrl);
    const data = await resp.json();

    if (data && data.code === 0) {
      // 写入 session（服务端登录态）
      req.session.user = {
        social_uid: data.social_uid,
        nickname: data.nickname,
        faceimg: data.faceimg,
        gender: data.gender || '',
        location: data.location || '',
      };

      const userJson = JSON.stringify(req.session.user);
      const script = `<!DOCTYPE html><html><head><meta charset="utf-8"><title>登录中</title></head><body>
        <script>
          var user = ${userJson};
          if (window.parent && window.parent !== window) {
            window.parent.postMessage({ type: 'loginSuccess', user: user }, '*');
            ${fromClient ? "window.parent.location.href = '/login/client?t=' + Date.now();" : ''}
          } else {
            window.location.href = '/?t=' + Date.now();
          }
        </script>
      </body></html>`;
      res.send(script);
    } else {
      const err = (data && data.msg) || '登录失败';
      res.send(`<!DOCTYPE html><html><head><meta charset="utf-8"></head><body><script>
        if (window.parent && window.parent !== window) {
          window.parent.postMessage({ type: 'loginError', error: ${JSON.stringify(err)} }, '*');
        } else {
          window.location.href = '/login?error=' + encodeURIComponent(${JSON.stringify(err)});
        }
      </script></body></html>`);
    }
  } catch (e) {
    res.status(500).send('回调处理异常：' + e.message);
  }
});

/* ---------------------------------------------------------------
 * 桌面端回传页（?from=client 时使用）
 *  实际项目可改为自定义协议 music://login?... 或 webview.postMessage
 * ------------------------------------------------------------- */
app.get('/login/client', (req, res) => {
  const user = req.session && req.session.user;
  const userJson = user ? JSON.stringify(user) : 'null';
  res.send(`<!DOCTYPE html><html><head><meta charset="utf-8"></head><body>
    <script>
      // 桌面端（WebView）可在此通过 postMessage 或自定义协议回传 token
      if (window.chrome && window.chrome.webview) {
        window.chrome.webview.postMessage({ type: 'loginSuccess', user: ${userJson} });
      }
      window.__LOGIN_DATA__ = ${userJson};
      window.location.href = 'music://login?user=' + encodeURIComponent(${userJson});
    </script>
  </body></html>`);
});

/* ---------------------------------------------------------------
 * 竞速下载 — 拉取两个 git 镜像的最新 Release，匹配各平台安装包
 *  返回 { version, published, assets: { windows/mac/linux: {github, gitee} } }
 *  前端据此自动选择最快镜像或提供手动选择
 * ------------------------------------------------------------- */
const downloadCache = { ts: 0, data: null };

function fetchJson(url, headers) {
  return new Promise((resolve) => {
    fetch(url, { headers: headers || {}, signal: AbortSignal.timeout(8000) })
      .then((r) => r.json())
      .then(resolve)
      .catch(() => resolve(null));
  });
}

function pickAsset(assets, re) {
  if (!Array.isArray(assets)) return null;
  for (const a of assets) {
    const name = a && (a.name || '');
    if (re.test(name)) {
      // GitHub / Gitee 字段名不同，统一取下载地址
      const url = a.browser_download_url || a.url || null;
      if (url) return url;
    }
  }
  return null;
}

app.get('/download/latest', async (req, res) => {
  const now = Date.now();
  if (downloadCache.data && now - downloadCache.ts < config.download.cacheTtl * 1000) {
    return res.json(downloadCache.data);
  }

  const m = config.download.mirrors;
  const pat = config.download.patterns;

  // GitHub（无 token 也能读 public release）
  const gh = await fetchJson(m.github.api, {
    Accept: 'application/vnd.github+json',
    'User-Agent': 'Yunji-Music-Web',
  });
  // Gitee
  const ge = await fetchJson(m.gitee.api, {
    'User-Agent': 'Yunji-Music-Web',
  });

  const assets = { windows: {}, mac: {}, linux: {} };
  function fill(src, mirrorKey) {
    if (!src) return;
    const list = src.assets || [];
    const version = src.tag_name || src.name || src.tag || '';
    for (const plat of ['windows', 'mac', 'linux']) {
      const u = pickAsset(list, pat[plat]);
      if (u) assets[plat][mirrorKey] = u;
      // 记录版本（取第一个成功的）
      if (version && !downloadCache.data) {
        // 占位，下面统一写
      }
    }
    return version;
  }
  const vGh = fill(gh, 'github');
  const vGe = fill(ge, 'gitee');

  const version = (gh && (gh.tag_name || gh.name)) || (ge && (ge.tag_name || ge.name)) || '';
  const published =
    (gh && (gh.published_at || gh.created_at)) ||
    (ge && (ge.created_at || ge.updated_at)) ||
    '';

  const data = { version, published, assets };
  downloadCache.data = data;
  downloadCache.ts = now;
  res.json(data);
});

/* ---------------------------------------------------------------
 * 登录态查询（页面刷新后保持登录）
 * ------------------------------------------------------------- */
app.get('/api/is-login', (req, res) => {
  if (req.session && req.session.user) {
    res.json({ code: 1, data: req.session.user });
  } else {
    res.json({ code: 0, data: null });
  }
});

/* ---------------------------------------------------------------
 * 退出登录
 * ------------------------------------------------------------- */
app.get('/logout', (req, res) => {
  if (req.session) req.session.destroy(() => {});
  res.redirect('/');
});

app.listen(PORT, () => {
  console.log(`[营销官网] 运行于 http://localhost:${PORT}`);
  console.log(`[UM] apiUrl=${config.um.apiUrl} appid=${config.um.appid} callback=${config.um.callback}`);
});
