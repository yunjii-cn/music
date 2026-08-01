<?php

/**
 * 云集用户系统 (UM) - PHP SDK（新接口版本）
 *
 * 一行代码接入扫码登录，调用 UM 最新接口
 *
 * 协议版本：UM v2.0（新增时间戳+签名防重放）
 * 更新日期：2026-06-10
 *
 * 安全机制：
 *   - 所有请求携带 timestamp（Unix 时间戳）+ sign（MD5 签名）
 *   - 签名规则：参数按 key 字典序排列，拼接 key=value&...&appkey=xxx，MD5
 *   - 服务端验证：时间戳 5 分钟内有效 + 签名正确
 *   - 旧版仅传 appkey 的方式仍兼容，但建议尽快升级
 *
 * 使用方法：
 *   1. 在 https://um.yunjii.cn/um/admin/apps.php 创建应用获取 appid/appkey
 *   2. 在您的网站引入本文件
 *   3. 调用 UM::qrcodeUrl($type) 生成二维码图片地址
 *   4. 在您的回调页面调用 UM::token() 完成登录
 *
 * 完整示例见 example.php
 */

class UM
{
    private $apiurl;
    private $appid;
    private $appkey;
    private $callback;

    /**
     * @param string $appid  应用 ID（在 UM 后台获取）
     * @param string $appkey 应用密钥（在 UM 后台获取）
     * @param string $callback 登录成功回调地址（必须是 https）
     * @param string $apiurl  UM API 根地址，默认 https://um.yunjii.cn/
     */
    public function __construct($appid, $appkey, $callback, $apiurl = 'https://api.yunjii.cn/')
    {
        $this->apiurl   = rtrim($apiurl, '/') . '/';
        $this->appid    = $appid;
        $this->appkey   = $appkey;
        $this->callback = $callback;
    }

    /**
     * 获取标准 OAuth 2.0 授权页 URL（推荐新接入使用）
     * @param string $state 业务方自定义 state（可选）
     * @return string
     */
    public function authorizeUrl($state = '')
    {
        $params = [
            'response_type' => 'code',
            'client_id'     => $this->appid,
            'redirect_uri'  => $this->callback,
            'state'         => $state,
            'timestamp'     => time(),
        ];
        $params['sign'] = $this->sign($params);
        return $this->apiurl . 'oauth/authorize.php?' . http_build_query($params);
    }

    /**
     * 获取二维码图片 URL
     * @param string $type page（默认）| wx | qq | alipay
     * @param int    $size 图片尺寸
     * @param string $state
     * @return string
     */
    public function qrcodeUrl($type = 'page', $size = 200, $state = '')
    {
        $params = [
            'appid'        => $this->appid,
            'type'         => $type,
            'redirect_uri' => $this->callback,
            'state'        => $state,
            'size'         => $size,
            'timestamp'    => time(),
        ];
        $params['sign'] = $this->sign($params);
        return $this->apiurl . 'api/qrcode.php?' . http_build_query($params);
    }

    /**
     * 用 authorization code 换取 access_token（推荐新接入使用）
     * @param string $code
     * @return array
     */
    public function token($code)
    {
        $params = [
            'grant_type'    => 'authorization_code',
            'code'          => $code,
            'client_id'     => $this->appid,
            'client_secret' => $this->appkey,
            'timestamp'     => time(),
        ];
        $params['sign'] = $this->sign($params);
        $url      = $this->apiurl . 'oauth/token.php';
        $response = $this->post_curl($url, $params);
        return json_decode($response, true);
    }

    /**
     * 获取旧版登录跳转 URL（兼容老接口）
     * @param string $type  登录方式：wx/qq/alipay 等
     * @param string $state 业务方自定义 state（可选）
     * @return array  {code:0, url:'https://...', type:'wx'}
     * @deprecated 请使用 authorizeUrl() / token()
     */
    public function login($type = 'wx', $state = '')
    {
        $params = [
            'id'           => 'web_qrcode_app_wrp',
            'act'          => 'login',
            'appid'        => $this->appid,
            'type'         => $type,
            'redirect_uri' => $this->callback,
            'state'        => $state,
            'timestamp'    => time(),
        ];
        $params['sign'] = $this->sign($params);
        $url      = $this->apiurl . 'um/connect.php?' . http_build_query($params);
        $response = $this->get_curl($url);
        return json_decode($response, true);
    }

    /**
     * 处理旧版 OAuth 回调
     * @return array
     * @deprecated 请使用 token()
     */
    public function callback()
    {
        $code = isset($_GET['code']) ? $_GET['code'] : '';
        if (!$code) {
            return ['code' => -1, 'msg' => 'no code'];
        }
        $params = [
            'act'       => 'callback',
            'appid'     => $this->appid,
            'code'      => $code,
            'timestamp' => time(),
        ];
        $params['sign'] = $this->sign($params);
        $url      = $this->apiurl . 'um/connect.php?' . http_build_query($params);
        $response = $this->get_curl($url);
        return json_decode($response, true);
    }

    /**
     * 查询第三方用户信息
     * @param string $type       登录方式
     * @param string $social_uid 用户 openid
     * @return array
     */
    public function query($type, $social_uid)
    {
        $params = [
            'act'        => 'query',
            'appid'      => $this->appid,
            'type'       => $type,
            'social_uid' => $social_uid,
            'timestamp'  => time(),
        ];
        $params['sign'] = $this->sign($params);
        $url      = $this->apiurl . 'um/connect.php?' . http_build_query($params);
        $response = $this->get_curl($url);
        return json_decode($response, true);
    }

    /**
     * 生成签名
     *
     * 规则：将所有参数按 key 字典序排列，拼接成 key=value&key=value，
     * 末尾追加 &appkey=xxx，然后 MD5
     *
     * @param array $params 请求参数（不含 sign）
     * @return string MD5 签名
     */
    private function sign($params)
    {
        unset($params['sign']);
        ksort($params);
        $str = '';
        foreach ($params as $k => $v) {
            $str .= $k . '=' . $v . '&';
        }
        $str .= 'appkey=' . $this->appkey;
        return md5($str);
    }

    private function get_curl($url)
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 UM-SDK/3.0');
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        $ret = curl_exec($ch);
        return $ret;
    }

    private function post_curl($url, $data)
    {
        $ch = curl_init();
        curl_setopt($ch, CURLOPT_URL, $url);
        curl_setopt($ch, CURLOPT_SSL_VERIFYPEER, false);
        curl_setopt($ch, CURLOPT_SSL_VERIFYHOST, false);
        curl_setopt($ch, CURLOPT_USERAGENT, 'Mozilla/5.0 UM-SDK/3.0');
        curl_setopt($ch, CURLOPT_TIMEOUT, 10);
        curl_setopt($ch, CURLOPT_RETURNTRANSFER, 1);
        curl_setopt($ch, CURLOPT_POST, 1);
        curl_setopt($ch, CURLOPT_POSTFIELDS, http_build_query($data));
        $ret = curl_exec($ch);
        return $ret;
    }
}
