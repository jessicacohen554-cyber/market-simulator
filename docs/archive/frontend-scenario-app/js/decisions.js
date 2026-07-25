// ============================================================================
// Decisions tracker — open modeling choices from build-plan §5 ("Open Items to
// Resolve During Build"). Renders one collapsible section per domain; each
// decision has radio options plus a free-text notes field. Selections persist
// to localStorage under marketsim_decision_{id} and restore on load.
// ============================================================================
(function () {
    'use strict';

    var STORAGE_PREFIX = 'marketsim_decision_';

    // --- Decision catalogue -------------------------------------------------
    // Each decision: id, domain, title, question, options[{value,label,desc}],
    // defaultValue (the "Default If Unresolved" from the build plan), rationale.
    var DECISIONS = [
        {
            id: 'weather_year',
            domain: 'Calibration',
            title: 'Representative weather year',
            question: 'Which year from 2022–2025 anchors the base-case load and renewable profiles?',
            options: [
                { value: '2022', label: '2022', desc: 'Winter Storm Elliott; stressed ERCOT winter peak.' },
                { value: '2023', label: '2023', desc: 'Record summer demand across both ISOs.' },
                { value: '2024', label: '2024', desc: 'Most recent complete EIA-930 year.' },
                { value: '2025', label: '2025', desc: 'Partial year — would need synthetic fill.' }
            ],
            defaultValue: '2024',
            rationale: 'Build plan §5 default: use 2024 as the most recent complete year.'
        },
        {
            id: 'p10p50p90_method',
            domain: 'Calibration',
            title: 'P10 / P50 / P90 methodology',
            question: 'How are reported confidence bands computed from model runs?',
            options: [
                { value: 'ensemble_percentiles', label: 'Ensemble percentiles', desc: 'Empirical percentiles across the scenario ensemble.' },
                { value: 'analytic_normal', label: 'Analytic (normal)', desc: 'Mean ± z·σ assuming a normal output distribution.' },
                { value: 'bootstrap', label: 'Bootstrap resample', desc: 'Resample hourly residuals; recompute percentiles.' }
            ],
            defaultValue: 'ensemble_percentiles',
            rationale: 'Build plan §5 default: percentiles taken across the scenario ensemble.'
        },
        {
            id: 'calibration_target_year',
            domain: 'Calibration',
            title: 'Price-formation calibration target',
            question: 'Which historical year are simulated LMPs calibrated against?',
            options: [
                { value: '2022', label: '2022', desc: 'High and volatile gas prices.' },
                { value: '2023', label: '2023', desc: 'Normalising gas prices, strong renewable build.' },
                { value: '2024', label: '2024', desc: 'Aligns with the default weather year.' }
            ],
            defaultValue: '2024',
            rationale: 'Match the calibration target to the chosen weather year unless evidence says otherwise.'
        },
        {
            id: 'caiso_voll',
            domain: 'Reliability',
            title: 'CAISO value of lost load',
            question: 'What VOLL ($/MWh) prices unserved energy in CAISO?',
            options: [
                { value: '1000', label: '$1,000 / MWh', desc: 'Conservative lower bound used in some CPUC filings.' },
                { value: '2000', label: '$2,000 / MWh', desc: 'Closer to the CAISO administrative price cap.' }
            ],
            defaultValue: '2000',
            rationale: 'Build plan §5 default: $2,000, closer to the administrative cap.'
        },
        {
            id: 'ercot_scarcity_mechanism',
            domain: 'Reliability',
            title: 'ERCOT scarcity pricing mechanism',
            question: 'How is scarcity priced into ERCOT energy outcomes?',
            options: [
                { value: 'ordc_adder', label: 'ORDC adder', desc: 'Operating-reserve demand curve adder on top of dispatch price.' },
                { value: 'fixed_voll', label: 'Fixed VOLL', desc: 'Flat VOLL applied only on shortfall hours.' }
            ],
            defaultValue: 'ordc_adder',
            rationale: 'ORDC mirrors current ERCOT market design; fixed VOLL is the simpler fallback.'
        },
        {
            id: 'ercot_ttc_source',
            domain: 'Transmission',
            title: 'ERCOT inter-zonal TTC values',
            question: 'Where do ERCOT inter-zonal total transfer capability limits come from?',
            options: [
                { value: 'published_cdr', label: 'Published CDR estimates', desc: 'Planning estimates from ERCOT Capacity, Demand & Reserves reports.' },
                { value: 'custom_powerflow', label: 'Custom power-flow study', desc: 'Derive limits from an in-house power-flow model.' },
                { value: 'historical_flows', label: 'Historical observed flows', desc: 'Cap limits at observed historical inter-zonal flows.' }
            ],
            defaultValue: 'published_cdr',
            rationale: 'Build plan §5 default: use published CDR planning estimates.'
        },
        {
            id: 'caiso_import_curve',
            domain: 'Transmission',
            title: 'CAISO WECC import supply curve',
            question: 'How is the WECC-to-CAISO import supply curve specified?',
            options: [
                { value: 'three_step', label: '3-step approximation', desc: 'Three-tranche hand-set curve (hydro / CCGT / peaker).' },
                { value: 'four_tranche_placeholder', label: '4-tranche placeholder', desc: 'Current constants.py placeholder with four tranches.' },
                { value: 'eia930_fit', label: 'Empirical EIA-930 fit', desc: 'Fit tranches from EIA-930 interchange and price data.' }
            ],
            defaultValue: 'three_step',
            rationale: 'Build plan §5 default: use the 3-step approximation until an EIA-930 fit is available.'
        },
        {
            id: 'gas_price_default_path',
            domain: 'Fuel Prices',
            title: 'Default gas price path',
            question: 'Which gas price path is the headline base case?',
            options: [
                { value: 'low', label: 'Low', desc: 'EIA AEO 2024 low gas price path.' },
                { value: 'mid', label: 'Mid', desc: 'EIA AEO 2024 reference gas price path.' },
                { value: 'high', label: 'High', desc: 'EIA AEO 2024 high gas price path.' }
            ],
            defaultValue: 'mid',
            rationale: 'Mid path is the AEO reference case; low/high frame the sensitivity band.'
        },
        {
            id: 'gas_price_escalation_basis',
            domain: 'Fuel Prices',
            title: 'Gas price escalation basis',
            question: 'How does the real gas price escalate over the 2026–2050 horizon?',
            options: [
                { value: 'aeo2024', label: 'AEO 2024 (2%/yr real)', desc: 'Constant 2% annual real escalation per AEO 2024.' },
                { value: 'flat', label: 'Flat (no escalation)', desc: 'Hold the base-year real price constant.' },
                { value: 'futures_strip', label: 'Futures strip', desc: 'Anchor near-term years to the Henry Hub futures strip.' }
            ],
            defaultValue: 'aeo2024',
            rationale: 'Matches GAS_PRICE_ESCALATION in constants.py (2% real per AEO 2024).'
        },
        {
            id: 'new_entry_cost_learning',
            domain: 'Capacity Expansion',
            title: 'New-entry cost decline method',
            question: 'How do capital costs for new wind / solar / storage decline over time?',
            options: [
                { value: 'wrights_law', label: "Wright's Law", desc: 'Cost falls with cumulative global deployment (learning rate).' },
                { value: 'atb_trajectory', label: 'NREL ATB trajectory', desc: 'Use ATB year-by-year cost projections directly.' },
                { value: 'fixed', label: 'Fixed (no decline)', desc: 'Hold base-year capex constant — conservative bound.' }
            ],
            defaultValue: 'wrights_law',
            rationale: "Wright's Law ties cost decline to endogenous build, matching WRIGHT_REFERENCE_GW."
        },
        {
            id: 'queue_cap_enforcement',
            domain: 'Capacity Expansion',
            title: 'Interconnection queue cap enforcement',
            question: 'Which interconnection queue caps bind new entry each year?',
            options: [
                { value: 'iso_total_and_per_tech', label: 'ISO total + per-tech', desc: 'Both QUEUE_CAP_GW and QUEUE_CAP_PER_TECH_GW bind independently.' },
                { value: 'iso_total_only', label: 'ISO total only', desc: 'Only the aggregate ISO throughput cap binds.' },
                { value: 'none', label: 'No queue cap', desc: 'New entry limited only by economics — optimistic bound.' }
            ],
            defaultValue: 'iso_total_and_per_tech',
            rationale: 'Both caps exist in constants.py and are documented to bind independently.'
        },
        {
            id: 'carbon_price_default_path',
            domain: 'Policy',
            title: 'Default carbon price path',
            question: 'Which carbon price trajectory is the headline base case?',
            options: [
                { value: 'zero', label: 'Zero', desc: 'No explicit carbon price — current federal baseline.' },
                { value: 'low', label: 'Low', desc: 'RFF low path ($25/t by 2050).' },
                { value: 'mid', label: 'Mid', desc: 'RFF mid path ($50/t by 2050).' },
                { value: 'high', label: 'High', desc: 'RFF high path ($110/t by 2050).' }
            ],
            defaultValue: 'zero',
            rationale: 'Zero reflects current policy; priced paths are run as explicit sensitivities.'
        },
        {
            id: 'caiso_rps_treatment',
            domain: 'Policy',
            title: 'CAISO SB 100 enforcement',
            question: 'How is the CA SB 100 clean-energy floor enforced in dispatch / expansion?',
            options: [
                { value: 'hard_floor', label: 'Hard floor', desc: 'Clean share is a binding constraint each compliance year.' },
                { value: 'soft_penalty', label: 'Soft penalty', desc: 'Shortfall allowed at a penalty (alternative compliance price).' }
            ],
            defaultValue: 'hard_floor',
            rationale: 'STATE_RPS_FLOORS encodes SB 100 as a floor; a soft penalty better models slippage risk.'
        },
        {
            id: 'storage_deployment_pace',
            domain: 'Storage',
            title: 'Default storage deployment pace',
            question: 'Which base-year storage fleet sizing is the headline assumption?',
            options: [
                { value: 'low', label: 'Low (3 GW)', desc: 'Conservative STORAGE_BASE_FLEET_MW low case.' },
                { value: 'mid', label: 'Mid (8 GW)', desc: 'Reference STORAGE_BASE_FLEET_MW case.' },
                { value: 'high', label: 'High (20 GW)', desc: 'Aggressive STORAGE_BASE_FLEET_MW case.' }
            ],
            defaultValue: 'mid',
            rationale: 'Mid sizing is the NREL ATB reference; subsequent years grow via economics.'
        }
    ];

    // --- Persistence helpers ------------------------------------------------
    function storageKey(id) { return STORAGE_PREFIX + id; }

    /** Read a persisted decision record, or null if absent / unreadable. */
    function loadDecision(id) {
        try {
            var raw = window.localStorage.getItem(storageKey(id));
            if (!raw) { return null; }
            var rec = JSON.parse(raw);
            return (rec && typeof rec === 'object') ? rec : null;
        } catch (err) {
            console.warn('Could not read decision', id, err);
            return null;
        }
    }

    /** Persist {value, notes} for a decision; removes the key when both empty. */
    function saveDecision(id, value, notes) {
        try {
            if (!value && !notes) {
                window.localStorage.removeItem(storageKey(id));
            } else {
                window.localStorage.setItem(
                    storageKey(id),
                    JSON.stringify({ value: value || '', notes: notes || '' })
                );
            }
        } catch (err) {
            console.warn('Could not save decision', id, err);
        }
    }

    // --- Rendering ----------------------------------------------------------
    var domainOrder = [];
    DECISIONS.forEach(function (d) {
        if (domainOrder.indexOf(d.domain) === -1) { domainOrder.push(d.domain); }
    });

    function el(tag, className, text) {
        var node = document.createElement(tag);
        if (className) { node.className = className; }
        if (text != null) { node.textContent = text; }
        return node;
    }

    /** Build the DOM for a single decision and wire up persistence. */
    function renderDecision(decision) {
        var saved = loadDecision(decision.id) || {};

        var wrap = el('div', 'decision');
        wrap.dataset.decisionId = decision.id;

        var head = el('div', 'decision-head');
        head.appendChild(el('span', 'decision-title', decision.title));
        head.appendChild(el('span', 'decision-id', decision.id));
        var status = el('span', 'decision-status');
        head.appendChild(status);
        wrap.appendChild(head);

        wrap.appendChild(el('p', 'decision-question', decision.question));

        var list = el('div', 'option-list');
        var radioName = 'decision_' + decision.id;

        decision.options.forEach(function (opt) {
            var label = el('label', 'option');

            var input = document.createElement('input');
            input.type = 'radio';
            input.name = radioName;
            input.value = opt.value;
            if (saved.value === opt.value) { input.checked = true; }
            label.appendChild(input);

            var body = el('span', 'option-label');
            body.appendChild(document.createTextNode(opt.label));
            if (opt.value === decision.defaultValue) {
                body.appendChild(el('span', 'default-tag', '· default'));
            }
            if (opt.desc) { body.appendChild(el('span', 'option-desc', opt.desc)); }
            label.appendChild(body);

            input.addEventListener('change', function () {
                saveDecision(decision.id, input.value, notes.value);
                refreshStatus();
            });

            list.appendChild(label);
        });
        wrap.appendChild(list);

        var notesLabel = el('label', 'decision-notes-label', 'Notes / rationale');
        notesLabel.setAttribute('for', 'notes_' + decision.id);
        wrap.appendChild(notesLabel);

        var notes = document.createElement('textarea');
        notes.className = 'decision-notes';
        notes.id = 'notes_' + decision.id;
        notes.placeholder = 'Why this choice? Link evidence, caveats, follow-ups…';
        notes.value = saved.notes || '';
        notes.addEventListener('input', function () {
            var checked = list.querySelector('input:checked');
            saveDecision(decision.id, checked ? checked.value : '', notes.value);
            refreshStatus();
        });
        wrap.appendChild(notes);

        wrap.appendChild(el('p', 'decision-rationale', 'Guidance: ' + decision.rationale));

        function refreshStatus() {
            var resolved = !!list.querySelector('input:checked');
            status.textContent = resolved ? 'Resolved' : 'Open';
            status.className = 'decision-status decision-status--' +
                (resolved ? 'resolved' : 'open');
        }
        refreshStatus();

        return wrap;
    }

    /** Build a collapsible <details> section for one domain. */
    function renderDomain(domain) {
        var decisions = DECISIONS.filter(function (d) { return d.domain === domain; });

        var section = document.createElement('details');
        section.className = 'domain-section';
        section.open = true;

        var summary = document.createElement('summary');
        summary.appendChild(document.createTextNode(domain));
        summary.appendChild(el('span', 'domain-count',
            decisions.length + (decisions.length === 1 ? ' decision' : ' decisions')));
        section.appendChild(summary);

        var body = el('div', 'domain-body');
        decisions.forEach(function (d) { body.appendChild(renderDecision(d)); });
        section.appendChild(body);

        return section;
    }

    /** Update the "X of N resolved" pill. */
    function refreshProgress() {
        var resolved = DECISIONS.filter(function (d) {
            var rec = loadDecision(d.id);
            return rec && rec.value;
        }).length;
        var pill = document.getElementById('progress-pill');
        if (pill) {
            pill.innerHTML = '<strong>' + resolved + '</strong> of <strong>' +
                DECISIONS.length + '</strong> resolved';
        }
    }

    // --- Export -------------------------------------------------------------
    /** Assemble the current state of every decision into a plain object. */
    function buildExport() {
        return {
            exported_at: new Date().toISOString(),
            schema: 'marketsim_decisions/1.0',
            decisions: DECISIONS.map(function (d) {
                var rec = loadDecision(d.id) || {};
                return {
                    id: d.id,
                    domain: d.domain,
                    title: d.title,
                    selected: rec.value || null,
                    default: d.defaultValue,
                    resolved: !!rec.value,
                    notes: rec.notes || ''
                };
            })
        };
    }

    function showToast(message) {
        var toast = document.getElementById('toast');
        if (!toast) { return; }
        toast.textContent = message;
        toast.classList.add('is-visible');
        window.clearTimeout(showToast._timer);
        showToast._timer = window.setTimeout(function () {
            toast.classList.remove('is-visible');
        }, 2600);
    }

    /** Copy text to the clipboard, with a legacy execCommand fallback. */
    function copyToClipboard(text) {
        if (navigator.clipboard && navigator.clipboard.writeText) {
            return navigator.clipboard.writeText(text);
        }
        return new Promise(function (resolve, reject) {
            var ta = document.createElement('textarea');
            ta.value = text;
            ta.style.position = 'fixed';
            ta.style.opacity = '0';
            document.body.appendChild(ta);
            ta.select();
            var ok = false;
            try { ok = document.execCommand('copy'); } catch (err) { ok = false; }
            document.body.removeChild(ta);
            ok ? resolve() : reject(new Error('copy command failed'));
        });
    }

    // --- Bootstrap ----------------------------------------------------------
    function init() {
        var container = document.getElementById('decisions-root');
        if (!container) { return; }

        domainOrder.forEach(function (domain) {
            container.appendChild(renderDomain(domain));
        });
        refreshProgress();

        // Keep the progress pill live as selections change anywhere in the tree.
        container.addEventListener('change', refreshProgress);
        container.addEventListener('input', refreshProgress);

        var exportBtn = document.getElementById('export-btn');
        if (exportBtn) {
            exportBtn.addEventListener('click', function () {
                var json = JSON.stringify(buildExport(), null, 2);
                copyToClipboard(json).then(function () {
                    showToast('Decisions JSON copied to clipboard');
                }).catch(function (err) {
                    console.error(err);
                    showToast('Copy failed — see console for the JSON');
                    console.log(json);
                });
            });
        }

        var expandBtn = document.getElementById('expand-btn');
        if (expandBtn) {
            expandBtn.addEventListener('click', function () {
                var sections = container.querySelectorAll('.domain-section');
                var anyClosed = Array.prototype.some.call(sections, function (s) {
                    return !s.open;
                });
                Array.prototype.forEach.call(sections, function (s) {
                    s.open = anyClosed;
                });
                expandBtn.textContent = anyClosed ? 'Collapse all' : 'Expand all';
            });
        }
    }

    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', init);
    } else {
        init();
    }
})();
