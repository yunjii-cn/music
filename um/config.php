<?php

/**
 * 云集智能音乐创意台 - 登录系统配置
 * 参考：云集智能视频创意站 web/sl/
 *
 * 对接「云集统一用户中心（UM）」：https://um.yunjii.cn
 * 协议：UM v1.0  →  接口 /um/connect.php
 */

// ============================================================
// ⚠️ 部署前必改：把下面的域名改成你实际部署的站点域名
//    MI_CALLBACK 必须与该应用在 um.yunjii.cn 后台登记的回调一致，
//    且必须是 https（微信/QQ 扫码回调要求）。
// ============================================================
define('MI_DOMAIN',   'https://music.yunjii.cn');                 // 本站域名
define('MI_CALLBACK', 'https://music.yunjii.cn/um/connect.php');  // 扫码成功后的回调地址

// 本地应用深链（可选）：登录成功后“进入工作台”按钮跳转地址。
// 音乐客户端是本地桌面程序，部署时可改成如 http://127.0.0.1:7860
// 留空则默认跳回官网首页。
define('MI_APP_URL', '');

// OAuth 2.1 回调地址（标准 OIDC 授权码流程）—— 必须在 UM 后台登记
define('MI_OAUTH_CALLBACK', 'https://music.yunjii.cn/um/oauth_callback.php');

// UM 用户中心 SDK 配置
$UM_CONFIG = [
    'apiurl'  => 'https://api.yunjii.cn/',                 // UM API 根地址（收口：经 api 网关代理）
    'appid'   => '1016',                                  // 应用 ID（在 um.yunjii.cn 后台获取）
    'appkey'  => 'd4eff6cb43a0f31c3f05ddfd0256c27b',      // 应用密钥（切勿在前端暴露）
    'callback'=> MI_CALLBACK,
    'oauth_callback' => MI_OAUTH_CALLBACK,
];

// 统一用户资料网关（"数据在 UM，UI 在各应用"的收口 /user/profile）
// 同机直连 8080 + Host 头，避免公网 TLS 波动；语义上仍是 api.yunjii.cn 能力域。
// 服务端以 Bearer 携带本站 session 里的 UM JWT 调用，前端不接触 token、不跨域。
define('MI_API_PROFILE_URL',  'http://127.0.0.1:8080/user/profile');
define('MI_API_PROFILE_HOST', 'api.yunjii.cn');
