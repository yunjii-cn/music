<?php
/**
 * 云集智能音乐创意台 - OAuth 2.1 回调处理器
 *
 * 标准 OAuth 2.1 Authorization Code + PKCE 流程：
 *   login.html 跳转到 UM /oauth/authorize → 用户授权 →
 *   UM 302 回本文件 ?code=...&state=... →
 *   本文件用 code 换 token → 调 /oauth/userinfo 取用户 → 写 session →
 *   302 回 login.html（已登录态自动识别）
 *
 * 参考：UM 开放接口对接文档 OAuth 2.1 + OIDC 标准
 */

error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', __DIR__ . '/error.log');

session_start();
require_once __DIR__ . '/config.php';
require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenClient.php';
require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenLogin.php';
require_once '/www/wwwroot/um.yunjii.cn/php/sdk/UMOpenQr.php';

// 目标：回到 login.html，保留所有查询参数（redirect / gate / app 等）
$loginPage = MI_DOMAIN . '/login.html';
$returnParams = [];

// 从 state 参数中解析业务透传参数
// state 格式: oauth_TIMESTAMP（无业务参数）或 oauth_TIMESTAMP|r=REDIRECT&g=GATE&a=APP
$state = $_GET['state'] ?? '';
if ($state && str_contains($state, '|')) {
    $parts = explode('|', $state, 2);
    if (count($parts) === 2) {
        parse_str($parts[1], $extraParams);
        // 映射: r → redirect, g → gate, a → app
        if (!empty($extraParams['r'])) $returnParams['redirect'] = $extraParams['r'];
        if (!empty($extraParams['g'])) $returnParams['gate'] = $extraParams['g'];
        if (!empty($extraParams['a'])) $returnParams['app'] = $extraParams['a'];
    }
}

// 也支持直接 URL 参数透传（兜底）
foreach (['redirect', 'gate', 'app'] as $k) {
    if (!empty($_GET[$k]) && empty($returnParams[$k])) {
        $returnParams[$k] = $_GET[$k];
    }
}

function goBack($error = '') {
    global $loginPage, $returnParams;
    $params = $returnParams;
    if ($error) $params['error'] = $error;
    $url = $loginPage . (empty($params) ? '' : '?' . http_build_query($params));
    header("Location: $url", true, 302);
    exit;
}

// 取 authorization code
$code = $_GET['code'] ?? '';
if (empty($code)) {
    goBack('no_code');
}

try {
    $um = new UMOpenLogin(
        $UM_CONFIG['appid'],
        $UM_CONFIG['appkey'],
        MI_DOMAIN . '/um/oauth_callback.php',
        $UM_CONFIG['apiurl']
    );
    // 直接用 UMOpenClient 调接口（UMOpenLogin/UMOpenQr 的 $client 是 private，外部不可访问）
    $client = new UMOpenClient(
        $UM_CONFIG['appid'],
        $UM_CONFIG['appkey'],
        MI_DOMAIN . '/um/oauth_callback.php',
        $UM_CONFIG['apiurl']
    );

    // PKCE: 从 session 取 code_verifier（login.html 发起前种下）
    $codeVerifier = $_SESSION['oauth_code_verifier'] ?? '';
    if (empty($codeVerifier)) {
        goBack('missing_verifier');
    }
    unset($_SESSION['oauth_code_verifier']);

    $tokenRes = $client->exchangeCode($code, $codeVerifier);
    if (empty($tokenRes) || isset($tokenRes['error'])) {
        goBack('token_error:' . ($tokenRes['error_description'] ?? $tokenRes['error'] ?? 'unknown'));
    }

    $accessToken = $tokenRes['access_token'] ?? '';
    if (empty($accessToken)) {
        goBack('no_access_token');
    }

    $userinfo = $client->userinfo($accessToken);
    if (empty($userinfo) || isset($userinfo['error'])) {
        goBack('userinfo_failed');
    }

    // 写本站 session（与 connect.php act=setsession 一致的结构）
    $qr = new UMOpenQr($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);
    $_SESSION['user'] = $qr->toLocalUser($userinfo, $accessToken);

    goBack(); // 无 error → 正常跳回 login.html

} catch (\Throwable $e) {
    error_log('[oauth_callback] ' . $e->getMessage());
    goBack('exception:' . $e->getMessage());
}
