<?php
/**
 * 云集智能音乐创意台 - 用户资料页（统一网关 dogfooding）
 *
 * 落地「数据在 UM，UI 在各应用」：
 *   - 服务端用 $_SESSION['user']['token']（UM 用户 JWT）以 Bearer 调用 api.yunjii.cn/user/profile
 *   - GET 读取全量资料渲染，PATCH 部分更新（昵称/用户名/性别/所在地/手机/邮箱）
 *   - 前端用本站紫色品牌色渲染同一份 UM 数据，token 不出服务端、不跨域
 *
 * 与 UM 官网 next/app/api/user/profile 同源：官网走 Next 代理，本站是纯 PHP 服务端直调，
 * 但都消费同一个 api.yunjii.cn/user/profile 能力域，证明该能力可被任意应用复用。
 */

session_start();
require_once __DIR__ . '/config.php';

// ===== 登录门控：缺 user 或 token → 回登录页 =====
if (empty($_SESSION['user']) || empty($_SESSION['user']['token'])) {
    header('Location: ./index.php', true, 302);
    exit;
}
$token = $_SESSION['user']['token'];

/**
 * 以 Bearer 调用统一网关 /user/profile
 * @return array [httpCode, json, curlError]
 */
function mi_call_gateway($method, $token, $body = null)
{
    $ch = curl_init(MI_API_PROFILE_URL);
    $headers = [
        'Authorization: Bearer ' . $token,
        'Content-Type: application/json',
        'Host: ' . MI_API_PROFILE_HOST,
    ];
    $opts = [
        CURLOPT_CUSTOMREQUEST    => $method,
        CURLOPT_HTTPHEADER       => $headers,
        CURLOPT_RETURNTRANSFER   => true,
        CURLOPT_TIMEOUT          => 10,
        CURLOPT_SSL_VERIFYPEER   => false,
        CURLOPT_SSL_VERIFYHOST   => false,
    ];
    if ($body !== null) {
        $opts[CURLOPT_POSTFIELDS] = json_encode($body, JSON_UNESCAPED_UNICODE);
    }
    curl_setopt_array($ch, $opts);
    $resp    = curl_exec($ch);
    $http    = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $curlErr = curl_error($ch);
    // PHP 8.5 起 curl_close() 已弃用（PHP 8.0 后无实际作用），省略即可
    $json = json_decode($resp, true);
    return [$http, $json, $curlErr];
}

$msg = '';
$msgType = '';

// ===== 保存（PATCH）=====
if ($_SERVER['REQUEST_METHOD'] === 'POST') {
    $patch = [];
    foreach (['nickname', 'username', 'gender', 'location', 'country', 'province', 'city', 'language', 'phone', 'email'] as $f) {
        if (isset($_POST[$f])) {
            $patch[$f] = trim($_POST[$f]);
        }
    }
    [$http, $r, $curlErr] = mi_call_gateway('PATCH', $token, $patch);
    if ($curlErr) {
        $msg = '网络错误：' . $curlErr;
        $msgType = 'err';
    } elseif ($http === 200 && isset($r['code']) && $r['code'] === 0) {
        $msg = $r['msg'] ?? '资料已更新';
        $msgType = 'ok';
        // 同步回本站 session（昵称/用户名），其余字段下次 GET 自然刷新
        if (!empty($r['data'])) {
            $_SESSION['user']['nickname'] = $r['data']['nickname'] ?? ($_SESSION['user']['nickname'] ?? '');
            $_SESSION['user']['username'] = $r['data']['username'] ?? ($_SESSION['user']['username'] ?? '');
        }
    } else {
        $msg = ($r['msg'] ?? '保存失败') . (isset($r['errcode']) ? '（code ' . $r['errcode'] . '）' : '');
        $msgType = 'err';
    }
}

// ===== 读取（GET）=====
[$http, $profile, $curlErr] = mi_call_gateway('GET', $token);
$data = [];
if ($curlErr) {
    $msg = $msg ?: ('网络错误：' . $curlErr);
    $msgType = $msgType ?: 'err';
} elseif ($http === 200 && isset($profile['code']) && $profile['code'] === 0 && !empty($profile['data'])) {
    $data = $profile['data'];
} else {
    // token 失效 / 用户不存在 → 提示重新登录（不强制跳转，展示错误 + 链接）
    $msg = $msg ?: ($profile['msg'] ?? '获取资料失败，请重新登录');
    $msgType = $msgType ?: 'err';
}

