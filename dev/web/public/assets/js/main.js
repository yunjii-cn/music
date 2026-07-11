/**
 * 官网主逻辑 — 多语言切换、登录态、UM 扫码弹窗
 */
(function () {
  'use strict';

  // 从服务端安全配置注入（由 index.html 内联提供）
  var SITE = window.__SITE__ || {};
  var I18N = window.__I18N__ || {};

  var LANG_KEY = (SITE.i18n && SITE.i18n.storageKey) || 'ym-site-lang';
  var DEFAULT_LANG = (SITE.i18n && SITE.i18n.defaultLang) || 'zh-CN';
  var AVAILABLE = (SITE.i18n && SITE.i18n.available) || [{ code: 'zh-CN', label: '简体中文' }];

  function getLang() {
    var l = localStorage.getItem(LANG_KEY) || DEFAULT_LANG;
    if (!I18N[l]) l = DEFAULT_LANG;
    return l;
  }
  function setLang(l) {
    localStorage.setItem(LANG_KEY, l);
    applyI18n(l);
  }

  function t(path, lang) {
    var parts = path.split('.');
    var obj = I18N[lang] || I18N[DEFAULT_LANG];
    for (var i = 0; i < parts.length; i++) {
      if (obj == null) return path;
      obj = obj[parts[i]];
    }
    return obj == null ? path : obj;
  }

  function applyI18n(lang) {
    var dict = I18N[lang] || I18N[DEFAULT_LANG];
    if (!dict) return;

    // 站点名称
    var brandName = document.querySelector('[data-i18n="brand"]');
    if (brandName) brandName.textContent = (SITE.site && SITE.site.name) || '云集音乐';

    // 通用 data-i18n 文本替换
    document.querySelectorAll('[data-i18n]').forEach(function (el) {
      var key = el.getAttribute('data-i18n');
      if (key === 'brand') return;
      var val = t(key, lang);
      if (typeof val === 'string') el.textContent = val;
    });

    // 列表型（features / how）动态渲染
    renderFeatures(dict);
    renderHow(dict);
    renderNav(dict);
    renderFooter(dict);
    renderDownload(dict);
    renderHero(dict);

    // 语言选择器同步
    var sel = document.getElementById('langSelect');
    if (sel) sel.value = lang;

    document.documentElement.lang = lang;
  }

  function renderHero(dict) {
    var h = dict.hero; if (!h) return;
    var badge = document.querySelector('[data-hero="badge"]');
    var title = document.querySelector('[data-hero="title"]');
    var sub = document.querySelector('[data-hero="subtitle"]');
    var cta1 = document.querySelector('[data-hero="cta1"]');
    var cta2 = document.querySelector('[data-hero="cta2"]');
    if (badge) badge.textContent = h.badge;
    if (title) { title.innerHTML = h.title; }
    if (sub) sub.textContent = h.subtitle;
    if (cta1) cta1.textContent = h.ctaPrimary;
    if (cta2) cta2.textContent = h.ctaSecondary;
    var stats = document.querySelector('[data-hero="stats"]');
    if (stats) {
      stats.innerHTML = '';
      (h.stats || []).forEach(function (s) {
        var span = document.createElement('span');
        span.textContent = s;
        stats.appendChild(span);
      });
    }
  }

  function renderNav(dict) {
    var navEl = document.querySelector('[data-nav]');
    if (!navEl || !dict.nav) return;
    navEl.innerHTML = '';
    (SITE.nav || []).forEach(function (item) {
      var a = document.createElement('a');
      a.href = item.href;
      a.textContent = dict.nav[item.key] || item.key;
      navEl.appendChild(a);
    });
  }

  function renderFeatures(dict) {
    var grid = document.querySelector('[data-features]');
    if (!grid || !dict.features) return;
    document.querySelector('[data-features-title]').textContent = dict.features.title;
    document.querySelector('[data-features-sub]').textContent = dict.features.subtitle;
    grid.innerHTML = '';
    (dict.features.items || []).forEach(function (it) {
      var card = document.createElement('div');
      card.className = 'feature-card';
      card.innerHTML =
        '<div class="icon">' + it.icon + '</div>' +
        '<h3></h3><p></p>';
      card.querySelector('h3').textContent = it.title;
      card.querySelector('p').textContent = it.desc;
      grid.appendChild(card);
    });
  }

  function renderHow(dict) {
    var wrap = document.querySelector('[data-how]');
    if (!wrap || !dict.how) return;
    document.querySelector('[data-how-title]').textContent = dict.how.title;
    document.querySelector('[data-how-sub]').textContent = dict.how.subtitle;
    wrap.innerHTML = '';
    (dict.how.steps || []).forEach(function (s) {
      var step = document.createElement('div');
      step.className = 'step';
      step.innerHTML = '<div class="n"></div><h3></h3><p></p>';
      step.querySelector('.n').textContent = s.n;
      step.querySelector('h3').textContent = s.title;
      step.querySelector('p').textContent = s.desc;
      wrap.appendChild(step);
    });
  }

  function renderDownload(dict) {
    var sec = document.querySelector('[data-download]');
    if (!sec || !dict.download) return;
    document.querySelector('[data-download-title]').textContent = dict.download.title;
    document.querySelector('[data-download-sub]').textContent = dict.download.subtitle;
    document.querySelector('[data-dl-win]').textContent = dict.download.windows;
    document.querySelector('[data-dl-mac]').textContent = dict.download.mac;
    document.querySelector('[data-dl-linux]').textContent = dict.download.linux;
    document.querySelector('[data-dl-note]').textContent = dict.download.note;

    // 绑定竞速下载
    document.querySelectorAll('[data-platform]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        startRaceDownload(btn.getAttribute('data-platform'));
      });
    });

    // 拉取最新版本信息 + 镜像手动链接
    refreshDownloadMeta();
  }

  function refreshDownloadMeta() {
    fetch('/download/latest')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        if (d && d.version) {
          var v = document.querySelector('[data-dl-version]');
          if (v) v.textContent = '最新版本：' + d.version;
        }
        renderMirrorLinks(d);
      })
      .catch(function () {});
  }

  function renderMirrorLinks(d) {
    var row = document.querySelector('[data-dl-mirrors]');
    if (!row) return;
    var mirrors = (SITE.download && SITE.download.mirrors) || {};
    var html = '<span style="font-size:13px;color:var(--text-dim)">其他镜像：</span> ';
    var any = false;
    Object.keys(mirrors).forEach(function (k) {
      var m = mirrors[k];
      if (m.page) {
        html += '<a href="' + m.page + '" target="_blank" rel="noopener" style="font-size:13px;color:var(--text-muted);margin-left:10px">' + m.label + '</a>';
        any = true;
      }
    });
    row.innerHTML = any ? html : '';
  }

  /**
   * 竞速下载：从 /download/latest 取各镜像地址，
   * 用 no-cors HEAD 探测各镜像延迟，自动跳转到最快的一个。
   * 若探测失败，则回退到第一个可用镜像。
   */
  function startRaceDownload(platform) {
    var btn = document.querySelector('[data-platform="' + platform + '"]');
    if (btn) {
      var old = btn.textContent;
      btn.disabled = true;
      btn.textContent = '测速中…';
      setTimeout(function () { btn.disabled = false; btn.textContent = old; }, 6000);
    }

    fetch('/download/latest')
      .then(function (r) { return r.json(); })
      .then(function (d) {
        var plat = (d && d.assets && d.assets[platform]) || {};
        var keys = Object.keys(plat);
        if (keys.length === 0) {
          // 无可用资源，回退到发布页
          fallbackToReleasePage(platform);
          return;
        }
        if (keys.length === 1) {
          window.location.href = plat[keys[0]];
          return;
        }
        // 多镜像竞速：谁先响应 HEAD 谁赢
        var winner = null;
        var done = false;
        keys.forEach(function (k) {
          var t0 = performance.now();
          fetch(plat[k], { method: 'HEAD', mode: 'no-cors', cache: 'no-store', signal: AbortSignal.timeout(6000) })
            .then(function () {
              if (!done) {
                done = true;
                winner = plat[k];
                window.location.href = winner;
              }
            })
            .catch(function () {
              if (!done && k === keys[keys.length - 1]) {
                // 全部失败，用第一个
                window.location.href = plat[keys[0]];
              }
            });
        });
      })
      .catch(function () {
        fallbackToReleasePage(platform);
      });
  }

  function fallbackToReleasePage(platform) {
    var mirrors = (SITE.download && SITE.download.mirrors) || {};
    var first = Object.keys(mirrors).map(function (k) { return mirrors[k].page; }).filter(Boolean)[0];
    if (first) window.location.href = first;
  }

  function renderFooter(dict) {
    var links = document.querySelector('[data-footer-links]');
    if (links && dict.footer) {
      links.innerHTML = '';
      (SITE.footer && SITE.footer.links || []).forEach(function (l) {
        var a = document.createElement('a');
        a.href = l.href;
        a.textContent = dict.footer[l.key] || l.label;
        links.appendChild(a);
      });
    }
    var copy = document.querySelector('[data-footer-copy]');
    if (copy && SITE.footer) copy.textContent = SITE.footer.copyright;
  }

  /* ---------------- Login ---------------- */
  function renderLangOptions() {
    var sel = document.getElementById('langSelect');
    if (!sel) return;
    sel.innerHTML = '';
    AVAILABLE.forEach(function (lang) {
      var o = document.createElement('option');
      o.value = lang.code;
      o.textContent = lang.label;
      sel.appendChild(o);
    });
  }

  function openLogin() {
    var mask = document.getElementById('loginMask');
    mask.classList.add('show');
    var status = document.getElementById('loginStatus');
    status.className = 'status';
    status.textContent = (I18N[getLang()] || {}).login
      ? I18N[getLang()].login.scanHint : '';
    // 加载二维码（iframe，跨域经由 UM 返回微信 QR）
    var frame = document.getElementById('qrFrame');
    frame.src = '/login/qr?type=' + ((SITE.um && SITE.um.loginType) || 'wx') + '&t=' + Date.now();
  }
  function closeLogin() {
    var mask = document.getElementById('loginMask');
    mask.classList.remove('show');
    var frame = document.getElementById('qrFrame');
    if (frame) frame.src = 'about:blank';
  }

  function showLoggedIn(user) {
    var btn = document.getElementById('loginBtn');
    var chip = document.getElementById('userChip');
    var avatar = document.getElementById('userAvatar');
    var name = document.getElementById('userName');
    if (btn) btn.style.display = 'none';
    if (chip) chip.style.display = 'flex';
    if (avatar && user.faceimg) avatar.src = user.faceimg;
    if (avatar) avatar.style.display = user.faceimg ? 'block' : 'none';
    if (name) name.textContent = (I18N[getLang()].login.welcome) + (user.nickname || user.social_uid);
  }
  function showLoggedOut() {
    var btn = document.getElementById('loginBtn');
    var chip = document.getElementById('userChip');
    if (btn) btn.style.display = 'inline-flex';
    if (chip) chip.style.display = 'none';
  }

  function logout() {
    fetch('/logout').then(function () {
      showLoggedOut();
      var chip = document.getElementById('userChip');
      if (chip) chip.innerHTML =
        '<img id="userAvatar" class="avatar" alt=""/><span class="name" id="userName"></span>' +
        '<button class="btn btn-ghost" id="logoutBtn" style="padding:6px 12px;font-size:13px"></button>';
      bindLogout();
    });
  }
  function bindLogout() {
    var b = document.getElementById('logoutBtn');
    if (b) {
      b.textContent = (I18N[getLang()].login.logout);
      b.addEventListener('click', logout);
    }
  }

  function checkLogin() {
    fetch('/api/is-login').then(function (r) { return r.json(); }).then(function (r) {
      if (r.code === 1 && r.data) showLoggedIn(r.data);
      else showLoggedOut();
    }).catch(showLoggedOut);
  }

  // 接收 UM 回调 postMessage
  window.addEventListener('message', function (e) {
    var d = e.data || {};
    if (d.type === 'loginSuccess') {
      var status = document.getElementById('loginStatus');
      status.className = 'status ok';
      status.textContent = (I18N[getLang()].login.loginSuccess);
      showLoggedIn(d.user);
      setTimeout(closeLogin, 900);
    } else if (d.type === 'loginError') {
      var s = document.getElementById('loginStatus');
      s.className = 'status err';
      s.textContent = (I18N[getLang()].login.loginFailed) + '：' + (d.error || '');
    }
  });

  /* ---------------- Init ---------------- */
  document.addEventListener('DOMContentLoaded', function () {
    // 先从服务端拉取安全配置（剔除 appkey），再渲染
    fetch('/api/site-config')
      .then(function (r) { return r.json(); })
      .then(function (cfg) {
        window.__SITE__ = cfg;
        SITE = cfg;
        if (cfg.i18n && cfg.i18n.storageKey) LANG_KEY = cfg.i18n.storageKey;
        if (cfg.i18n && cfg.i18n.defaultLang) DEFAULT_LANG = cfg.i18n.defaultLang;
        if (cfg.i18n && cfg.i18n.available) AVAILABLE = cfg.i18n.available;
        renderLangOptions();
        applyI18n(getLang());
        bindUi();
      })
      .catch(function () {
        applyI18n(getLang());
        bindUi();
      });
  });

  function bindUi() {
    var sel = document.getElementById('langSelect');
    if (sel) sel.addEventListener('change', function () { setLang(this.value); });

    var loginBtn = document.getElementById('loginBtn');
    if (loginBtn) loginBtn.addEventListener('click', openLogin);
    var loginHeroBtn = document.getElementById('loginHeroBtn');
    if (loginHeroBtn) loginHeroBtn.addEventListener('click', openLogin);

    var closeBtn = document.getElementById('loginClose');
    if (closeBtn) closeBtn.addEventListener('click', closeLogin);
    var mask = document.getElementById('loginMask');
    if (mask) mask.addEventListener('click', function (e) {
      if (e.target === mask) closeLogin();
    });

    bindLogout();
    checkLogin();
  }
})();
