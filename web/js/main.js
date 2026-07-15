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
