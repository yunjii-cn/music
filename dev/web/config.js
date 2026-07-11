/**
 * 云集智能音乐创意台 — 营销官网集中配置
 *
 * 所有可配置项集中在此文件，避免散落在各页面搜索修改。
 * 修改品牌名、Logo、颜色、UM 密钥、语言等都只改这里。
 *
 * 注意：um.appkey 是服务端密钥，仅服务端(server.js)可读，
 *       前端通过 /api/site-config 获取时会被剔除（不会暴露给浏览器）。
 */

module.exports = {
  /* ============================================================
   * 站点身份（品牌）
   * ========================================================== */
  site: {
    name: '云集智能音乐创意台',
    nameEn: 'Yunji AI Music Studio',
    shortName: '云集音乐',
    logo: '/assets/img/logo.svg',
    favicon: '/assets/img/favicon.svg',
    description: '本地优先的 AI 音乐创作平台：文本生成音乐、翻唱、LoRA 风格训练，全部在你的显卡上完成。',
    keywords: 'AI音乐,音乐生成,翻唱,LoRA训练,ACE-Step,云集音乐',
    // 发布到公网的站点地址（用于 SEO / OG / 回调基础域名）
    url: process.env.SITE_URL || 'https://music.yunjii.cn',
  },

  /* ============================================================
   * 品牌配色（暗黑 + CC0000 品牌红）
   * 仅在此修改即可全局换色
   * ========================================================== */
  brand: {
    primary: '#CC0000', // 品牌主红
    primaryHover: '#E60000',
    primaryDark: '#990000',
    bg: '#0A0A0B', // 页面背景（近黑）
    surface: '#161618', // 卡片/分区背景
    surfaceAlt: '#1F1F22', // 次级表面
    border: '#2A2A2E',
    text: '#F5F5F7', // 主文字
    textMuted: '#A1A1AA', // 次要文字
    textDim: '#6B6B70',
  },

  /* ============================================================
   * UM 扫码登录（云集用户系统）
   * 服务端密钥，勿在前端硬编码
   * ========================================================== */
  um: {
    apiUrl: process.env.UM_API_URL || 'https://um.yunjii.cn/', // UM 服务根地址
    appid: process.env.UM_APPID || '1016',
    appkey: process.env.UM_APPKEY || 'd4eff6cb43a0f31c3f05ddfd0256c27b',
    // 登录回调地址（必须 https，且需在 UM 后台登记）。可用环境变量覆盖。
    callback: process.env.UM_CALLBACK_URL || 'http://localhost:7788/login/callback',
    loginType: 'wx', // 扫码方式：wx / qq / alipay
  },

  /* ============================================================
   * 多语言
   * ========================================================== */
  i18n: {
    defaultLang: 'zh-CN',
    storageKey: 'ym-site-lang',
    available: [
      { code: 'zh-CN', label: '简体中文', short: '简' },
      { code: 'zh-TW', label: '繁體中文', short: '繁' },
      { code: 'en', label: 'English', short: 'EN' },
      { code: 'ja', label: '日本語', short: '日' },
      { code: 'ko', label: '한국어', short: '한' },
    ],
  },

  /* ============================================================
   * 导航
   * ========================================================== */
  nav: [
    { key: 'home', href: '#home' },
    { key: 'features', href: '#features' },
    { key: 'how', href: '#how' },
    { key: 'download', href: '#download' },
  ],

  /* ============================================================
   * 下载（竞速下载）
   * EXE 已发布到两个远程 git 的 Releases 页，前端自动选最快镜像
   * ========================================================== */
  download: {
    // 各平台安装包文件名关键字（用于在 release assets 中匹配）
    patterns: {
      windows: /\.exe$/i,
      mac: /\.(dmg|pkg|app\.zip)$/i,
      linux: /\.(AppImage|deb|tar\.gz|rpm)$/i,
    },
    // 发布镜像（与 git remote 对应）
    mirrors: {
      github: {
        label: 'GitHub',
        owner: 'yunjii-cn',
        repo: 'music',
        api: 'https://api.github.com/repos/yunjii-cn/music/releases/latest',
        // 浏览器可直接访问的最终发布页（手动兜底）
        page: 'https://github.com/yunjii-cn/music/releases/latest',
      },
      gitee: {
        label: 'Gitee',
        owner: 'yunjii',
        repo: 'music',
        api: 'https://gitee.com/api/v5/repos/yunjii/music/releases/latest',
        page: 'https://gitee.com/yunjii/music/releases',
      },
    },
    // 缓存时长（秒），避免频繁打 git API
    cacheTtl: 300,
  },

  /* ============================================================
   * 社交 / 外链
   * ========================================================== */
  social: {
    github: 'https://github.com/yunjii-cn/music',
    gitee: 'https://gitee.com/yunjii/music',
    bilibili: '',
    discord: '',
  },

  /* ============================================================
   * 页脚
   * ========================================================== */
  footer: {
    copyright: '© 2026 云集智能音乐创意台',
    links: [
      { key: 'privacy', label: 'privacy', href: '#' },
      { key: 'terms', label: 'terms', href: '#' },
      { key: 'contact', label: 'contact', href: '#' },
    ],
  },

  /* ============================================================
   * 服务器
   * ========================================================== */
  server: {
    port: process.env.PORT || 7788,
  },
};
