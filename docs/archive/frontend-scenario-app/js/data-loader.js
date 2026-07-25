/* ============================================================================
   data-loader.js — Fetches exported model results as static JSON.

   - Loads the scenario index (data/scenarios.json) once on first use.
   - Lazy-loads a per-scenario result file the first time it is selected.
   - Caches everything in memory for the lifetime of the page (no localStorage).

   Exposes a single global: window.DataLoader
   ============================================================================ */
(function (global) {
    'use strict';

    var DATA_DIR = 'data/';
    var SCENARIO_INDEX = DATA_DIR + 'scenarios.json';

    // In-memory caches. Cleared on full page reload, never persisted.
    var indexPromise = null;            // Promise<scenarioIndex>
    var scenarioCache = {};             // { [scenarioId]: Promise<scenarioData> }

    /**
     * Fetch JSON from a URL, rejecting on any non-2xx response.
     * @param {string} url
     * @returns {Promise<Object>}
     */
    function fetchJson(url) {
        return fetch(url).then(function (response) {
            if (!response.ok) {
                throw new Error('Failed to load ' + url + ' (HTTP ' + response.status + ')');
            }
            return response.json();
        });
    }

    /**
     * Load the scenario index. Cached after the first call so repeated
     * callers share one network request.
     * @returns {Promise<Object>} The parsed scenarios.json document.
     */
    function loadScenarioIndex() {
        if (!indexPromise) {
            indexPromise = fetchJson(SCENARIO_INDEX).catch(function (err) {
                // Reset so a later retry can attempt the fetch again.
                indexPromise = null;
                throw err;
            });
        }
        return indexPromise;
    }

    /**
     * Lazy-load the result file for a single scenario. Subsequent calls for
     * the same id resolve from the in-memory cache without re-fetching.
     * @param {string} scenarioId
     * @returns {Promise<Object>} The parsed per-scenario result document.
     */
    function loadScenario(scenarioId) {
        if (!scenarioId) {
            return Promise.reject(new Error('loadScenario requires a scenario id'));
        }
        if (!scenarioCache[scenarioId]) {
            var url = DATA_DIR + 'results/' + scenarioId + '.json';
            scenarioCache[scenarioId] = fetchJson(url).catch(function (err) {
                delete scenarioCache[scenarioId];
                throw err;
            });
        }
        return scenarioCache[scenarioId];
    }

    /**
     * Load the parameter citation registry (data/parameters.json).
     * Reuses the scenario cache slot keyed by a reserved id.
     * @returns {Promise<Object>}
     */
    function loadParameters() {
        if (!scenarioCache.__parameters__) {
            scenarioCache.__parameters__ = fetchJson(DATA_DIR + 'parameters.json')
                .catch(function (err) {
                    delete scenarioCache.__parameters__;
                    throw err;
                });
        }
        return scenarioCache.__parameters__;
    }

    /**
     * True when a scenario's result file is already resolved in memory.
     * @param {string} scenarioId
     * @returns {boolean}
     */
    function isCached(scenarioId) {
        return Object.prototype.hasOwnProperty.call(scenarioCache, scenarioId);
    }

    global.DataLoader = {
        loadScenarioIndex: loadScenarioIndex,
        loadScenario: loadScenario,
        loadParameters: loadParameters,
        isCached: isCached
    };

    // Kick off the index fetch immediately so it is warm by the time the
    // first page interaction needs it.
    if (global.document) {
        loadScenarioIndex().catch(function () { /* surfaced on explicit use */ });
    }
})(window);
