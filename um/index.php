<?php
/**
 * 云集智能音乐创意台 - 登录页面（PHP 服务端渲染版）
 *
 * 与 login.html 功能等价，双登录方式 + 软件门控深链。
 * 当用户直接访问 /um/ 时展示此页面（PHP 处理）。
 */

session_start();
header('Content-Type: text/html; charset=UTF-8');

include_once __DIR__ . '/config.php';

$isLoggedIn = isset($_SESSION['user']);
$user = $isLoggedIn ? $_SESSION['user'] : null;

// 门控 / 回跳参数解析
$gate     = $_GET['gate'] ?? '';
$app      = $_GET['app'] ?? '';
$redirect = $_GET['redirect'] ?? '';
$error    = $_GET['error'] ?? '';

$isGate = !empty($gate) || (!empty($redirect) && !str_contains($redirect, $_SERVER['HTTP_HOST']));
if (empty($redirect) && !empty($_SERVER['HTTP_REFERER'])) {
    $refHost = parse_url($_SERVER['HTTP_REFERER'], PHP_URL_HOST);
    if ($refHost === $_SERVER['HTTP_HOST'] && !str_ends_with($_SERVER['HTTP_REFERER'], '/login.html')) {
        $redirect = $_SERVER['HTTP_REFERER'];
    }
}
if (empty($redirect)) $redirect = '../index.html';

// 门控深链：构建带有用户信息的跳转 URL
function buildGateUrl($user, $target, $gate)
{
    if (!$gate || !$target) return $target;
    $payload = [
        'nickname' => $user['nickname'] ?? '',
        'avatar'   => $user['faceimg'] ?? '',
        'openid'   => $user['social_uid'] ?? '',
        'username' => $user['username'] ?? '',
        'token'    => $user['token'] ?? '',
    ];
    $b64 = base64_encode(json_encode($payload, JSON_UNESCAPED_UNICODE));
    $sep = str_contains($target, '?') ? '&' : '?';
    return $target . $sep . 'yunji_user=' . urlencode($b64);
}

