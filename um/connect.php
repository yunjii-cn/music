<?php

/**
 * 云集智能音乐创意台 - UM 扫码登录回调 / 二维码（云集开放接口）
 *
 * 对接「云集统一用户中心（UM）」：https://um.yunjii.cn
 * 微信扫码走 UM 原生 QR（api/qrcode.php + query.php），
 * 扫码成功后用 token 调开放接口 userinfo 端点取用户，全程标准开放接口家族。
 *
 *   - 默认：服务端取微信二维码（一次），前端轮询 query.php，扫码成功回写 session
 *   - act=setsession：前端轮询到 token 后回写本站登录态
 */

error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', __DIR__ . '/error.log');

session_start();
@header('Content-Type: text/html; charset=UTF-8');

require_once __DIR__ . '/config.php';
require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenClient.php';
require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenQr.php';

function umLog($msg, $level = 'info')
{
    @file_put_contents('/tmp/mi-um.log', '[' . date('Y-m-d H:i:s') . "][$level] $msg\n", FILE_APPEND);
}
umLog('--- 收到新请求 ---');
umLog('GET: ' . json_encode($_GET));

/**
 * 回写本站登录态（前端轮询到 token 后调用）
 */
if (isset($_GET['act']) && $_GET['act'] === 'setsession') {
    $raw  = file_get_contents('php://input');
    $data = json_decode($raw, true);
    if (isset($data['token']) && $data['token']) {
        // 走开放接口 userinfo 端点取规范用户对象（注意：$qr->client 是 private，必须直接构造 UMOpenClient 调用）
        $client = new UMOpenClient($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);
        $user = $client->userinfo($data['token']);
        $qr = new UMOpenQr($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);
        if (empty($user) || isset($user['error'])) {
            // userinfo 失败则退回扫码接口返回的基础用户
            $user = $data['user'] ?? [];
        }
        $_SESSION['user'] = $qr->toLocalUser($user, $data['token']);
        // 同步 UM 家族 SSO Cookie（.yunjii.cn 共享域）：扫码登录本身不经过 UM 授权页，
        // 浏览器没有 um_sso_token，这里补种，让用户可无缝访问 um.yunjii.cn/user 等同族站点。
        // 属性与 UM 的 um_set_sso_cookie 完全一致（config: name=um_sso_token, domain=.yunjii.cn, 168h, secure, httponly, SameSite=None）。
        if (!headers_sent()) {
            setcookie('um_sso_token', $data['token'], [
                'expires'  => time() + 168 * 3600,
                'path'     => '/',
                'domain'   => '.yunjii.cn',
                'secure'   => true,
                'httponly' => true,
                'samesite' => 'None',
            ]);
        }
        umLog('setsession 成功，已写入 session(userinfo) + um_sso_token');
        echo json_encode(['code' => 1, 'msg' => 'ok']);
    } else {
        echo json_encode(['code' => -1, 'msg' => 'invalid data']);
    }
    exit;
}

$qr = new UMOpenQr($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);

/**
 * 二维码分支：服务端取一次微信二维码（保证展示图与轮询 logid 一致）
 */
umLog('>>> 进入二维码分支');
$state  = md5(uniqid((string) mt_rand(), true));
$r      = $qr->fetchQr('wx', 200, $state);
umLog('fetchQr: ' . json_encode($r));

if (isset($r['error'])) {
    echo '<div style="color:#9a96b3;font-size:13px;padding:20px;text-align:center;background:#1c1c28;border-radius:8px;">'
        . htmlspecialchars($r['error']) . '</div>';
    exit;
}

$imgSrc  = $r['img'];
$logid   = $r['logid'];
$pollUrl = $UM_CONFIG['apiurl'] . '/um/query.php?act=qrcode&logid=' . $logid;
?>
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>扫码登录</title>
    <style>
        html, body { margin: 0; padding: 0; background: #1c1c28; }
        img { display: block; border-radius: 6px; background: #fff; }
    </style>
</head>
<body>
    <img id="umQr" src="<?php echo $imgSrc; ?>" width="200" height="200" alt="登录二维码">

    <script>
    (function () {
        var logid  = '<?php echo $logid; ?>';
        var pollUrl = '<?php echo $pollUrl; ?>';
        if (!logid) return;

        var tried = 0;
        function poll() {
            tried++;
            fetch(pollUrl + '&_=' + Date.now(), { method: 'GET', credentials: 'omit', cache: 'no-store' })
                .then(function (r) { return r.json(); })
                .then(function (j) {
                    if (j && j.code === 0 && j.token) {
                        return fetch('./connect.php?act=setsession', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            credentials: 'same-origin',
                            body: JSON.stringify(j)
                        }).then(function () { return true; });
                    }
                    if (tried < 240) setTimeout(poll, 2500);
                    return false;
                })
                .then(function (ok) {
                    if (!ok) return;
                    if (window.parent && window.parent !== window) {
                        window.parent.postMessage({ type: 'loginSuccess' }, '*');
                    } else {
                        window.location.href = './index.php?t=' + Date.now();
                    }
                })
                .catch(function () {
                    if (tried < 240) setTimeout(poll, 5000);
                });
        }
        poll();
    })();
    </script>
</body>
</html>
