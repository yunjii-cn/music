<?php

/**
 * 云集智能音乐创意台 - UM 扫码登录回调/跳转处理
 * 参考：云集智能视频创意站 web/sl/connect.php（精简版，仅保留核心 UM 登录）
 *
 * 流程：
 *   未带 code  → act=login，拿到扫码页地址后让 iframe 跳转过去显示二维码
 *   带 code    → act=callback，用 code 换用户信息，写入 session，postMessage 通知父页
 */

error_reporting(E_ALL);
ini_set('display_errors', 0);
ini_set('log_errors', 1);
ini_set('error_log', __DIR__ . '/error.log');

function umLog($msg, $level = 'info')
{
    $ts = date('Y-m-d H:i:s');
    @file_put_contents('/tmp/mi-um.log', "[$ts][$level] $msg\n", FILE_APPEND);
}

session_start();
@header('Content-Type: text/html; charset=UTF-8');

include_once __DIR__ . '/config.php';
include_once __DIR__ . '/UM.class.php';

umLog('--- 收到新请求 ---');
umLog('GET: ' . json_encode($_GET));
umLog('SESSION_id: ' . session_id());

$type = isset($_GET['type']) ? $_GET['type'] : 'wx';

// ① 回调分支：UM 扫码成功后带着 code 跳回这里
if (isset($_GET['code']) && $_GET['code']) {
    umLog('>>> 进入 callback 分支');
    $UM  = new UM($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);
    $arr = $UM->callback();
    umLog('UM->callback() 返回: ' . json_encode($arr));

    if (isset($arr['code']) && $arr['code'] == 0) {
        // 写入 session
        $_SESSION['user'] = $arr;

        umLog('callback 成功，postMessage 通知父页');
        // 让父页面（登录页 iframe 的父级）收到消息后刷新以显示已登录态
        $userJson = json_encode($arr, JSON_UNESCAPED_UNICODE);
        exit("<script language='javascript'>
            if (window.parent && window.parent !== window) {
                window.parent.postMessage({type: 'loginSuccess', user: $userJson}, '*');
            } else {
                window.location.href = './index.php?t=' + Date.now();
            }
        </script>");
    }

    // 失败 / code 已消费：跳回登录页
    umLog('callback 返回错误或无返回，跳回 index.php: ' . json_encode($arr), 'warn');
    $target = './index.php?t=' . time();
    exit("<script language='javascript'>window.location.href='$target';</script>");
}

// ② 登录分支：生成扫码页地址，iframe 内跳过去显示二维码
umLog('>>> 进入 login 分支，type=' . $type);
$UM  = new UM($UM_CONFIG['appid'], $UM_CONFIG['appkey'], $UM_CONFIG['callback'], $UM_CONFIG['apiurl']);
$arr = $UM->login($type);
if (isset($arr['code']) && $arr['code'] == 0) {
    // 跳到 UM 扫码页（该页会在 iframe 内显示二维码）
    exit("<script language='javascript'>window.location.href='{$arr['url']}';</script>");
} elseif (isset($arr['code'])) {
    exit('登录接口返回：' . htmlspecialchars($arr['msg']));
} else {
    exit('获取登录地址失败（UM 服务无响应）');
}