// OAuth 回调返回（?code=...&state=...）→ 转发给 oauth_callback.php 处理
if (!empty($_GET['code'])) {
    $cbUrl = './oauth_callback.php?' . $_SERVER['QUERY_STRING'];
    header("Location: $cbUrl", true, 302);
    exit;
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>登录 - 云集智能音乐创意台</title>
    <link rel="shortcut icon" href="../favicon.ico">
    <style>
        :root {
            --violet: #8B5CF6;
            --violet-hover: #7c4df0;
            --violet-soft: rgba(139, 92, 246, 0.15);
            --violet-glow: rgba(139, 92, 246, 0.45);
            --bg: #0a0a0f;
            --card: #14141c;
            --card-border: #26263a;
            --text: #ece9f5;
            --muted: #9a96b3;
        }
        * { margin: 0; padding: 0; box-sizing: border-box; }
        html, body { height: 100%; }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: "Microsoft YaHei", -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
            display: flex;
            justify-content: center;
            align-items: center;
            min-height: 100vh;
            position: relative;
            overflow: hidden;
        }
        body::before {
            content: "";
            position: absolute;
            width: 620px; height: 620px;
            background: radial-gradient(circle, var(--violet-glow) 0%, transparent 70%);
            top: 50%; left: 50%;
            transform: translate(-50%, -50%);
            filter: blur(40px);
            opacity: 0.5;
            z-index: 0;
        }
        .login-card {
            position: relative;
            z-index: 1;
            background: var(--card);
            border: 1px solid var(--card-border);
            border-radius: 20px;
            padding: 40px 36px 36px;
            width: 380px;
            max-width: calc(100vw - 32px);
            text-align: center;
            box-shadow: 0 20px 60px rgba(0,0,0,0.55), 0 0 0 1px var(--violet-soft) inset;
        }
        .login-logo {
            width: 56px; height: 56px;
            border-radius: 14px;
            margin: 0 auto 18px;
            display: block;
            box-shadow: 0 0 24px var(--violet-glow);
        }
        .login-title { font-size: 21px; font-weight: 700; margin-bottom: 6px; letter-spacing: 0.5px; }
        .login-title .accent { color: var(--violet); }
        .login-subtitle { font-size: 13px; color: var(--muted); margin-bottom: 22px; }

        .tabs {
            display: flex; gap: 0; margin-bottom: 22px;
            background: #1c1c28; border-radius: 10px; padding: 4px;
        }
        .tab {
            flex: 1; padding: 8px 0; font-size: 13px; border: none;
            border-radius: 8px; cursor: pointer; background: transparent;
            color: var(--muted); font-family: inherit; transition: all 0.2s;
        }
        .tab.active { background: var(--violet-soft); color: #fff; font-weight: 600; }
        .tab-panel { display: none; }
        .tab-panel.active { display: block; }
        .qrcode-wrap {
            background: #1c1c28; border: 2px solid var(--violet); border-radius: 14px;
            padding: 14px; display: inline-block; margin-bottom: 16px;
            box-shadow: 0 0 18px var(--violet-soft); position: relative; line-height: 0;
        }
        .qrcode-wrap iframe {
            border: none; display: block; border-radius: 6px;
            background: #fff; width: 200px; height: 200px;
        }
        .qrcode-loading {
            position: absolute; inset: 14px; display: flex; align-items: center;
            justify-content: center; font-size: 12px; color: var(--muted);
            background: #1c1c28; border-radius: 6px;
        }
        .oauth-buttons {
            display: flex; flex-direction: column; gap: 12px; margin-bottom: 16px;
        }
        .btn-oauth {
            display: flex; align-items: center; justify-content: center; gap: 10px;
            width: 100%; padding: 14px 20px; border-radius: 14px; font-size: 15px;
            font-weight: 600; cursor: pointer; border: 1px solid var(--card-border);
            background: #1c1c28; color: var(--text); font-family: inherit;
            transition: all 0.2s; text-decoration: none;
        }
        .btn-oauth:hover { border-color: var(--violet); background: var(--violet-soft); }
        .btn-oauth svg { width: 20px; height: 20px; flex-shrink: 0; }
        .oauth-hint { font-size: 12px; color: var(--muted); line-height: 1.6; }
        .qr-tip { font-size: 12px; color: #6f6b88; margin-top: 8px; line-height: 1.6; }
        .qr-tip a { color: var(--violet); text-decoration: none; }

        .user-card { text-align: center; }
        .user-avatar {
            width: 72px; height: 72px; border-radius: 50%; border: 2px solid var(--violet);
            object-fit: cover; margin-bottom: 14px; box-shadow: 0 0 20px var(--violet-glow);
        }
        .user-nickname { font-size: 19px; font-weight: 700; margin-bottom: 4px; word-break: break-all; }
        .user-id { font-size: 12px; color: var(--muted); margin-bottom: 24px; }
        .btn-primary {
            display: inline-block; padding: 10px 28px; background: var(--violet);
            border: none; color: #fff; border-radius: 10px; font-size: 14px; font-weight: 600;
            cursor: pointer; text-decoration: none; transition: all 0.2s; margin: 0 6px;
        }
        .btn-primary:hover { background: var(--violet-hover); box-shadow: 0 6px 20px var(--violet-glow); }
        .btn-logout {
            display: inline-block; padding: 10px 28px; background: transparent;
            border: 1px solid var(--violet); color: var(--violet); border-radius: 10px;
            font-size: 14px; cursor: pointer; text-decoration: none; transition: all 0.2s; margin: 0 6px;
        }
        .btn-logout:hover { background: var(--violet); color: #fff; }
        .redirect-hint { font-size: 12px; color: var(--muted); margin-bottom: 18px; line-height: 1.5; word-break: break-all; }
        .redirect-hint b { color: var(--violet); font-weight: 600; }
        .gate-banner {
            background: var(--violet-soft); border: 1px solid rgba(139,92,246,0.35);
            border-radius: 10px; padding: 10px 14px; margin-bottom: 20px;
            font-size: 12px; color: var(--violet); text-align: left; line-height: 1.5;
        }
        .gate-banner b { color: #fff; }
        .login-error {
            background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3);
            border-radius: 10px; padding: 10px 14px; margin-bottom: 18px;
            font-size: 12px; color: #f87171; display: none;
        }
        .login-error.show { display: block; }
        .back-home {
            position: absolute; top: 18px; left: 20px; font-size: 13px; color: var(--muted);
            text-decoration: none; display: inline-flex; align-items: center; gap: 4px;
            transition: color 0.2s; z-index: 2;
        }
        .back-home:hover { color: var(--violet); }
        .hidden { display: none !important; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(4px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body>
    <a href="../index.html" class="back-home">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        返回首页
    </a>

    <div class="login-card">
        <?php if ($error): ?>
        <div class="login-error show"><?php echo htmlspecialchars($error); ?></div>
        <?php endif; ?>

        <?php if ($isGate): ?>
        <div class="gate-banner">
            <b>正在登录「<?php echo htmlspecialchars($app ?: '应用程序'); ?>」</b><br>
            登录后自动返回应用，请使用云集账号授权
        </div>
        <?php endif; ?>

        <?php if ($isLoggedIn): ?>
            <!-- ===== 已登录 ===== -->
            <?php $gateUrl = buildGateUrl($user, $redirect, $isGate); ?>
            <div class="user-card">
                <img class="user-avatar" src="<?php echo htmlspecialchars($user['faceimg'] ?? '../favicon.ico'); ?>" alt="头像">
                <div class="user-nickname"><?php echo htmlspecialchars($user['nickname'] ?? '云集用户'); ?></div>
                <div class="user-id">ID: <?php echo htmlspecialchars($user['social_uid'] ?? '-'); ?></div>
                <?php if ($redirect && $redirect !== '../index.html'): ?>
                <div class="redirect-hint">登录后将<?php echo $isGate ? '自动启动应用' : '返回'; ?>：<b><?php echo htmlspecialchars($redirect); ?></b></div>
                <?php endif; ?>
                <a href="<?php echo htmlspecialchars($gateUrl); ?>" class="btn-primary">
                    <?php echo $isGate ? '启动应用' : '进入工作台'; ?>
                </a>
                <a href="./profile.php" class="btn-logout">编辑资料</a>
                <a href="./logout.php" class="btn-logout">退出登录</a>
            </div>
            <?php if ($isGate): ?>
            <script>setTimeout(function(){ window.location.href = <?php echo json_encode($gateUrl); ?>; }, 1500);</script>
            <?php endif; ?>
        <?php else: ?>
            <!-- ===== 未登录 ===== -->
            <img src="../favicon.ico" alt="云集" class="login-logo">
            <div class="login-title">登录 <span class="accent">云集智能音乐创意台</span></div>
            <div class="login-subtitle"><?php echo $isGate ? '请登录以继续使用应用程序' : '登录后可同步创作数据，解锁更多功能'; ?></div>

            <div class="tabs" id="tabs">
                <button class="tab active" data-tab="qr">微信扫码</button>
                <button class="tab" data-tab="oauth">账号登录</button>
            </div>

            <!-- 扫码 Tab -->
            <div class="tab-panel active" id="panelQr">
                <div class="qrcode-wrap">
                    <div class="qrcode-loading" id="qrLoading">二维码生成中…</div>
                    <iframe id="qrFrame" src="./connect.php?type=wx" width="200" height="200" frameborder="0" scrolling="no"></iframe>
                </div>
                <div class="qr-tip">微信扫一扫，安全快捷登录</div>
            </div>

            <!-- OAuth Tab -->
            <div class="tab-panel" id="panelOauth">
                <div class="oauth-buttons">
                    <a class="btn-oauth" id="btnWechat" href="javascript:;">
                        <svg viewBox="0 0 24 24" fill="currentColor"><path d="M8.691 2.188C3.891 2.188 0 5.476 0 9.53c0 2.212 1.17 4.203 3.002 5.55a.59.59 0 01.213.665l-.39 1.48c-.019.07-.048.141-.048.213 0 .163.13.295.29.295a.326.326 0 00.167-.054l1.903-1.114a.864.864 0 01.717-.098 10.16 10.16 0 002.837.403c.276 0 .543-.027.811-.05-.857-2.578.157-4.972 1.932-6.446 1.703-1.415 3.882-1.98 5.853-1.838-.576-3.583-4.196-6.348-8.596-6.348zM5.785 5.991c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178A1.17 1.17 0 014.623 7.17c0-.651.52-1.18 1.162-1.18zm5.813 0c.642 0 1.162.529 1.162 1.18a1.17 1.17 0 01-1.162 1.178 1.17 1.17 0 01-1.162-1.178c0-.651.52-1.18 1.162-1.18zm5.171 2.671c-3.44 0-6.228 2.236-6.228 5.005 0 2.769 2.788 5.005 6.228 5.005.972 0 1.896-.195 2.757-.534a.646.646 0 01.558.076l1.483.868a.255.255 0 00.13.042.23.23 0 00.225-.23c0-.056-.022-.112-.038-.166l-.304-1.154a.462.462 0 01.166-.518C23.02 18.205 24 16.912 24 15.35c0-2.564-2.391-4.688-5.231-4.688zm-2.017 2.408c.497 0 .9.413.9.92 0 .508-.403.92-.9.92a.909.909 0 01-.9-.92c0-.507.403-.92.9-.92zm4.034 0c.497 0 .9.413.9.92 0 .508-.403.92-.9.92a.909.909 0 01-.9-.92c0-.507.403-.92.9-.92z"/></svg>
                        微信快捷登录
                    </a>
                    <a class="btn-oauth" id="btnPassword" href="javascript:;">
                        <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0110 0v4"/><circle cx="12" cy="16" r="1"/></svg>
                        密码登录
                    </a>
                </div>
                <div class="oauth-hint">通过云集统一用户中心安全授权</div>
            </div>

            <div class="qr-tip">扫码即代表同意 <a href="#">用户协议</a> 和 <a href="#">隐私政策</a></div>
        <?php endif; ?>
    </div>

    <script>
    (function() {
        var UM_AUTHORIZE = 'https://um.yunjii.cn/oauth/authorize.php';
        var CLIENT_ID = '1016';
        var CALLBACK  = 'https://music.yunjii.cn/um/oauth_callback.php';
        var GATE = <?php echo json_encode($isGate ? '1' : ''); ?>;
        var APP  = <?php echo json_encode($app); ?>;
        var RD   = <?php echo json_encode($redirect !== '../index.html' ? $redirect : ''); ?>;

        // Tab 切换
        document.querySelectorAll('.tab').forEach(function(t) {
            t.addEventListener('click', function() {
                document.querySelectorAll('.tab').forEach(function(x) { x.classList.remove('active'); });
                t.classList.add('active');
                var id = t.getAttribute('data-tab');
                document.getElementById('panelQr').classList.toggle('active', id==='qr');
                document.getElementById('panelOauth').classList.toggle('active', id==='oauth');
            });
        });

        // iframe 加载完成
        var qrFrame = document.getElementById('qrFrame');
        if (qrFrame) {
            qrFrame.addEventListener('load', function() {
                var l = document.getElementById('qrLoading');
                if (l) l.style.display = 'none';
            });
        }

        // 扫码成功消息
        window.addEventListener('message', function(e) {
            if (e.data && e.data.type === 'loginSuccess') {
                window.location.reload();
            }
        });

        // PKCE + OAuth 登录
        function generatePKCE() {
            var chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~';
            var v = '';
            var c = window.crypto || window.msCrypto;
            if (c && c.getRandomValues) {
                var b = new Uint8Array(32); c.getRandomValues(b);
                for (var i=0; i<b.length; i++) v += chars.charAt(b[i] % chars.length);
            } else {
                for (var i=0; i<43; i++) v += chars.charAt(Math.floor(Math.random() * chars.length));
            }
            function b64url(buf) {
                var s = btoa(String.fromCharCode.apply(null, new Uint8Array(buf)));
                return s.replace(/\+/g,'-').replace(/\//g,'_').replace(/=+$/,'');
            }
            if (c && c.subtle) {
                return c.subtle.digest('SHA-256', new TextEncoder().encode(v)).then(function(h) {
                    return { verifier: v, challenge: b64url(h) };
                });
            }
            return Promise.resolve({ verifier: v, challenge: v });
        }
        function startOAuth(mode) {
            generatePKCE().then(function(pk) {
                fetch('./islogin.php?set_verifier=' + encodeURIComponent(pk.verifier), { credentials:'same-origin' }).catch(function(){});
                var st = 'oauth_' + Date.now();
                var extra = [];
                if (RD) extra.push('r='+encodeURIComponent(RD));
                if (GATE) extra.push('g='+GATE);
                if (APP) extra.push('a='+encodeURIComponent(APP));
                if (extra.length) st += '|' + extra.join('&');
                var q = [
                    'response_type=code',
                    'client_id='+encodeURIComponent(CLIENT_ID),
                    'redirect_uri='+encodeURIComponent(CALLBACK),
                    'code_challenge='+encodeURIComponent(pk.challenge),
                    'code_challenge_method=S256',
                    'state='+encodeURIComponent(st)
                ];
                if (mode==='wechat') q.push('login_tab=wechat');
                window.location.href = UM_AUTHORIZE + '?' + q.join('&');
            });
        }
        var bw = document.getElementById('btnWechat');
        if (bw) bw.addEventListener('click', function(e){ e.preventDefault(); startOAuth('wechat'); });
        var bp = document.getElementById('btnPassword');
        if (bp) bp.addEventListener('click', function(e){ e.preventDefault(); startOAuth('password'); });
    })();
    </script>
</body>
</html>
