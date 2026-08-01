<?php
/**
 * 云集智能音乐创意台 - 登录状态检查（API 接口）
 *
 * 双重用途：
 *   1. 前端页面（login.html）轮询/校验登录态 —— 返回 JSON
 *   2. 软件客户端（深链门控）查询用户信息 —— 返回 JSON + token
 *
 * GET 参数：
 *   ?set_verifier=<pkce_verifier>  写入 PKCE code_verifier 到 session（OAuth 流程）
 *   ?full=1                        返回完整用户对象（含 token，供软件端导入）
 *
 * 参考：云集智能视频创意站 web/sl/islogin.php
 */

session_start();
header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Cache-Control: no-cache, no-store, must-revalidate');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// -- PKCE code_verifier 临时存储（login.html 发起 OAuth 前写入） --
if (isset($_GET['set_verifier']) && $_GET['set_verifier'] !== '') {
    $_SESSION['oauth_code_verifier'] = $_GET['set_verifier'];
    echo json_encode(['code' => 1, 'msg' => 'ok']);
    exit;
}

// -- 优先 Session 认证 --
if (isset($_SESSION['user'])) {
    outputLoggedIn($_SESSION['user']);
    exit;
}

// -- Token 认证（Bearer token，供软件客户端/API 直接调用） --
$token = null;
if (!empty($_SERVER['HTTP_AUTHORIZATION'])) {
    $token = preg_replace('/^Bearer\s+/i', '', $_SERVER['HTTP_AUTHORIZATION']);
}
if (!$token && isset($_GET['token'])) {
    $token = $_GET['token'];
}
if ($token) {
    require_once __DIR__ . '/config.php';
    require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenClient.php';
    require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenQr.php';

    $qr = new UMOpenQr($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);
    $client = new UMOpenClient($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);
    $user = $client->userinfo($token);
    if (!empty($user) && !isset($user['error'])) {
        $localUser = $qr->toLocalUser($user, $token);
        $_SESSION['user'] = $localUser;
        outputLoggedIn($localUser);
        exit;
    }
}

// 未登录
echo json_encode(['code' => 0, 'msg' => '未登录']);

// ============================================================

function outputLoggedIn($user)
{
    $full = isset($_GET['full']) || !empty($_SERVER['HTTP_AUTHORIZATION']);

    $data = [
        'nickname'     => $user['nickname'] ?? '',
        'avatar'       => $user['faceimg'] ?? '',
        'openid'       => $user['social_uid'] ?? '',
        'username'     => $user['username'] ?? '',
        'gender'       => $user['gender'] ?? '',
        'location'     => $user['location'] ?? '',
        'type'         => $user['type'] ?? '',
    ];

    // 返回 token（软件客户端需要 token 来做后续 API 调用）
    if ($full) {
        $data['token']        = $user['token'] ?? '';
        $data['access_token'] = $user['access_token'] ?? '';
        $data['site']         = $user['site'] ?? '';
    }

    echo json_encode([
        'code' => 1,
        'msg'  => '已登录',
        'data' => $data,
    ]);
}
