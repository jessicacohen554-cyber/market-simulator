/* ============================================================================
   charts.js — Plotly renderers for the Scenario Results Dashboard.

   Reads the per-scenario result document exported by
   scripts/export_results.py. That document has the shape:

     { cache_key, iso, config, years: { "2026": <summary>, ... } }

   where each <summary> carries:
     generation_twh { fuel: TWh }, capacity_gw { fuel: GW },
     emissions_mt, nox_tonnes, so2_tonnes, avg_price, peak_price,
     curtailment_twh, storage_cycles
     (nox_tonnes/so2_tonnes are secondary reporting pollutants -- CO2 stays
     the primary scored metric -- and are absent from exports older than
     W3-E2)

   Resource colors are pulled live from the CSS custom properties in
   css/style.css so the charts and the HTML legend never drift apart.

   Exposes a single global: window.Charts
   ============================================================================ */
(function (global) {
    'use strict';

    // Export fuel key -> CSS custom property holding its canonical color.
    var FUEL_TOKEN = {
        nuclear: '--nuclear',
        coal: '--coal',
        gas_cc: '--gas-cc',
        gas_ct: '--gas-ct',
        hydro: '--hydro',
        wind: '--wind',
        solar: '--solar',
        storage: '--storage'
    };

    // Stacking + legend order: baseload at the bottom, variable on top.
    var FUEL_ORDER = [
        'nuclear', 'coal', 'gas_cc', 'gas_ct',
        'hydro', 'wind', 'solar', 'storage', 'import'
    ];

    var FUEL_LABEL = {
        gas_cc: 'Gas CC', gas_ct: 'Gas CT', coal: 'Coal', nuclear: 'Nuclear',
        wind: 'Wind', solar: 'Solar', hydro: 'Hydro', storage: 'Storage',
        'import': 'Import'
    };

    var FALLBACK_COLOR = '#9AA5B1';

    // Hourly-price fields renderPriceDuration will accept, in priority order.
    var PRICE_FIELDS = ['price_duration', 'prices', 'lmp_hourly', 'hourly_lmp'];

    var CHART_IDS = {
        generationMix: 'chart-generation-mix',
        emissions: 'chart-emissions',
        priceDuration: 'chart-price-duration',
        capacity: 'chart-capacity-mix'
    };

    var PLOT_CONFIG = { responsive: true, displayModeBar: false };

    /* ----------------------------------------------------------------------
       Color + style helpers
       ---------------------------------------------------------------------- */

    /** Resolve a CSS custom property to its trimmed computed value. */
    function cssVar(name) {
        var v = global.getComputedStyle(document.documentElement)
            .getPropertyValue(name);
        return v ? v.trim() : '';
    }

    /** Canonical color for a fuel key, falling back to a neutral grey. */
    function fuelColor(fuel) {
        var token = FUEL_TOKEN[fuel];
        return (token && cssVar(token)) || FALLBACK_COLOR;
    }

    /** Human-readable label for a fuel key. */
    function fuelLabel(fuel) {
        return FUEL_LABEL[fuel] || fuel;
    }

    /** Convert a #rrggbb / #rgb hex string to an rgba() string. */
    function hexToRgba(hex, alpha) {
        var h = (hex || '').replace('#', '');
        if (h.length === 3) {
            h = h[0] + h[0] + h[1] + h[1] + h[2] + h[2];
        }
        var n = parseInt(h, 16);
        if (h.length !== 6 || isNaN(n)) {
            return hex || 'rgba(0,0,0,' + alpha + ')';
        }
        return 'rgba(' + ((n >> 16) & 255) + ',' + ((n >> 8) & 255) +
            ',' + (n & 255) + ',' + alpha + ')';
    }

    /** Shared base layout; `extra` is merged on top. */
    function baseLayout(extra) {
        var layout = {
            autosize: true,
            margin: { l: 64, r: 24, t: 16, b: 56 },
            paper_bgcolor: 'rgba(0,0,0,0)',
            plot_bgcolor: 'rgba(0,0,0,0)',
            font: {
                family: cssVar('--font-body') || 'sans-serif',
                size: 12,
                color: cssVar('--ink') || '#1F2933'
            },
            xaxis: { gridcolor: cssVar('--border') || '#DCE2E8', zeroline: false },
            yaxis: { gridcolor: cssVar('--border') || '#DCE2E8', zeroline: false },
            legend: { orientation: 'h', y: -0.22, x: 0 },
            hoverlabel: { font: { family: cssVar('--font-body') || 'sans-serif' } }
        };
        return mergeDeep(layout, extra || {});
    }

    /** Shallow-recursive merge of plain objects (target is mutated). */
    function mergeDeep(target, source) {
        Object.keys(source).forEach(function (key) {
            var val = source[key];
            if (val && typeof val === 'object' && !Array.isArray(val) &&
                target[key] && typeof target[key] === 'object') {
                mergeDeep(target[key], val);
            } else {
                target[key] = val;
            }
        });
        return target;
    }

    /* ----------------------------------------------------------------------
       Container-state helpers
       ---------------------------------------------------------------------- */

    function escapeHtml(s) {
        return String(s).replace(/[&<>"]/g, function (c) {
            return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c];
        });
    }

    /** Replace a chart container's content with a placeholder message. */
    function placeholder(id, title, detail) {
        var el = document.getElementById(id);
        if (!el) { return null; }
        if (global.Plotly) { global.Plotly.purge(el); }
        el.innerHTML = '<div class="chart-placeholder"><strong>' +
            escapeHtml(title) + '</strong><span>' +
            escapeHtml(detail) + '</span></div>';
        return null;
    }

    /** Draw (or re-draw) a Plotly figure into a container by id. */
    function draw(id, traces, layout) {
        var el = document.getElementById(id);
        if (!el) { return; }
        if (!global.Plotly) {
            placeholder(id, 'Plotly unavailable', 'The charting library failed to load.');
            return;
        }
        // Drop any loading/empty placeholder so it does not bleed through
        // the plot — Plotly.react leaves foreign child nodes in place.
        var stale = el.querySelector('.chart-placeholder');
        if (stale) { el.removeChild(stale); }
        global.Plotly.react(el, traces, layout, PLOT_CONFIG);
    }

    /* ----------------------------------------------------------------------
       Data accessors
       ---------------------------------------------------------------------- */

    /** Sorted numeric list of model years present in a result document. */
    function yearKeys(data) {
        if (!data || !data.years) { return []; }
        return Object.keys(data.years)
            .map(Number)
            .filter(function (y) { return !isNaN(y); })
            .sort(function (a, b) { return a - b; });
    }

    /**
     * Ordered list of fuels appearing in a per-year sub-field across all
     * years — FUEL_ORDER first, then any unrecognized fuels alphabetically.
     */
    function fuelsIn(data, field) {
        var seen = {};
        yearKeys(data).forEach(function (y) {
            var bucket = data.years[String(y)][field] || {};
            Object.keys(bucket).forEach(function (f) { seen[f] = true; });
        });
        var ordered = FUEL_ORDER.filter(function (f) { return seen[f]; });
        Object.keys(seen).sort().forEach(function (f) {
            if (ordered.indexOf(f) === -1) { ordered.push(f); }
        });
        return ordered;
    }

    /** Pull an hourly price series for a year, or null when none is exported. */
    function priceSeries(data, year) {
        var summary = data && data.years && data.years[String(year)];
        if (!summary) { return null; }
        for (var i = 0; i < PRICE_FIELDS.length; i++) {
            var raw = summary[PRICE_FIELDS[i]];
            if (Array.isArray(raw) && raw.length) {
                return [{ name: data.iso || 'LMP', values: raw.slice() }];
            }
            if (raw && typeof raw === 'object') {
                var zones = Object.keys(raw).filter(function (z) {
                    return Array.isArray(raw[z]) && raw[z].length;
                });
                if (zones.length) {
                    return zones.map(function (z) {
                        return { name: z, values: raw[z].slice() };
                    });
                }
            }
        }
        return null;
    }

    /* ----------------------------------------------------------------------
       Chart renderers
       ---------------------------------------------------------------------- */

    /**
     * Stacked-area generation mix across the full model horizon.
     * @param {Object} data Per-scenario result document.
     */
    function renderGenerationMix(data) {
        var years = yearKeys(data);
        if (!years.length) {
            return placeholder(CHART_IDS.generationMix,
                'No generation data', 'This scenario exported no annual results.');
        }
        var fuels = fuelsIn(data, 'generation_twh');
        var traces = fuels.map(function (fuel) {
            var color = fuelColor(fuel);
            return {
                type: 'scatter',
                mode: 'lines',
                name: fuelLabel(fuel),
                stackgroup: 'gen',
                x: years,
                y: years.map(function (y) {
                    return data.years[String(y)].generation_twh[fuel] || 0;
                }),
                line: { width: 1, color: color },
                fillcolor: hexToRgba(color, 0.78),
                hovertemplate: '%{y:.1f} TWh<extra>' + fuelLabel(fuel) + '</extra>'
            };
        });
        draw(CHART_IDS.generationMix, traces, baseLayout({
            yaxis: { title: { text: 'Generation (TWh)' }, rangemode: 'tozero' },
            xaxis: { title: { text: 'Model year' }, dtick: 4 },
            hovermode: 'x unified'
        }));
    }

    /**
     * Annual CO2 (primary) plus NOx/SO2 (secondary, reporting-only) emissions
     * trajectory across the model horizon.
     * @param {Object} data Per-scenario result document.
     */
    function renderEmissions(data) {
        var years = yearKeys(data);
        if (!years.length) {
            return placeholder(CHART_IDS.emissions,
                'No emissions data', 'This scenario exported no annual results.');
        }
        var accent = cssVar('--danger') || '#E74C3C';
        var co2Trace = {
            type: 'scatter',
            mode: 'lines+markers',
            name: 'CO₂ (Mt)',
            x: years,
            y: years.map(function (y) {
                return data.years[String(y)].emissions_mt;
            }),
            line: { width: 2.5, color: accent, shape: 'spline' },
            marker: { size: 6, color: accent },
            fill: 'tozeroy',
            fillcolor: hexToRgba(accent, 0.12),
            hovertemplate: '%{x}: %{y:.1f} Mt CO₂<extra></extra>'
        };
        var traces = [co2Trace];
        // NOx/SO2 are secondary reporting pollutants -- CO2 stays the primary
        // scored metric -- plotted on a separate axis since their tonnage is
        // orders of magnitude smaller. Older exports carry no nox_tonnes/
        // so2_tonnes field, so those traces are simply omitted.
        if (data.years[String(years[0])].nox_tonnes !== undefined) {
            var noxColor = cssVar('--warning') || '#F1C40F';
            traces.push({
                type: 'scatter',
                mode: 'lines+markers',
                name: 'NOx (tons)',
                yaxis: 'y2',
                x: years,
                y: years.map(function (y) {
                    return data.years[String(y)].nox_tonnes;
                }),
                line: { width: 1.5, color: noxColor, dash: 'dot' },
                marker: { size: 4, color: noxColor },
                hovertemplate: '%{x}: %{y:.1f} tons NOx<extra></extra>'
            });
        }
        if (data.years[String(years[0])].so2_tonnes !== undefined) {
            var so2Color = cssVar('--ink-muted') || '#647184';
            traces.push({
                type: 'scatter',
                mode: 'lines+markers',
                name: 'SO₂ (tons)',
                yaxis: 'y2',
                x: years,
                y: years.map(function (y) {
                    return data.years[String(y)].so2_tonnes;
                }),
                line: { width: 1.5, color: so2Color, dash: 'dot' },
                marker: { size: 4, color: so2Color },
                hovertemplate: '%{x}: %{y:.1f} tons SO₂<extra></extra>'
            });
        }
        draw(CHART_IDS.emissions, traces, baseLayout({
            yaxis: { title: { text: 'CO₂ (Mt)' }, rangemode: 'tozero' },
            yaxis2: {
                title: { text: 'NOx / SO₂ (tons)' },
                overlaying: 'y',
                side: 'right',
                rangemode: 'tozero',
                showgrid: false
            },
            xaxis: { title: { text: 'Model year' }, dtick: 4 },
            showlegend: traces.length > 1
        }));
    }

    /**
     * Price duration curve — hourly LMPs sorted high-to-low — for one year.
     * @param {Object} data Per-scenario result document.
     * @param {number} year Selected model year.
     */
    function renderPriceDuration(data, year) {
        var series = priceSeries(data, year);
        if (!series) {
            var summary = data && data.years && data.years[String(year)];
            var detail = summary
                ? 'This export carries only annual price summaries (avg ' +
                  summary.avg_price + ', peak ' + summary.peak_price +
                  ' $/MWh) — hourly LMPs are needed for a duration curve.'
                : 'No results exported for ' + year + '.';
            return placeholder(CHART_IDS.priceDuration,
                'No hourly price data', detail);
        }
        var traces = series.map(function (s, i) {
            var sorted = s.values.slice().sort(function (a, b) { return b - a; });
            var n = sorted.length;
            var color = i === 0
                ? (cssVar('--accent-deep') || '#2F6FB3')
                : fuelColor(FUEL_ORDER[i % FUEL_ORDER.length]);
            return {
                type: 'scatter',
                mode: 'lines',
                name: s.name,
                x: sorted.map(function (_, h) {
                    return n > 1 ? (h / (n - 1)) * 100 : 0;
                }),
                y: sorted,
                line: { width: 2, color: color },
                hovertemplate: '%{y:.1f} $/MWh at %{x:.0f}% of hours' +
                    '<extra>' + s.name + '</extra>'
            };
        });
        draw(CHART_IDS.priceDuration, traces, baseLayout({
            yaxis: { title: { text: 'LMP ($/MWh)' }, rangemode: 'tozero' },
            xaxis: {
                title: { text: 'Share of hours (%) — ' + year },
                range: [0, 100]
            },
            showlegend: series.length > 1
        }));
    }

    /**
     * Installed capacity by resource for one year, as a colored bar chart.
     * @param {Object} data Per-scenario result document.
     * @param {number} year Selected model year.
     */
    function renderCapacity(data, year) {
        var summary = data && data.years && data.years[String(year)];
        if (!summary || !summary.capacity_gw) {
            return placeholder(CHART_IDS.capacity,
                'No capacity data', 'No results exported for ' + year + '.');
        }
        var capacity = summary.capacity_gw;
        var fuels = FUEL_ORDER.filter(function (f) {
            return Object.prototype.hasOwnProperty.call(capacity, f);
        });
        Object.keys(capacity).sort().forEach(function (f) {
            if (fuels.indexOf(f) === -1) { fuels.push(f); }
        });
        var trace = {
            type: 'bar',
            x: fuels.map(fuelLabel),
            y: fuels.map(function (f) { return capacity[f] || 0; }),
            marker: {
                color: fuels.map(fuelColor),
                line: { width: 0 }
            },
            hovertemplate: '%{x}: %{y:.1f} GW<extra></extra>'
        };
        draw(CHART_IDS.capacity, [trace], baseLayout({
            yaxis: { title: { text: 'Capacity (GW)' }, rangemode: 'tozero' },
            xaxis: { title: { text: 'Resource — ' + year } },
            showlegend: false,
            bargap: 0.35
        }));
    }

    /* ----------------------------------------------------------------------
       Bulk-state helpers used by the page bootstrap
       ---------------------------------------------------------------------- */

    /** Show the same placeholder message in every chart container. */
    function placeholderAll(title, detail) {
        Object.keys(CHART_IDS).forEach(function (k) {
            placeholder(CHART_IDS[k], title, detail);
        });
    }

    /** Show a loading placeholder in every chart container. */
    function loadingAll() {
        placeholderAll('Loading…', 'Fetching scenario results.');
    }

    global.Charts = {
        renderGenerationMix: renderGenerationMix,
        renderEmissions: renderEmissions,
        renderPriceDuration: renderPriceDuration,
        renderCapacity: renderCapacity,
        placeholderAll: placeholderAll,
        loadingAll: loadingAll,
        fuelColor: fuelColor
    };
})(window);
