<?php
/**
 * 云集智能音乐创意台 - 退出登录
 * 参考：云集智能视频创意站 web/sl/logout.php
 */

session_start();
header("Cache-Control: no-cache, no-store, must-revalidate");
header("Pragma: no-cache");
header("Expires: 0");

$_SESSION = array();

if (ini_get("session.use_cookies")) {
    $params = session_get_cookie_params();
    setcookie(session_name(), '', time() - 42000,
        $params["path"], $params["domain"],
        $params["secure"], $params["httponly"]
    );
}

session_destroy();

// 退出后跳回登录页（或来源页）
$redirect = './index.php';
if (isset($_SERVER['HTTP_REFERER'])) {
    $referer = $_SERVER['HTTP_REFERER'];
    if (strpos($referer, '/um/') === false && strpos($referer, 'yunjii.cn') !== false) {
        $redirect = $referer;
    }
}

header("Location: $redirect");
exit;
