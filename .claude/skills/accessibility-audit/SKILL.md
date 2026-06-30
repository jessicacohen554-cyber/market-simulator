---
name: accessibility-audit
description: Audit the codebase-site for text readability, color contrast, and accessibility issues. Checks all HTML pages and CSS files for WCAG AA violations — dark text on dark backgrounds, light text on light backgrounds, missing dark-section overrides, low-contrast badges/labels, and mobile readability regressions. Use when the user says "check accessibility", "audit readability", "fix contrast", "can't read the text", or reports text visibility problems on the site.
---

# Codebase-site accessibility & readability audit

Audit the static documentation site at `docs/codebase-site/` for text
readability, color contrast, and WCAG AA compliance. The site uses a
section-level light/dark rhythm (`.section-light` / `.section-dark`) with
no global dark-mode toggle.

## Site structure

- **CSS design system:** `docs/codebase-site/css/shared.css` — tokens, layout,
  section-level light/dark theming
- **Page-specific CSS:** `docs/codebase-site/css/site.css` — figure components,
  code blocks, equations, breadcrumbs, buttons
- **HTML pages (11):** `index.html` + 10 sub-pages (`mental-model.html`,
  `data-pipeline.html`, `fleet-offer-curves.html`, `lp-core.html`,
  `solving-pricing.html`, `network.html`, `capacity-evolution.html`,
  `policy-scarcity.html`, `results-calibration.html`, `config-reference.html`)
- **Inline `<style>` blocks:** several pages define page-specific styles in
  `<head>` (fleet-offer-curves, network, etc.)

## Color system

The site defines color tokens in `:root` (shared.css):
- Surfaces: `--bg-page: #F8F9FC`, `--navy: #1A2744`, `--navy-dark: #0F1A2E`
- Text: `--text-primary: #000000`, `--text-secondary: #1E293B`,
  `--text-muted: #566370`, `--text-on-dark: #FFFFFF`,
  `--text-muted-dark: rgba(255,255,255,0.70)`
- WCAG-safe text: `--hydro-text`, `--green-text`, `--amber-text`, etc.

### Dark section convention

`.section-dark` applies `color: #fff` and sets heading/paragraph overrides:
```css
.section-dark h2, .section-dark h3, .section-dark h4 { color: #fff; }
.section-dark p, .section-dark li { color: rgba(255,255,255,0.80); }
```

**The root cause of most contrast bugs:** components styled with light-theme
tokens (`--text-primary`, `--text-secondary`, `--text-muted`) that appear
inside `.section-dark` without an override. These resolve to black/dark grey
on a navy background — nearly invisible.

## Audit checklist

For each page, check EVERY element that could appear inside `.section-dark`:

1. **Figure titles** (`.fig__title`) — uses `--text-primary` (#000), needs
   dark override to `#fff`
2. **Figure captions** (`.fig__caption`) — uses `--text-muted` (#566370),
   needs dark override
3. **Figure labels** (`.fig__label`) — same issue
4. **Chart legends** (`.legend-item`, `.chart-legend`) — check both inline
   and CSS-defined colors
5. **Code blocks** — inline `<code>` and `.code-block` in dark sections
6. **Badges / chips** (`.badge-fuel`, `.iso-btn`) — check text-on-background
   contrast ratios
7. **Table cells** (`.data-table th`, `.data-table td`) — if tables appear
   in dark sections
8. **Insight / callout boxes** — `.insight-box`, `.emphasis-callout`
9. **Inline styles** — `style="color:..."` that override the cascade
10. **SVG text / D3 labels** — chart axis labels, tick marks, annotations
    rendered by JavaScript
11. **Form elements** — `<select>`, `<input>` in dark sections
12. **Breadcrumb** text colors in different sections
13. **Tooltip** text and backgrounds
14. **Section headers** (`.section-header__title`) — the small eyebrow text

### WCAG AA contrast requirements
- Normal text (< 18pt / < 14pt bold): **4.5:1** minimum
- Large text (≥ 18pt / ≥ 14pt bold): **3:1** minimum
- UI components and graphical objects: **3:1** minimum

### Contrast calculation shortcut
On a `#1A2744` (navy) background:
- `#000000` → ~1.4:1 (FAIL)
- `#566370` → ~2.3:1 (FAIL)
- `#1E293B` → ~1.2:1 (FAIL)
- `rgba(255,255,255,0.50)` → ~5.5:1 (PASS for large text only)
- `rgba(255,255,255,0.70)` → ~8.5:1 (PASS)
- `rgba(255,255,255,0.80)` → ~10.5:1 (PASS)
- `#FFFFFF` → ~13.5:1 (PASS)

## Fix pattern

For CSS-level fixes, add `.section-dark` overrides in the appropriate
stylesheet:

```css
/* In site.css or shared.css */
.section-dark .fig__title { color: #fff; }
.section-dark .fig__caption { color: rgba(255,255,255,0.60); }
.section-dark .fig__label { color: rgba(255,255,255,0.50); }
.section-dark .legend-item { color: rgba(255,255,255,0.60); }
```

For inline-style issues in HTML, either:
- Remove the inline style and let the CSS cascade handle it
- Add a class that has proper dark-section overrides

For D3/JS-rendered SVG text, check the JavaScript files in `docs/codebase-site/js/`
for hardcoded colors that don't adapt to section background.

## Output

Report findings grouped by severity:
1. **Critical** — text completely unreadable (contrast < 2:1)
2. **High** — text hard to read (contrast 2:1 – 3:1)
3. **Medium** — text strained to read (contrast 3:1 – 4.5:1)
4. **Low** — technically passes AA but inconsistent with design intent

For each finding: file, line, element, current colors, contrast ratio, fix.
Apply all Critical and High fixes directly. Ask before applying Medium/Low.
