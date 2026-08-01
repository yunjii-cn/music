<?php
/**
 * 云集智能音乐创意台 - 退出登录（云集开放接口）
 * 收口逻辑（与登录页 login.html 对称）：
 *   - 清除本站 session + 本站 cookie
 *   - 清除跨站 SSO cookie（um_sso_token，.yunjii.cn 共享域），保证同族站点也登出
 *   - 吊销 token
 *   - 回跳地址（redirect）支持：
 *       * 同域 music.yunjii.cn  → 走 UM OIDC end_session 单点登出，再回该页
 *       * 跨域（仅允许 localhost/127.0.0.1，即桌面启动器）→ 本地清完直接回跳
 *       * 未提供               → 站内 HTTP_REFERER，再无则回登录页
 *   - 退出后渲染简洁的「已退出」页面（LOGO + 网站标题 + 重新登录），不再回到登录表单
 */

session_start();
require_once __DIR__ . '/config.php';
require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenClient.php';
require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenLogin.php';

header("Cache-Control: no-cache, no-store, must-revalidate");
header("Pragma: no-cache");
header("Expires: 0");

// ---------- 是否“展示退出页”的第二段请求 ----------
if (!empty($_GET['done']) && $_GET['done'] === '1') {
    $to    = $_GET['to'] ?? '';
    $embed = !empty($_GET['embed']) ? $_GET['embed'] : '';
    renderLogoutPage($to, $embed);
    exit;
}

// ============================================================
//  第一段：执行清理，并决定去向
// ============================================================

// 吊销本站会话 token（如有）
if (!empty($_SESSION['user']['token'])) {
    try {
        $um = new UMOpenLogin($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);
        $um->revoke($_SESSION['user']['token'], 'access_token');
    } catch (\Throwable $e) { /* 忽略吊销失败 */ }
}

// 清除本站 session
$_SESSION = array();
if (ini_get("session.use_cookies")) {
    $params = session_get_cookie_params();
    setcookie(session_name(), '', time() - 42000,
        $params["path"], $params["domain"], $params["secure"], $params["httponly"]);
}
session_destroy();

// 清除跨站 SSO cookie（.yunjii.cn 共享域），保证同族站点也登出
if (!headers_sent()) {
    setcookie('um_sso_token', '', [
        'expires'  => time() - 42000,
        'path'     => '/',
        'domain'   => '.yunjii.cn',
        'secure'   => true,
        'httponly' => true,
        'samesite' => 'None',
    ]);
}

// ---------- 解析回跳目标 ----------
function mi_is_same_origin($url)
{
    if (!preg_match('#^https?://#i', $url)) return false;
    $h = parse_url($url, PHP_URL_HOST) ?: '';
    return (strpos($h, 'music.yunjii.cn') !== false);
}
function mi_is_localhost($url)
{
    if (!preg_match('#^https?://#i', $url)) return false;
    $h = parse_url($url, PHP_URL_HOST) ?: '';
    return ($h === 'localhost' || $h === '127.0.0.1' || $h === '0.0.0.0' || $h === '[::1]');
}

$redirect = $_GET['redirect'] ?? '';
$embed    = !empty($_GET['embed']) ? $_GET['embed'] : '';

$target = '';
$mode   = '';   // 'um_sso' | 'direct'

if ($redirect !== '') {
    if (mi_is_same_origin($redirect)) {
        $target = $redirect;
        $mode   = 'um_sso';
    } elseif (mi_is_localhost($redirect)) {
        $target = $redirect;
        $mode   = 'direct';
    }
}
if ($target === '') {
    if (!empty($_SERVER['HTTP_REFERER']) && mi_is_same_origin($_SERVER['HTTP_REFERER'])) {
        $target = $_SERVER['HTTP_REFERER'];
        $mode   = 'um_sso';
    } else {
        $target = defined('MI_DOMAIN') ? MI_DOMAIN . '/login.html' : './index.php';
        $mode   = 'um_sso';
    }
}

// 第二段落地地址（始终落在本站的退出页，由它渲染 + 提供“重新登录”）
$landing = MI_DOMAIN . '/um/logout.php?done=1&to=' . urlencode($target);
if ($embed === '1') {
    $landing .= '&embed=1';
}

