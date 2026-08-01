/* ============================================
   云集智能音乐创意台 - 官网交互脚本
   ============================================ */
(function () {
    'use strict';

    /* --- 导航栏滚动态 --- */
    var navbar = document.getElementById('navbar');
    function onScroll() {
        if (window.scrollY > 30) {
            navbar.classList.add('scrolled');
        } else {
            navbar.classList.remove('scrolled');
        }
    }
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();

    /* --- 移动端菜单 --- */
    var navToggle = document.getElementById('navToggle');
    var navLinks = document.getElementById('navLinks');
    if (navToggle && navLinks) {
        navToggle.addEventListener('click', function () {
            navLinks.classList.toggle('open');
        });
        navLinks.querySelectorAll('a').forEach(function (a) {
            a.addEventListener('click', function () {
                navLinks.classList.remove('open');
            });
        });
    }

    /* --- 登录链接：携带当前页 URL，登录后回跳 --- */
    var loginLinks = document.querySelectorAll('a[data-login-link]');
    loginLinks.forEach(function (a) {
        a.addEventListener('click', function () {
            var base = a.getAttribute('href').split('?')[0];
            a.href = base + '?redirect=' + encodeURIComponent(window.location.href);
        });
    });

    /* --- 下载区：竞速下载 + 版本历史 --- */
    var RELEASES_JSON = './data/releases.json';
    var releaseData = null;

    function loadReleases() {
        fetch(RELEASES_JSON, { cache: 'no-cache' })
            .then(function (r) { return r.json(); })
            .then(function (data) {
                releaseData = data;
                renderLatest();
                renderVersionHistory();
            })
            .catch(function () { /* 静默失败，保留默认文案 */ });
    }

    function renderLatest() {
        if (!releaseData || !releaseData.latest) return;
        var v = releaseData.latest;
        var verEl = document.getElementById('dlVersion');
        if (verEl) verEl.textContent = v.version + ' · ' + v.date;
        // 更新 GitHub / Gitee 备选链接指向具体 release
        if (v.gh_html) {
            var gh = document.getElementById('btnGitHub');
            if (gh) gh.href = v.gh_html;
        }
        if (v.ge_html) {
            var ge = document.getElementById('btnGitee');
            if (ge) ge.href = v.ge_html;
        }
    }

    // 竞速下载：并行 HEAD 探测双镜像延迟，选最快源
    function raceDownload() {
        if (!releaseData || !releaseData.latest) {
            // 数据未加载，降级到 GitHub releases 页
            window.open('https://github.com/yunjii-cn/music/releases', '_blank');
            return;
        }
        var v = releaseData.latest;
        var sources = [];
        if (v.github) sources.push({ name: 'GitHub', url: v.github });
        if (v.gitee) sources.push({ name: 'Gitee', url: v.gitee });
        if (sources.length === 0) {
            window.open('https://github.com/yunjii-cn/music/releases', '_blank');
            return;
        }

        var btn = document.getElementById('btnRaceDownload');
        var status = document.getElementById('downloadStatus');
        var btnText = document.getElementById('raceBtnText');
        if (btn) { btn.disabled = true; }
        if (btnText) { btnText.textContent = '测速中…'; }
        if (status) { status.textContent = '正在测试镜像延迟…'; }

        var timed = sources.map(function (s) {
            return new Promise(function (resolve) {
                var img = new Image();
                var start = performance.now();
                var done = false;
                var finish = function (ok) {
                    if (done) return; done = true;
                    resolve({ src: s, ok: ok, cost: performance.now() - start });
                };
                img.onload = function () { finish(true); };
                img.onerror = function () { finish(true); }; // HEAD 探测用图片不一定成功，error 也视为可达
                setTimeout(function () { finish(false); }, 4000);
                // 用HEAD探测：通过 fetch 不可行（CORS），用图片加载探测延迟
                img.src = s.url.split('?')[0] + '?_t=' + Date.now();
            });
        });

        Promise.all(timed).then(function (results) {
            results.sort(function (a, b) {
                if (a.ok !== b.ok) return a.ok ? -1 : 1;
                return a.cost - b.cost;
            });
            var best = results.find(function (r) { return r.ok; }) || results[0];
            if (status) {
                status.textContent = '已选用 ' + best.src.name + ' 镜像（' + Math.round(best.cost) + 'ms），开始下载…';
            }
            setTimeout(function () {
                window.location.href = best.src.url;
                if (btn) { btn.disabled = false; }
                if (btnText) { btnText.textContent = '一键竞速下载'; }
            }, 600);
        });
    }

    var raceBtn = document.getElementById('btnRaceDownload');
    if (raceBtn) raceBtn.addEventListener('click', raceDownload);

    function renderVersionHistory() {
        if (!releaseData) return;
        var list = document.getElementById('vhList');
        var count = document.getElementById('vhCount');
        if (!list) return;
        if (count) count.textContent = releaseData.versions.length;

        var html = '';
        releaseData.versions.slice(0, 12).forEach(function (v, i) {
            var links = [];
            if (v.github) links.push('<a href="' + v.github + '" target="_blank" rel="noopener" class="vh-link gh">GitHub</a>');
            if (v.gitee) links.push('<a href="' + v.gitee + '" target="_blank" rel="noopener" class="vh-link ge">Gitee</a>');
            var notes = v.notes ? '<p class="vh-notes">' + escapeHtml(v.notes) + '</p>' : '';
            var latestTag = (i === 0) ? '<span class="vh-latest">最新</span>' : '';
            html += '<div class="vh-item">' +
                        '<div class="vh-head">' +
                            '<span class="vh-ver">' + escapeHtml(v.version) + '</span>' +
                            latestTag +
                            '<span class="vh-date">' + escapeHtml(v.date) + '</span>' +
                        '</div>' +
                        notes +
                        '<div class="vh-links">' + links.join('') + '</div>' +
                    '</div>';
        });
        list.innerHTML = html;
    }

    function escapeHtml(s) {
        return String(s).replace(/[&<>"']/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c];
        });
    }

    var vhToggle = document.getElementById('vhToggle');
    var vhList = document.getElementById('vhList');
    if (vhToggle && vhList) {
        vhToggle.addEventListener('click', function () {
            var hidden = vhList.hasAttribute('hidden');
            if (hidden) {
                vhList.removeAttribute('hidden');
                vhToggle.classList.add('open');
            } else {
                vhList.setAttribute('hidden', '');
                vhToggle.classList.remove('open');
            }
        });
    }

    loadReleases();

    /* --- Hero 粒子画布 --- */
    var canvas = document.getElementById('particles');
    if (canvas && canvas.getContext) {
        var ctx = canvas.getContext('2d');
        var particles = [];
        var W, H, raf;
        var COLORS = ['rgba(139,92,246,', 'rgba(168,85,247,', 'rgba(236,72,153,'];

        function resize() {
            W = canvas.width = canvas.offsetWidth;
            H = canvas.height = canvas.offsetHeight;
            initParticles();
        }

        function initParticles() {
            var count = Math.min(70, Math.floor((W * H) / 16000));
            particles = [];
            for (var i = 0; i < count; i++) {
                particles.push({
                    x: Math.random() * W,
                    y: Math.random() * H,
                    r: Math.random() * 1.8 + 0.6,
                    vx: (Math.random() - 0.5) * 0.35,
                    vy: (Math.random() - 0.5) * 0.35,
                    a: Math.random() * 0.5 + 0.2,
                    c: COLORS[Math.floor(Math.random() * COLORS.length)]
                });
            }
        }

        function draw() {
            ctx.clearRect(0, 0, W, H);
            for (var i = 0; i < particles.length; i++) {
                var p = particles[i];
                p.x += p.vx;
                p.y += p.vy;
                if (p.x < 0 || p.x > W) p.vx *= -1;
                if (p.y < 0 || p.y > H) p.vy *= -1;
                ctx.beginPath();
                ctx.arc(p.x, p.y, p.r, 0, Math.PI * 2);
                ctx.fillStyle = p.c + p.a + ')';
                ctx.fill();
            }
            // 连线
            for (var j = 0; j < particles.length; j++) {
                for (var k = j + 1; k < particles.length; k++) {
                    var dx = particles[j].x - particles[k].x;
                    var dy = particles[j].y - particles[k].y;
                    var dist = dx * dx + dy * dy;
                    if (dist < 12000) {
                        var op = (1 - dist / 12000) * 0.12;
                        ctx.strokeStyle = 'rgba(139,92,246,' + op + ')';
                        ctx.lineWidth = 1;
                        ctx.beginPath();
                        ctx.moveTo(particles[j].x, particles[j].y);
                        ctx.lineTo(particles[k].x, particles[k].y);
                        ctx.stroke();
                    }
                }
            }
            raf = requestAnimationFrame(draw);
        }

        resize();
        window.addEventListener('resize', resize);
        // 仅在可见时运行，省电
        if (!document.hidden) draw();
        document.addEventListener('visibilitychange', function () {
            if (document.hidden) {
                cancelAnimationFrame(raf);
            } else {
                draw();
            }
        });
    }

    /* --- 产品展示切换 --- */
    var thumbs = document.querySelectorAll('#galleryThumbs .thumb');
    var screens = document.querySelectorAll('#galleryViewport .gallery-screen');
    thumbs.forEach(function (thumb) {
        thumb.addEventListener('click', function () {
            var idx = thumb.getAttribute('data-index');
            thumbs.forEach(function (t) { t.classList.remove('active'); });
            thumb.classList.add('active');
            screens.forEach(function (s) {
                s.classList.toggle('active', s.getAttribute('data-index') === idx);
            });
        });
    });

    /* --- 滚动淡入 --- */
    var fadeEls = document.querySelectorAll('.section, .feature-card, .adv-item, .tech-card, .shot-card, .timeline-item, .compare-wrap');
    fadeEls.forEach(function (el, i) {
        el.classList.add('fade-in');
        el.style.transitionDelay = (Math.min(i % 6, 5) * 0.05) + 's';
    });

    if ('IntersectionObserver' in window) {
        var io = new IntersectionObserver(function (entries) {
            entries.forEach(function (entry) {
                if (entry.isIntersecting) {
                    entry.target.classList.add('visible');
                    io.unobserve(entry.target);
                }
            });
        }, { threshold: 0.08 });
        fadeEls.forEach(function (el) { io.observe(el); });
    } else {
        fadeEls.forEach(function (el) { el.classList.add('visible'); });
    }
})();
