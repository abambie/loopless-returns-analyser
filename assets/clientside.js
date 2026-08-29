/* ───────────────────────────────────────────────────────────────────────────
 * clientside.js
 * ───────────────────────────────────────────────────────────────────────────
 * All browser-side JavaScript callbacks for the Loopless dashboard.
 *
 * In Dash, "clientside callbacks" are JS functions that run in the browser
 * instead of round-tripping to the Python server. Putting them in this file
 * (auto-loaded by Dash from /assets) keeps app.py free of inline JS strings
 * and makes the JS easy to read, edit, and debug from browser dev-tools.
 *
 * Callbacks defined below (referenced from app.py via "loopless.<name>"):
 *   • pageTransition      Slide-in fill bar + fade overlay between routes
 *   • formatDate          Auto-insert hyphens in YYYY-MM-DD inputs
 *   • validateDateRange   Cross-validate "from" must be ≤ "to" on Apply
 *   • showToast           Open the success toast when Apply is clicked
 *   • riskBtnLoading      Disable + spin the "Analyse" button while training
 *   • riskBtnReveal       Reveal the result cards once training finishes
 *   • exportPdf           Open the browser's print dialog from the modal
 * ───────────────────────────────────────────────────────────────────────── */

window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.loopless = {

    /* ── Page transition animation ──────────────────────────────────────── */
    pageTransition: function(pathname) {
        var overlay = document.getElementById('page-transition-overlay');
        var bar     = document.getElementById('nav-bar-fill');
        if (!overlay || !bar) return window.dash_clientside.no_update;

        bar.style.transition = 'none';
        bar.style.width = '0%';
        overlay.style.display = 'flex';
        overlay.style.opacity  = '1';

        requestAnimationFrame(function() {
            requestAnimationFrame(function() {
                bar.style.transition = 'width 0.35s cubic-bezier(0.4, 0, 0.2, 1)';
                bar.style.width = '100%';
            });
        });

        setTimeout(function() {
            overlay.style.transition = 'opacity 0.18s ease';
            overlay.style.opacity = '0';
            setTimeout(function() {
                overlay.style.display = 'none';
                overlay.style.opacity = '1';
                overlay.style.transition = '';
                bar.style.transition = 'none';
                bar.style.width = '0%';
            }, 190);
        }, 400);

        return window.dash_clientside.no_update;
    },

    /* ── Date input auto-format (YYYY-MM-DD) ────────────────────────────── */
    formatDate: function(val) {
        if (!val) return [val, {}];
        var digits = val.replace(/[^0-9]/g, '');
        digits = digits.slice(0, 8);
        var out = digits;
        if (digits.length > 4) out = digits.slice(0,4) + '-' + digits.slice(4);
        if (digits.length > 6) out = digits.slice(0,4) + '-' + digits.slice(4,6) + '-' + digits.slice(6);
        var style = {};
        if (digits.length === 8) {
            var d = new Date(out);
            var valid = !isNaN(d.getTime()) && out.length === 10;
            style = valid ? {borderColor: '#10b981'} : {borderColor: '#ec4899'};
        }
        return [out, style];
    },

    /* ── Cross-field date validation (from ≤ to) ────────────────────────── */
    validateDateRange: function(n, from_val, to_val, from_style, to_style) {
        if (!n) return '';
        var errors = [];
        var fromFilled = from_val && from_val.length > 0;
        var toFilled   = to_val   && to_val.length   > 0;
        if (fromFilled && (!from_style || from_style.borderColor === '#ec4899')) {
            errors.push('⚠ Start date is invalid — please use YYYY-MM-DD format (e.g. 2024-01-15).');
        }
        if (toFilled && (!to_style || to_style.borderColor === '#ec4899')) {
            errors.push('⚠ End date is invalid — please use YYYY-MM-DD format (e.g. 2024-12-31).');
        }
        if (fromFilled && toFilled && from_val.length === 10 && to_val.length === 10
                && (!from_style || from_style.borderColor !== '#ec4899')
                && (!to_style   || to_style.borderColor   !== '#ec4899')) {
            if (from_val > to_val) {
                errors.push('⚠ Start date must be earlier than the end date.');
            }
        }
        return errors.join('  ');
    },

    /* ── Show success toast on Apply ────────────────────────────────────── */
    showToast: function(n) {
        if (!n) return false;
        return true;
    },

    /* ── Risk page: disable + spin button while training ────────────────── */
    riskBtnLoading: function(n) {
        var nu = window.dash_clientside.no_update;
        if (!n) return [nu, nu];
        return ['risk-btn-scale hero loading', true];
    },

    /* ── Risk page: reveal result cards after training completes ────────── */
    riskBtnReveal: function(msg) {
        var nu = window.dash_clientside.no_update;
        if (!msg) return [nu, nu, nu, nu];
        return ['risk-btn-wrap normal', 'risk-btn-scale normal', {display: 'block'}, false];
    },

    /* ── PDF export: open browser print dialog ──────────────────────────── */
    exportPdf: function(n) {
        if (n) { window.print(); }
        return window.dash_clientside.no_update;
    },

};