$genderOptions = ['', '男', '女', '未知'];

function mi_v($k, $default = '')
{
    global $data;
    $v = $data[$k] ?? '';
    return htmlspecialchars($v !== '' ? $v : $default, ENT_QUOTES, 'UTF-8');
}
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>我的资料 - 云集智能音乐创意台</title>
    <link rel="shortcut icon" href="../favicon.ico">
    <link rel="stylesheet" href="../css/style.css">
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
        * { margin:0; padding:0; box-sizing:border-box; }
        html, body { min-height: 100%; }
        body {
            background: var(--bg);
            color: var(--text);
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Hiragino Sans GB', 'Microsoft YaHei', sans-serif;
            display: flex; justify-content: center; align-items: flex-start;
            min-height: 100vh; padding: 88px 16px 48px; position: relative; overflow-x: hidden;
        }
        body::before {
            content: ""; position: absolute; width: 620px; height: 620px;
            background: radial-gradient(circle, var(--violet-glow) 0%, transparent 70%);
            top: -120px; right: -120px; filter: blur(60px); opacity: 0.4; z-index: 0;
        }
        .wrap { position: relative; z-index: 1; width: 100%; max-width: 780px; }
        .back-home {
            display: inline-flex; align-items: center; gap: 4px; font-size: 13px;
            color: var(--muted); text-decoration: none; margin-bottom: 18px; transition: color .2s;
        }
        .back-home:hover { color: var(--violet); }
        .card {
            background: var(--card); border: 1px solid var(--card-border); border-radius: 20px;
            padding: 32px; box-shadow: 0 20px 60px rgba(0,0,0,0.55), 0 0 0 1px var(--violet-soft) inset;
        }
        .head { display: flex; align-items: center; gap: 16px; margin-bottom: 24px; }
        .avatar {
            width: 64px; height: 64px; border-radius: 50%; border: 2px solid var(--violet);
            object-fit: cover; box-shadow: 0 0 18px var(--violet-glow); background: #1c1c28;
        }
        .head h1 { font-size: 20px; font-weight: 700; }
        .head .sub { font-size: 12px; color: var(--muted); margin-top: 4px; }
        .msg {
            border-radius: 10px; padding: 10px 14px; margin-bottom: 18px; font-size: 13px; line-height: 1.5;
        }
        .msg.ok { background: rgba(34,197,94,0.12); border: 1px solid rgba(34,197,94,0.3); color: #4ade80; }
        .msg.err { background: rgba(239,68,68,0.12); border: 1px solid rgba(239,68,68,0.3); color: #f87171; }
        form.pf-grid {
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 14px;
        }
        .field label { display: block; font-size: 13px; color: var(--muted); margin-bottom: 6px; }
        .field input, .field select {
            width: 100%; padding: 11px 14px; border-radius: 10px; font-size: 14px; font-family: inherit;
            background: #1c1c28; border: 1px solid var(--card-border); color: var(--text); transition: border-color .2s;
        }
        .field input:focus, .field select:focus { outline: none; border-color: var(--violet); }
        .readonly {
            background: #14141c !important; color: var(--muted) !important;
            border-style: dashed !important; cursor: not-allowed;
        }
        .full { grid-column: 1 / -1; }
        .section-title {
            font-size: 12px; color: var(--muted); letter-spacing: .5px;
            padding-top: 8px; border-top: 1px solid var(--card-border);
            grid-column: 1 / -1; margin: 0;
        }
        .actions { display: flex; gap: 12px; margin-top: 4px; grid-column: 1 / -1; }
        .btn {
            display: inline-flex; align-items: center; justify-content: center;
            flex: 1; padding: 12px 0; border-radius: 12px; font-size: 14px; font-weight: 600;
            cursor: pointer; text-decoration: none; font-family: inherit; transition: all .2s;
        }
        .btn-primary { background: var(--violet); border: 1px solid var(--violet); color: #fff; }
        .btn-primary:hover { background: var(--violet-hover); box-shadow: 0 6px 20px var(--violet-glow); }
        .btn-ghost { background: transparent; border: 1px solid var(--violet); color: var(--violet); }
        .btn-ghost:hover { background: var(--violet); color: #fff; }
        .hint { font-size: 11px; color: #6f6b88; margin-top: 16px; line-height: 1.6; text-align: center; grid-column: 1 / -1; }
        .hint a { color: var(--violet); text-decoration: none; }
        @media (max-width: 640px) {
            .card { padding: 24px 16px; }
            form.pf-grid { grid-template-columns: 1fr; gap: 12px; }
        }
    </style>
</head>
<body>
    <!-- 顶栏（与首页一致） -->
    <nav class="navbar" id="navbar">
        <div class="nav-container">
            <a href="../index.html" class="nav-brand">
                <img src="../favicon.ico" alt="云集" class="nav-logo">
                <span class="nav-title">云集智能音乐创意台</span>
            </a>
            <div class="nav-links" id="navLinks">
                <a href="../index.html#features" class="nav-link">核心功能</a>
                <a href="../index.html#advantages" class="nav-link">为什么选云集</a>
                <a href="../index.html#showcase" class="nav-link">产品展示</a>
                <a href="../index.html#tech" class="nav-link">技术架构</a>
                <a href="../index.html#roadmap" class="nav-link">发展路线</a>
                <a href="https://github.com/sdbds/ACE-Step-1.5-for-windows" target="_blank" rel="noopener" class="nav-link">GitHub</a>
                <a href="../index.html#download" class="nav-link">免费下载</a>
            </div>
            <a href="/login" data-login-link class="nav-login">
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M20 21v-2a4 4 0 00-4-4H8a4 4 0 00-4 4v2M12 11a4 4 0 100-8 4 4 0 000 8z"/></svg>
                登录
            </a>
            <button class="nav-toggle" id="navToggle" aria-label="菜单">
                <span></span><span></span><span></span>
            </button>
        </div>
    </nav>

    <div class="wrap">
        <div class="card">
            <div class="head">
                <img class="avatar" src="<?php echo mi_v('avatar', '../favicon.ico'); ?>" alt="头像">
                <div>
                    <h1>我的资料</h1>
                    <div class="sub">由云集统一用户中心（UM）托管 · 多站通用</div>
                </div>
            </div>

            <?php if ($msg): ?>
            <div class="msg <?php echo $msgType === 'ok' ? 'ok' : 'err'; ?>"><?php echo htmlspecialchars($msg, ENT_QUOTES, 'UTF-8'); ?></div>
            <?php endif; ?>

            <form method="POST" action="./profile.php" class="pf-grid">
                <div class="field">
                    <label>昵称</label>
                    <input type="text" name="nickname" maxlength="50" value="<?php echo mi_v('nickname'); ?>" placeholder="未设置">
                </div>

                <div class="field">
                    <label>用户名</label>
                    <input type="text" name="username" maxlength="32" value="<?php echo mi_v('username'); ?>" placeholder="未设置">
                </div>

                <div class="field">
                    <label>性别</label>
                    <select name="gender">
                        <?php foreach ($genderOptions as $g): ?>
                        <option value="<?php echo htmlspecialchars($g, ENT_QUOTES, 'UTF-8'); ?>"<?php echo (($data['gender'] ?? '') === $g) ? ' selected' : ''; ?>><?php echo $g === '' ? '未设置' : htmlspecialchars($g, ENT_QUOTES, 'UTF-8'); ?></option>
                        <?php endforeach; ?>
                    </select>
                </div>

                <div class="field">
                    <label>所在地</label>
                    <input type="text" name="location" maxlength="100" value="<?php echo mi_v('location'); ?>" placeholder="如：浙江杭州">
                </div>

                <div class="field">
                    <label>手机号</label>
                    <input type="text" name="phone" maxlength="11" value="<?php echo mi_v('phone'); ?>" placeholder="11 位手机号">
                </div>
                <div class="field">
                    <label>邮箱</label>
                    <input type="text" name="email" maxlength="128" value="<?php echo mi_v('email'); ?>" placeholder="name@example.com">
                </div>

                <div class="section-title">更多资料（来自微信等平台，自动补全可改）</div>
                <div class="field">
                    <label>国家</label>
                    <input type="text" name="country" maxlength="64" value="<?php echo mi_v('country'); ?>" placeholder="如：中国">
                </div>
                <div class="field">
                    <label>省份</label>
                    <input type="text" name="province" maxlength="64" value="<?php echo mi_v('province'); ?>" placeholder="如：浙江">
                </div>
                <div class="field">
                    <label>城市</label>
                    <input type="text" name="city" maxlength="64" value="<?php echo mi_v('city'); ?>" placeholder="如：杭州">
                </div>
                <div class="field">
                    <label>语言</label>
                    <input type="text" name="language" maxlength="32" value="<?php echo mi_v('language'); ?>" placeholder="如：zh_CN">
                </div>

                <div class="section-title">账户信息（只读）</div>
                <div class="field full">
                    <label>微信 UnionID（多平台归一标识）</label>
                    <input type="text" class="readonly" value="<?php echo mi_v('unionid'); ?>" readonly>
                </div>
                <div class="field">
                    <label>用户 ID</label>
                    <input type="text" class="readonly" value="<?php echo mi_v('user_id'); ?>" readonly>
                </div>
                <div class="field">
                    <label>积分</label>
                    <input type="text" class="readonly" value="<?php echo mi_v('score'); ?>" readonly>
                </div>
                <div class="field">
                    <label>余额</label>
                    <input type="text" class="readonly" value="<?php echo mi_v('balance'); ?>" readonly>
                </div>
                <div class="field">
                    <label>注册时间</label>
                    <input type="text" class="readonly" value="<?php echo mi_v('created_at'); ?>" readonly>
                </div>

                <div class="actions">
                    <button type="submit" class="btn btn-primary">保存修改</button>
                    <a href="/um/logout.php?redirect=/profile" class="btn btn-ghost">退出登录</a>
                </div>

                <div class="hint">修改将同步至云集账号体系，在 <a href="https://um.yunjii.cn/zh/user/profile" target="_blank" rel="noopener">UM 官网</a> 及其他接入应用即时生效。</div>
            </form>
        </div>
    </div>

    <!-- 顶栏交互：滚动阴影 / 移动端折叠 / 登录态切换为头像菜单 -->
    <script>
    (function () {
        var nav = document.getElementById('navbar');
        if (nav) {
            window.addEventListener('scroll', function () {
                nav.classList.toggle('scrolled', window.scrollY > 20);
            });
        }
        var tgl = document.getElementById('navToggle');
        var links = document.getElementById('navLinks');
        if (tgl && links) {
            tgl.addEventListener('click', function () { links.classList.toggle('open'); });
        }

        var link = document.querySelector('[data-login-link]');
        if (!link) return;
        fetch('../um/islogin.php', { credentials: 'same-origin' })
            .then(function (r) { return r.json(); })
            .then(function (res) { if (res && res.code === 1 && res.data) renderUser(res.data); })
            .catch(function () {});

        function escapeHtml(s) {
            return String(s == null ? '' : s).replace(/[&<>"]/g, function (c) {
                return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
            });
        }
        function renderUser(u) {
            var nick = u.nickname || '云集用户';
            var avatar = u.avatar || '../favicon.ico';
            var wrap = document.createElement('div');
            wrap.className = 'nav-user-wrap';
            wrap.innerHTML =
                '<button type="button" class="nav-user-btn">' +
                '<img src="' + escapeHtml(avatar) + '" alt="">' +
                '<span>' + escapeHtml(nick) + '</span>' +
                '<svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M6 9l6 6 6-6"/></svg>' +
                '</button>' +
                '<div class="nav-user-menu">' +
                '<a href="/profile">个人资料</a>' +
                '<a href="/um/logout.php?redirect=' + encodeURIComponent(location.href) + '" class="danger">退出登录</a>' +
                '</div>';
            link.parentNode.replaceChild(wrap, link);
            var btn = wrap.querySelector('.nav-user-btn');
            var menu = wrap.querySelector('.nav-user-menu');
            btn.addEventListener('click', function (e) { e.stopPropagation(); menu.style.display = menu.style.display === 'none' ? 'block' : 'none'; });
            document.addEventListener('click', function () { menu.style.display = 'none'; });
        }
    })();
    </script>
</body>
</html>
