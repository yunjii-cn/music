<?php
/**
 * 云集智能音乐创意台 - 登录页面（音乐紫主题）
 * 参考：云集智能视频创意站 web/sl/index.php
 *
 * 未登录：iframe 加载 ./connect.php?type=wx 显示微信扫码二维码
 * 已登录：显示头像 / 昵称 / ID，并提供进入工作台 / 退出登录
 */
session_start();
header('Content-Type: text/html; charset=UTF-8');

include_once __DIR__ . '/config.php';

$is_logged_in = isset($_SESSION['user']);
$user = $is_logged_in ? $_SESSION['user'] : null;

// 工作台深链（可选）
if (defined('MI_APP_URL') && MI_APP_URL) {
    $payload = [
        'nickname' => $user['nickname'] ?? '',
        'avatar'   => $user['faceimg'] ?? '',
        'openid'   => $user['social_uid'] ?? '',
    ];
    $b64     = base64_encode(json_encode($payload, JSON_UNESCAPED_UNICODE));
    $appHref = MI_APP_URL . '?yunji_user=' . urlencode($b64);
    $appLabel = '🚀 进入工作台';
} else {
    $appHref  = '../index.html';
    $appLabel = '返回首页';
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
        /* 背景光晕 */
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
            padding: 44px 36px 36px;
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
        .login-title {
            font-size: 21px;
            font-weight: 700;
            margin-bottom: 6px;
            letter-spacing: 0.5px;
        }
        .login-title .accent { color: var(--violet); }
        .login-subtitle {
            font-size: 13px;
            color: var(--muted);
            margin-bottom: 26px;
        }
        .qrcode-wrap {
            background: #1c1c28;
            border: 2px solid var(--violet);
            border-radius: 14px;
            padding: 14px;
            display: inline-block;
            margin-bottom: 20px;
            box-shadow: 0 0 18px var(--violet-soft);
        }
        .qrcode-wrap iframe {
            border: none;
            display: block;
            border-radius: 6px;
        }
        .login-hint {
            font-size: 12px;
            color: #6f6b88;
            margin-top: 14px;
            line-height: 1.6;
        }
        .login-hint a { color: var(--violet); text-decoration: none; }
        .login-hint a:hover { text-decoration: underline; }
        .back-home {
            position: absolute;
            top: 18px; left: 20px;
            font-size: 13px;
            color: var(--muted);
            text-decoration: none;
            display: inline-flex;
            align-items: center;
            gap: 4px;
            transition: color 0.2s;
        }
        .back-home:hover { color: var(--violet); }

        /* 已登录态 */
        .user-card { text-align: center; }
        .user-avatar {
            width: 72px; height: 72px;
            border-radius: 50%;
            border: 2px solid var(--violet);
            object-fit: cover;
            margin-bottom: 14px;
            box-shadow: 0 0 20px var(--violet-glow);
        }
        .user-nickname { font-size: 19px; font-weight: 700; margin-bottom: 4px; }
        .user-id { font-size: 12px; color: var(--muted); margin-bottom: 24px; }
        .btn-primary {
            display: inline-block;
            padding: 10px 28px;
            background: var(--violet);
            border: none;
            color: #fff;
            border-radius: 10px;
            font-size: 14px;
            font-weight: 600;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
            margin: 0 6px;
        }
        .btn-primary:hover { background: #7c4df0; box-shadow: 0 6px 20px var(--violet-glow); }
        .btn-logout {
            display: inline-block;
            padding: 10px 28px;
            background: transparent;
            border: 1px solid var(--violet);
            color: var(--violet);
            border-radius: 10px;
            font-size: 14px;
            cursor: pointer;
            text-decoration: none;
            transition: all 0.2s;
            margin: 0 6px;
        }
        .btn-logout:hover { background: var(--violet); color: #fff; }

        /* 登录成功过渡 */
        .success-icon {
            width: 60px; height: 60px;
            border-radius: 50%;
            background: var(--violet);
            display: flex; align-items: center; justify-content: center;
            margin: 0 auto 16px;
            animation: scaleIn 0.35s ease;
            box-shadow: 0 0 24px var(--violet-glow);
        }
        .success-icon svg { width: 30px; height: 30px; stroke: #fff; fill: none; stroke-width: 3; stroke-linecap: round; stroke-linejoin: round; }
        @keyframes scaleIn { from { transform: scale(0); } to { transform: scale(1); } }
        .success-text { font-size: 17px; font-weight: 600; margin-bottom: 8px; }
        .success-hint { font-size: 12px; color: var(--muted); }
    </style>
</head>
<body>
    <a href="../index.html" class="back-home">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M19 12H5M12 19l-7-7 7-7"/></svg>
        返回首页
    </a>

    <div class="login-card">
        <?php if ($is_logged_in): ?>
            <!-- 已登录 -->
            <div class="user-card">
                <img class="user-avatar" src="<?php echo htmlspecialchars($user['faceimg'] ?? '../favicon.ico'); ?>" alt="头像">
                <div class="user-nickname"><?php echo htmlspecialchars($user['nickname'] ?? '云集用户'); ?></div>
                <div class="user-id">ID: <?php echo htmlspecialchars($user['social_uid'] ?? '-'); ?></div>
                <a href="<?php echo htmlspecialchars($appHref); ?>" class="btn-primary"><?php echo htmlspecialchars($appLabel); ?></a>
                <a href="./logout.php" class="btn-logout">退出登录</a>
            </div>
        <?php else: ?>
            <!-- 未登录 - 显示微信扫码二维码 -->
            <img src="../favicon.ico" alt="云集" class="login-logo">
            <div class="login-title">登录 <span class="accent">云集智能音乐创意台</span></div>
            <div class="login-subtitle">微信扫一扫，快速登录你的创作账户</div>
            <div class="qrcode-wrap">
                <iframe src="./connect.php?type=wx" width="200" height="200" frameborder="0" scrolling="no"></iframe>
            </div>
            <div class="login-hint">
                扫码即代表同意 <a href="#">用户协议</a> 和 <a href="#">隐私政策</a>
            </div>
        <?php endif; ?>
    </div>

    <script>
        // 监听 iframe 内 connect.php 发来的登录成功消息，刷新本页以显示已登录态
        window.addEventListener('message', function (e) {
            if (e.data && e.data.type === 'loginSuccess') {
                window.location.reload();
            }
        });
    </script>
</body>
</html>
