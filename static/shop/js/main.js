// The Christmas Boutique - front-end interactions
// 1) AJAX "Add to cart" + cart badge bounce
// 2) Scroll-reveal on sections
// 3) A single orchestrated hero snowfall (respects prefers-reduced-motion)
// 4) Quantity stepper + basic form validation

function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
    return null;
}
const csrftoken = getCookie('csrftoken');
const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

function updateCartBadge(count) {
    const badge = document.querySelector('.cart-badge');
    if (!badge) return;
    badge.textContent = count;
    if (!prefersReducedMotion) {
        badge.classList.remove('bump');
        void badge.offsetWidth; // restart animation
        badge.classList.add('bump');
    }
}

function showToast(message) {
    const region = document.querySelector('.toast-region');
    if (!region) return;
    const toast = document.createElement('div');
    toast.className = 'toast';
    toast.textContent = message;
    region.appendChild(toast);
    window.setTimeout(() => {
        toast.classList.add('is-leaving');
        toast.addEventListener('animationend', () => toast.remove(), { once: true });
    }, 2800);
}

// --- Mobile navigation ---
(function initNavigation() {
    const toggle = document.querySelector('.nav-toggle');
    const navigation = document.getElementById('primary-navigation');
    if (!toggle || !navigation) return;

    function setOpen(open) {
        toggle.setAttribute('aria-expanded', String(open));
        navigation.classList.toggle('is-open', open);
    }

    toggle.addEventListener('click', () => {
        setOpen(toggle.getAttribute('aria-expanded') !== 'true');
    });
    navigation.addEventListener('click', (event) => {
        if (event.target.closest('a')) setOpen(false);
    });
    document.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') setOpen(false);
    });
})();

// --- Reading progress ---
(function initReadingProgress() {
    const progress = document.querySelector('.scroll-indicator span');
    if (!progress) return;
    let scheduled = false;

    function update() {
        const scrollable = document.documentElement.scrollHeight - window.innerHeight;
        progress.style.transform = `scaleX(${scrollable > 0 ? window.scrollY / scrollable : 0})`;
        scheduled = false;
    }

    window.addEventListener('scroll', () => {
        if (scheduled) return;
        scheduled = true;
        window.requestAnimationFrame(update);
    }, { passive: true });
    update();
})();

// --- Add to cart ---
document.addEventListener('click', function (e) {
    const btn = e.target.closest('[data-add-to-cart-url]');
    if (!btn) return;
    e.preventDefault();

    const url = btn.getAttribute('data-add-to-cart-url');
    const scope = btn.closest('.product-actions, form') || document;
    const qtyInput = scope.querySelector('[data-qty]');
    const quantity = qtyInput ? qtyInput.value : 1;

    fetch(url, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrftoken,
            'X-Requested-With': 'XMLHttpRequest',
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `quantity=${encodeURIComponent(quantity)}`,
    })
        .then((res) => res.json())
        .then((data) => {
            updateCartBadge(data.cart_count);
            showToast(`Added ${btn.dataset.productName || 'item'} to your bag.`);
            const original = btn.dataset.originalLabel || btn.textContent;
            btn.textContent = 'Added ✓';
            btn.disabled = true;
            setTimeout(() => { btn.textContent = original; btn.disabled = false; }, 1300);
        })
        .catch(() => { showToast('We could not add that just now. Please try again.'); });
});

document.querySelectorAll('[data-add-to-cart-url]').forEach((btn) => {
    btn.dataset.originalLabel = btn.textContent;
});

// --- Quantity stepper ---
document.addEventListener('click', function (e) {
    const step = e.target.closest('[data-qty-step]');
    if (!step) return;
    const input = step.parentElement.querySelector('[data-qty]');
    if (!input) return;
    const max = parseInt(input.getAttribute('max') || '99', 10);
    const delta = parseInt(step.getAttribute('data-qty-step'), 10);
    const next = Math.min(max, Math.max(1, parseInt(input.value || '1', 10) + delta));
    input.value = next;
});

// --- Form validation feedback ---
document.querySelectorAll('form[data-validate]').forEach((form) => {
    form.addEventListener('submit', function (e) {
        const required = form.querySelectorAll('[required]');
        let valid = true;
        required.forEach((field) => {
            if (!field.value.trim()) {
                valid = false;
                field.style.borderColor = '#7A1F2B';
            } else {
                field.style.borderColor = '';
            }
        });
        if (!valid) e.preventDefault();
    });
});

// --- Scroll reveal (single, deliberate: sections fade/slide up once) ---
(function initReveal() {
    const targets = document.querySelectorAll('[data-reveal]');
    if (!targets.length) return;

    if (prefersReducedMotion || !('IntersectionObserver' in window)) {
        targets.forEach((el) => el.classList.add('is-visible'));
        return;
    }

    const observer = new IntersectionObserver((entries) => {
        entries.forEach((entry) => {
            if (entry.isIntersecting) {
                entry.target.classList.add('is-visible');
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.15, rootMargin: '0px 0px -40px 0px' });

    targets.forEach((el, i) => {
        el.style.setProperty('--i', i % 8);
        observer.observe(el);
    });
})();

// --- Hero snowfall: one quiet, continuous canvas animation ---
(function initSnow() {
    const canvas = document.querySelector('.hero-canvas');
    if (!canvas || prefersReducedMotion) return;

    const ctx = canvas.getContext('2d');
    let width, height, flakes;

    function resize() {
        const rect = canvas.parentElement.getBoundingClientRect();
        width = canvas.width = rect.width;
        height = canvas.height = rect.height;
    }

    function makeFlakes() {
        const count = Math.min(70, Math.floor(width / 14));
        flakes = Array.from({ length: count }, () => ({
            x: Math.random() * width,
            y: Math.random() * height,
            r: Math.random() * 2 + 0.6,
            speed: Math.random() * 0.6 + 0.25,
            drift: Math.random() * 0.6 - 0.3,
            opacity: Math.random() * 0.5 + 0.35,
        }));
    }

    let animationFrame;

    function tick() {
        ctx.clearRect(0, 0, width, height);
        ctx.fillStyle = '#fff';
        for (const f of flakes) {
            ctx.globalAlpha = f.opacity;
            ctx.beginPath();
            ctx.arc(f.x, f.y, f.r, 0, Math.PI * 2);
            ctx.fill();
            f.y += f.speed;
            f.x += f.drift;
            if (f.y > height) { f.y = -4; f.x = Math.random() * width; }
        }
        ctx.globalAlpha = 1;
        animationFrame = requestAnimationFrame(tick);
    }

    resize();
    makeFlakes();
    tick();
    window.addEventListener('resize', () => { resize(); makeFlakes(); });
    document.addEventListener('visibilitychange', () => {
        if (document.hidden) {
            cancelAnimationFrame(animationFrame);
        } else {
            tick();
        }
    });
})();