if ($mode === 'um_sso') {
    // 同域：走 UM 单点登出，再回到本站退出页
    $um = new UMOpenLogin($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['oauth_callback'], $UM_CONFIG['apiurl']);
    header("Location: " . $um->logoutUrl($landing));
} else {
    // 启动器跨域：本地已清完，直接落本站退出页（post_logout 不接受 localhost）
    header("Location: " . $landing);
}
exit;

// ============================================================
//  渲染简洁的“已退出”页面
// ============================================================
function renderLogoutPage($to, $embed)
{
    $siteTitle = '云集智能音乐创意台';
    // 重新登录：回到登录页，并把原目标作为 redirect 带回（启动器则回到应用首页）
    $loginUrl = defined('MI_DOMAIN') ? MI_DOMAIN . '/login' : './login.html';
    if ($to !== '') {
        $loginUrl .= '?redirect=' . urlencode($to);
    }
    if ($embed === '1') {
        $loginUrl .= (strpos($loginUrl, '?') === false ? '?' : '&') . 'embed=1';
    }
    $favicon = defined('MI_DOMAIN') ? MI_DOMAIN . '/favicon.ico' : './favicon.ico';
    ?>
<!DOCTYPE html>
<html lang="zh-CN"<?php echo $embed === '1' ? ' class="embed"' : ''; ?>>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>已退出 - <?php echo htmlspecialchars($siteTitle); ?></title>
    <link rel="shortcut icon" href="<?php echo $favicon; ?>">
    <style>
        :root {
            --bg: #14141f;
            --card: #1c1c28;
            --violet: #8B5CF6;
            --violet-hover: #7c4df0;
            --violet-glow: rgba(139, 92, 246, 0.35);
            --text: #efeafc;
            --muted: #9a96b3;
        }
        * { box-sizing: border-box; }
        html, body { margin: 0; padding: 0; }
        body {
            min-height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            background: radial-gradient(1200px 600px at 50% -10%, #2a2140 0%, var(--bg) 60%);
            font-family: -apple-system, BlinkMacSystemFont, "PingFang SC", "Microsoft YaHei", "Segoe UI", sans-serif;
            color: var(--text);
        }
        html.embed body { background: var(--bg); }
        .logout-card {
            width: 360px;
            max-width: 90vw;
            background: var(--card);
            border: 1px solid rgba(139, 92, 246, 0.18);
            border-radius: 18px;
            padding: 44px 32px 36px;
            text-align: center;
            box-shadow: 0 20px 60px rgba(0, 0, 0, 0.45);
        }
        .brand {
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 14px;
            margin-bottom: 26px;
        }
        .brand img {
            width: 64px;
            height: 64px;
            border-radius: 16px;
            background: rgba(139, 92, 246, 0.12);
            padding: 10px;
        }
        .brand .title {
            font-size: 18px;
            font-weight: 600;
            letter-spacing: 0.5px;
            color: #fff;
        }
        .check {
            width: 56px;
            height: 56px;
            margin: 0 auto 16px;
            border-radius: 50%;
            background: rgba(139, 92, 246, 0.14);
            display: flex;
            align-items: center;
            justify-content: center;
        }
        .check svg { width: 28px; height: 28px; stroke: var(--violet); }
        .msg { font-size: 16px; color: var(--text); margin-bottom: 4px; }
        .sub { font-size: 13px; color: var(--muted); margin-bottom: 28px; }
        .btn-primary {
            display: inline-block;
            width: 100%;
            padding: 13px 0;
            background: var(--violet);
            color: #fff;
            text-decoration: none;
            border-radius: 12px;
            font-size: 15px;
            font-weight: 600;
            transition: all 0.2s;
        }
        .btn-primary:hover {
            background: var(--violet-hover);
            box-shadow: 0 8px 24px var(--violet-glow);
        }
    </style>
</head>
<body>
    <div class="logout-card">
        <div class="brand">
            <img src="<?php echo $favicon; ?>" alt="LOGO">
            <div class="title"><?php echo htmlspecialchars($siteTitle); ?></div>
        </div>
        <div class="check">
            <svg viewBox="0 0 24 24" fill="none" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round">
                <path d="M20 6 9 17l-5-5"></path>
            </svg>
        </div>
        <div class="msg">你已安全退出</div>
        <div class="sub">感谢使用，期待下次相见</div>
        <a href="<?php echo htmlspecialchars($loginUrl); ?>" class="btn-primary">重新登录</a>
    </div>
</body>
</html>
    <?php
}
