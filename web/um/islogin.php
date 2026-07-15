<?php
/**
 * 云集智能音乐创意台 - 登录状态检查（API 接口）
 * 供客户端/前端调用，返回 JSON 登录状态。
 * 参考：云集智能视频创意站 web/sl/islogin.php
 */

session_start();
header('Content-Type: application/json; charset=UTF-8');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// 优先使用 Session 认证（浏览器访问，Cookie 自动携带）
if (isset($_SESSION['user'])) {
    outputLoggedIn($_SESSION['user']);
    exit;
}

// 未登录
echo json_encode(['code' => 0, 'msg' => '未登录']);

function outputLoggedIn($user)
{
    echo json_encode([
        'code' => 1,
        'data' => [
            'nickname'     => $user['nickname'] ?? '',
            'avatar'       => $user['faceimg'] ?? '',
            'openid'       => $user['social_uid'] ?? '',
            'username'     => $user['username'] ?? '',
            'token'        => $user['token'] ?? '',
            'site'         => $user['site'] ?? '',
            'gender'       => $user['gender'] ?? '',
            'location'     => $user['location'] ?? '',
            'access_token' => $user['access_token'] ?? '',
            'type'         => $user['type'] ?? '',
        ]
    ]);
}
