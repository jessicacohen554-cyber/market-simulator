/**
 * viz-holdout-tiers.js — Interactive three-tier holdout timeline
 * Used on: model-validity.html
 *
 * Renders the 2018–2030 year-by-year holdout tier ladder from
 * data/holdout-tiers.json (CLAUDE.md rule 22 / holdout-policy-memo-2026-07).
 * The visual job is to make ONE distinction unmistakable: the iterable
 * validation tier (2022 — you may go back and re-tune against it) versus the
 * touch-once locked tier (2019 + H1-2026 — scored exactly once, never
 * re-entered into tuning). Locked cells are sealed (solid heavy border +
 * lock); the validation cell is an open loop (dashed animated border + cycle).
 *
 * Plain IIFE (no D3 / no module imports) — pure DOM + CSS so it degrades
 * gracefully and stays responsive without a redraw handler. All .ht-* styles
 * live in model-validity.html's <style> block.
 */
(function () {
  'use strict';

  // Tier → presentation. Colors are the page's design tokens; each tier gets a
  // glyph and a one-word discipline that the cell and legend both surface.
  var TIER_META = {
    data:       { label: 'Data',        color: '#566370', glyph: '▤', disc: 'intake only', order: 0 },
    train:      { label: 'Train',       color: '#0369A1', glyph: '✎', disc: 'tuned',       order: 1 },
    validation: { label: 'Validation',  color: '#B45309', glyph: '↺', disc: 'iterable',    order: 2 },
    locked:     { label: 'Locked test', color: '#6366F1', glyph: '🔒', disc: 'touch once',  order: 3 },
    forecast:   { label: 'Forecast',    color: '#0F766E', glyph: '→', disc: 'forward',     order: 4 }
  };

  // Human label for a year cell — the locked H1-2026 cell reads "H1 2026".
  function yearLabel(rec) {
    if (rec.span === 'H1-2026') return 'H1 2026';
    return String(rec.year);
  }

  function tierMeta(tier) {
    return TIER_META[tier] || { label: tier, color: '#566370', glyph: '•', disc: '', order: 9 };
  }

  document.addEventListener('DOMContentLoaded', init);

  function init() {
    var container = document.getElementById('holdout-tiers-viz');
    if (!container) return;

    fetch('data/holdout-tiers.json')
      .then(function (r) {
        if (!r.ok) throw new Error('HTTP ' + r.status);
        return r.json();
      })
      .then(function (data) { render(container, data); })
      .catch(function (err) {
        container.innerHTML =
          '<p class="ht-error" role="alert">Timeline data unavailable (' +
          String(err.message || err) + '). See <code>data/holdout-tiers.json</code>.</p>';
      });
  }

  function render(container, data) {
    var years = Array.isArray(data.years) ? data.years : [];
    var tierNotes = data.tiers || {};

    container.innerHTML = '';

    // ---- Legend: one chip per tier, in ladder order ----------------------
    var legend = document.createElement('div');
    legend.className = 'ht-legend';
    legend.setAttribute('role', 'list');
    legend.setAttribute('aria-label', 'Holdout tier key');
    Object.keys(TIER_META)
      .sort(function (a, b) { return TIER_META[a].order - TIER_META[b].order; })
      .forEach(function (tier) {
        var m = TIER_META[tier];
        var chip = document.createElement('div');
        chip.className = 'ht-legend__chip ht-tier--' + tier;
        chip.setAttribute('role', 'listitem');
        chip.style.setProperty('--ht-c', m.color);
        chip.innerHTML =
          '<span class="ht-legend__swatch" aria-hidden="true"></span>' +
          '<span class="ht-legend__name">' + m.label + '</span>' +
          '<span class="ht-legend__disc">' + m.disc + '</span>';
        legend.appendChild(chip);
      });
    container.appendChild(legend);

    // ---- Timeline strip (horizontal scroll on narrow viewports) ----------
    var scroll = document.createElement('div');
    scroll.className = 'ht-scroll';
    var strip = document.createElement('div');
    strip.className = 'ht-timeline';
    strip.setAttribute('role', 'list');
    strip.setAttribute('aria-label', 'Year-by-year holdout tiers, 2018 to 2030');

    var cells = [];
    years.forEach(function (rec) {
      var tier = rec.tier;
      var m = tierMeta(tier);
      var flags = rec.flags || [];
      var isCrossover = flags.indexOf('crossover-overlap-roadmap') !== -1;
      var isHorizonStart = flags.indexOf('forecast-horizon-start') !== -1;

      var cell = document.createElement('button');
      cell.type = 'button';
      cell.className = 'ht-cell ht-tier--' + tier +
        (rec.scored ? ' is-scored' : '') +
        (isCrossover ? ' is-crossover' : '');
      cell.style.setProperty('--ht-c', m.color);
      cell.setAttribute('role', 'listitem');
      cell.setAttribute('data-year', String(rec.year));
      cell.setAttribute('aria-label',
        yearLabel(rec) + ' — ' + m.label + ' tier (' + m.disc + ')' +
        (rec.scored ? ', scored' : ''));

      var dualNote = isHorizonStart
        ? '<span class="ht-cell__dual" title="H1-2026 locked test AND forecast-horizon start">＋forecast</span>'
        : (isCrossover ? '<span class="ht-cell__dual" title="Roadmap dual-mode overlap year (not implemented)">◇ roadmap</span>' : '');

      cell.innerHTML =
        '<span class="ht-cell__year">' + yearLabel(rec) + '</span>' +
        '<span class="ht-cell__glyph" aria-hidden="true">' + m.glyph + '</span>' +
        '<span class="ht-cell__tier">' + m.label + '</span>' +
        '<span class="ht-cell__disc">' + m.disc + '</span>' +
        dualNote +
        (rec.scored ? '<span class="ht-cell__scored" aria-hidden="true">scored&nbsp;×1</span>' : '');

      cell.addEventListener('click', function () { select(rec); });
      strip.appendChild(cell);
      cells.push({ el: cell, rec: rec });
    });

    scroll.appendChild(strip);
    container.appendChild(scroll);

    // ---- Detail panel ----------------------------------------------------
    var detail = document.createElement('div');
    detail.className = 'ht-detail';
    detail.id = 'ht-detail';
    detail.setAttribute('aria-live', 'polite');
    detail.innerHTML = '<p class="ht-detail__prompt">Select a year to read its tier and the discipline that governs it.</p>';
    container.appendChild(detail);

    // ---- Discipline contrast: iterable vs touch-once ---------------------
    var contrast = document.createElement('div');
    contrast.className = 'ht-contrast';
    contrast.innerHTML =
      '<div class="ht-contrast__card ht-tier--validation" style="--ht-c:' + TIER_META.validation.color + '">' +
        '<div class="ht-contrast__head"><span class="ht-contrast__glyph">↺</span> Iterable — validation (2022)</div>' +
        '<p>Solve the frozen keeper, score it, and <strong>a miss may send you back</strong> to re-tune 2023–2025 and re-solve. That is its purpose: model selection. Because it is iterated against, a 2022 number is <strong>selection evidence, never a certified out-of-sample skill number</strong>.</p>' +
      '</div>' +
      '<div class="ht-contrast__card ht-tier--locked" style="--ht-c:' + TIER_META.locked.color + '">' +
        '<div class="ht-contrast__head"><span class="ht-contrast__glyph">🔒</span> Touch-once — locked test (2019 + H1-2026)</div>' +
        '<p>Scored <strong>exactly once</strong> per ISO with the frozen config; the number is recorded whatever it is. <strong>No calibration change may respond to it</strong> without designating a new never-touched year. 2019 is the honest out-of-sample number precisely because it is never iterated against.</p>' +
      '</div>';
    container.appendChild(contrast);

    function select(rec) {
      var m = tierMeta(rec.tier);
      cells.forEach(function (c) {
        c.el.classList.toggle('is-active', c.rec.year === rec.year);
      });
      var flags = rec.flags || [];
      var flagHTML = flags.length
        ? '<div class="ht-detail__flags">' + flags.map(function (f) {
            return '<span class="ht-flag">' + f + '</span>';
          }).join('') + '</div>'
        : '';
      detail.innerHTML =
        '<div class="ht-detail__card ht-tier--' + rec.tier + '">' +
          '<div class="ht-detail__head">' +
            '<span class="ht-detail__badge">' + m.glyph + ' ' + m.label + '</span>' +
            '<span class="ht-detail__year">' + yearLabel(rec) + '</span>' +
            '<span class="ht-detail__disc">' + m.disc + '</span>' +
          '</div>' +
          '<p class="ht-detail__tiernote">' + (tierNotes[rec.tier] || '') + '</p>' +
          (rec.note ? '<p class="ht-detail__yearnote">' + rec.note + '</p>' : '') +
          flagHTML +
        '</div>';
    }
  }
})();
