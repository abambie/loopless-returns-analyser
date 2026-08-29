/* ── Auto-scroll dropdown menus into view when they open ─────────────────── */
(function () {
    if (window._looplessObserver) return;

    window._looplessObserver = new MutationObserver(function (mutations) {
        for (var i = 0; i < mutations.length; i++) {
            var added = mutations[i].addedNodes;
            for (var j = 0; j < added.length; j++) {
                var node = added[j];
                if (
                    node.nodeType === 1 &&
                    node.classList &&
                    node.classList.contains('Select-menu-outer')
                ) {
                    (function (el) {
                        setTimeout(function () {
                            el.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
                        }, 30);
                    })(node);
                }
            }
        }
    });

    window._looplessObserver.observe(document.body, {
        childList: true,
        subtree: true,
    });
})();


/* ── Scroll spy: highlight button for the most-visible panel ─────────────── */
(function () {
    if (window._looplessScrollSpy) return;
    window._looplessScrollSpy = true;

    var TABS = ['trend', 'breakdown', 'deepdive'];
    var _active = null;

    function setActive(name) {
        if (name === _active) return;
        _active = name;
        TABS.forEach(function (t) {
            var btn = document.getElementById('tab-btn-' + t);
            if (btn) btn.className = t === name ? 'dash-tab-btn active' : 'dash-tab-btn';
        });
    }

    function updateActive() {
        var vh = window.innerHeight;
        var best = null, bestPx = 0;
        TABS.forEach(function (t) {
            var el = document.getElementById('tab-panel-' + t);
            if (!el) return;
            var r = el.getBoundingClientRect();
            var visible = Math.max(0, Math.min(vh, r.bottom) - Math.max(0, r.top));
            if (visible > bestPx) { bestPx = visible; best = t; }
        });
        if (best && bestPx > 20) setActive(best);
    }

    window.addEventListener('scroll', updateActive, { passive: true });

    /* Re-run whenever Dash re-renders the page */
    new MutationObserver(function () {
        _active = null; // reset so setActive fires even if name unchanged
        updateActive();
    }).observe(document.body, { childList: true, subtree: true });
})();


/* ── Click a View button → set it active immediately + scroll to panel ───── */
(function () {
    if (window._looplessPanelScroll) return;
    window._looplessPanelScroll = true;

    var TABS = ['trend', 'breakdown', 'deepdive'];

    function setActive(name) {
        TABS.forEach(function (t) {
            var btn = document.getElementById('tab-btn-' + t);
            if (btn) btn.className = t === name ? 'dash-tab-btn active' : 'dash-tab-btn';
        });
    }

    document.addEventListener('click', function (e) {
        var btn = e.target.closest('.dash-tab-btn');
        if (!btn || !btn.id) return;

        var tab      = btn.id.replace('tab-btn-', '');
        var panelId  = 'tab-panel-' + tab;

        setActive(tab);

        setTimeout(function () {
            var panel = document.getElementById(panelId);
            if (panel) panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
        }, 60);
    });
})();
