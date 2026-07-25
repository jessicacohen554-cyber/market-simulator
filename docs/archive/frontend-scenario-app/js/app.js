/* ============================================================================
   app.js — Minimal app state + multi-page navigation.

   The frontend is three static pages (index / decisions / parameters), so
   "routing" here means: detect which page is loaded, mark the matching nav
   link active, and hold the user's current selections while that page is
   open. State lives in memory only — it does not persist across navigation.

   Exposes a single global: window.App
   ============================================================================ */
(function (global) {
    'use strict';

    // The three pages the nav bar links between.
    var PAGES = ['index', 'decisions', 'parameters'];

    /**
     * Derive the current page name from the document filename.
     * Falls back to 'index' for '/' or unknown paths.
     * @returns {string} One of PAGES.
     */
    function detectPage() {
        var file = (global.location.pathname.split('/').pop() || '').toLowerCase();
        var name = file.replace(/\.html?$/, '');
        if (name === '' ) { return 'index'; }
        return PAGES.indexOf(name) !== -1 ? name : 'index';
    }

    // Shared application state for the lifetime of this page.
    var state = {
        currentPage: detectPage(),
        selectedScenario: null,   // scenario id, set once results are chosen
        selectedYear: null        // integer model year, e.g. 2035
    };

    // Listeners notified whenever state changes, keyed by state field.
    var listeners = { selectedScenario: [], selectedYear: [] };

    /**
     * Subscribe to changes of a single state field.
     * @param {string} field 'selectedScenario' | 'selectedYear'
     * @param {Function} callback Invoked with the new value.
     */
    function on(field, callback) {
        if (listeners[field]) { listeners[field].push(callback); }
    }

    function emit(field, value) {
        (listeners[field] || []).forEach(function (cb) {
            try { cb(value); } catch (err) { console.error(err); }
        });
    }

    /**
     * Set the active scenario and notify subscribers if it changed.
     * @param {string} scenarioId
     */
    function setScenario(scenarioId) {
        if (state.selectedScenario === scenarioId) { return; }
        state.selectedScenario = scenarioId;
        emit('selectedScenario', scenarioId);
    }

    /**
     * Set the active model year and notify subscribers if it changed.
     * @param {number} year
     */
    function setYear(year) {
        var value = year == null ? null : parseInt(year, 10);
        if (state.selectedYear === value) { return; }
        state.selectedYear = value;
        emit('selectedYear', value);
    }

    /**
     * Navigate to one of the three pages.
     * @param {string} page One of PAGES.
     */
    function goTo(page) {
        if (PAGES.indexOf(page) === -1) { return; }
        global.location.href = page + '.html';
    }

    /**
     * Mark the nav link matching the current page as active. Looks for
     * anchors carrying a data-page attribute inside any .nav element.
     */
    function highlightNav() {
        var links = global.document.querySelectorAll('.nav-link[data-page]');
        Array.prototype.forEach.call(links, function (link) {
            link.classList.toggle('active', link.getAttribute('data-page') === state.currentPage);
        });
    }

    global.App = {
        PAGES: PAGES,
        state: state,
        on: on,
        setScenario: setScenario,
        setYear: setYear,
        goTo: goTo,
        highlightNav: highlightNav
    };

    if (global.document) {
        global.document.addEventListener('DOMContentLoaded', highlightNav);
    }
})(window);
