/**
 * nav.js — Top navigation injector for Codebase Explorer
 * Injects a sticky top nav into <nav id="topNav"> on every page.
 * Pattern matches the CFE optimizer nav.js implementation.
 */

(function () {
  'use strict';

  const NAV_ITEMS = [
    {
      label: 'Home',
      href: 'index.html',
    },
    {
      label: 'Foundations',
      dropdown: [
        { label: 'Mental Model',        href: 'mental-model.html',       num: '①' },
        { label: 'Data Pipeline',        href: 'data-pipeline.html',      num: '②' },
        { label: 'Fleet & Offer Curves', href: 'fleet-offer-curves.html', num: '③' },
      ],
    },
    {
      label: 'The Engine',
      dropdown: [
        { label: 'LP Core',          href: 'lp-core.html',       num: '④' },
        { label: 'Solving & Pricing', href: 'solving-pricing.html', num: '⑤' },
        { label: 'The Network',       href: 'network.html',        num: '⑥' },
      ],
    },
    {
      label: 'Evolution & Policy',
      dropdown: [
        { label: 'Capacity Evolution',     href: 'capacity-evolution.html',  num: '⑦' },
        { label: 'Policy & Scarcity',      href: 'policy-scarcity.html',     num: '⑧' },
        { label: 'Results & Calibration',  href: 'results-calibration.html', num: '⑨' },
      ],
    },
    {
      label: 'Backcast',
      dropdown: [
        { label: 'Run Explorer',        href: 'backcast-runs.html',     num: '&#9881;' },
        { label: 'Calibration Status',   href: 'calibration-status.html', num: '&#9678;' },
        { label: 'Calibration Rubric',   href: 'calibration-rubric.html', num: '&#9878;' },
        { label: 'Model Validity',       href: 'model-validity.html',     num: '&#8982;' },
        { label: 'Forecast Validation',  href: 'forecast-validation.html', num: '&#9873;' },
        { label: 'Data Completeness',    href: 'data-completeness.html',  num: '&#9745;' },
      ],
    },
    {
      label: 'Forecast',
      dropdown: [
        { label: 'Forecast Bands', href: 'forecast-bands.html', num: '&#8767;' },
      ],
    },
    {
      label: 'Reference',
      href: 'config-reference.html',
    },
  ];

  /** Returns the current page filename. */
  function currentPage() {
    const parts = window.location.pathname.split('/');
    return parts[parts.length - 1] || 'index.html';
  }

  /** Returns true if the item matches the current page. */
  function isActive(href) {
    const cur = currentPage();
    return cur === href || (cur === '' && href === 'index.html');
  }

  /** Returns true if any child in dropdown matches the current page. */
  function hasActiveChild(dropdown) {
    return dropdown.some(item => isActive(item.href));
  }

  /** Chevron SVG icon. */
  function chevronSVG() {
    return `<svg class="chevron" viewBox="0 0 12 12" fill="none" aria-hidden="true">
      <path d="M2 4l4 4 4-4" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round"/>
    </svg>`;
  }

  /** Logo SVG — simplified lightning bolt. */
  function logoSVG() {
    return `<svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
      <path d="M11 2L4 11h7l-2 7 9-10h-7l2-8z" fill="#0EA5E9" stroke="#0EA5E9" stroke-width="0.5" stroke-linejoin="round"/>
    </svg>`;
  }

  function buildNav() {
    const cur = currentPage();
    let html = `
      <div class="top-nav__inner">
        <a class="top-nav__logo" href="index.html" aria-label="Codebase Explorer home">
          ${logoSVG()}
          Codebase Explorer
        </a>
        <div class="top-nav__links" role="menubar" aria-label="Main navigation">
    `;

    NAV_ITEMS.forEach((item, idx) => {
      if (item.dropdown) {
        const active = hasActiveChild(item.dropdown);
        html += `
          <div class="top-nav__dropdown${active ? ' has-active' : ''}" role="none" data-dropdown="${idx}">
            <button
              class="top-nav__dropdown-btn${active ? ' active' : ''}"
              aria-haspopup="true"
              aria-expanded="false"
              aria-controls="dropdown-menu-${idx}"
              role="menuitem"
            >
              ${item.label} ${chevronSVG()}
            </button>
            <div class="top-nav__dropdown-menu" id="dropdown-menu-${idx}" role="menu">
        `;
        item.dropdown.forEach(child => {
          const childActive = isActive(child.href);
          html += `
              <a class="top-nav__dropdown-item${childActive ? ' active' : ''}"
                 href="${child.href}" role="menuitem"
                 ${childActive ? 'aria-current="page"' : ''}>
                <span aria-hidden="true" style="opacity:0.5;margin-right:6px">${child.num}</span>${child.label}
              </a>`;
        });
        html += `</div></div>`;
      } else {
        const active = isActive(item.href);
        html += `
          <a class="top-nav__link${active ? ' active' : ''}"
             href="${item.href}" role="menuitem"
             ${active ? 'aria-current="page"' : ''}>
            ${item.label}
          </a>`;
      }
    });

    html += `
        </div>
        <button class="top-nav__hamburger" aria-label="Open navigation menu" aria-expanded="false" aria-controls="mobileMenu">
          <span></span><span></span><span></span>
        </button>
      </div>
    `;

    // Mobile menu
    html += buildMobileMenu(cur);

    return html;
  }

  function buildMobileMenu(cur) {
    let html = `<div class="top-nav__mobile-menu" id="mobileMenu" aria-label="Mobile navigation">`;

    NAV_ITEMS.forEach(item => {
      if (item.dropdown) {
        html += `<span class="top-nav__mobile-section-label">${item.label}</span>`;
        item.dropdown.forEach(child => {
          const active = isActive(child.href);
          html += `
            <a class="top-nav__mobile-item${active ? ' active' : ''}"
               href="${child.href}" ${active ? 'aria-current="page"' : ''}>
              <span aria-hidden="true" style="opacity:0.5;margin-right:8px">${child.num}</span>${child.label}
            </a>`;
        });
      } else {
        const active = isActive(item.href);
        html += `
          <span class="top-nav__mobile-section-label">Navigation</span>
          <a class="top-nav__mobile-item${active ? ' active' : ''}"
             href="${item.href}" ${active ? 'aria-current="page"' : ''}>
            ${item.label}
          </a>`;
      }
    });

    html += `</div>`;
    return html;
  }

  function attachEvents(nav) {
    // Desktop dropdowns — click to open/close (accessible)
    const dropdowns = nav.querySelectorAll('.top-nav__dropdown');
    dropdowns.forEach(dd => {
      const btn = dd.querySelector('.top-nav__dropdown-btn');
      const menu = dd.querySelector('.top-nav__dropdown-menu');

      btn.addEventListener('click', (e) => {
        e.stopPropagation();
        const isOpen = dd.classList.contains('open');
        // Close all
        dropdowns.forEach(d => {
          d.classList.remove('open');
          d.querySelector('.top-nav__dropdown-btn').setAttribute('aria-expanded', 'false');
        });
        if (!isOpen) {
          dd.classList.add('open');
          btn.setAttribute('aria-expanded', 'true');
        }
      });

      // Keyboard: Escape closes
      menu.addEventListener('keydown', (e) => {
        if (e.key === 'Escape') {
          dd.classList.remove('open');
          btn.setAttribute('aria-expanded', 'false');
          btn.focus();
        }
      });
    });

    // Click outside closes all dropdowns
    document.addEventListener('click', () => {
      dropdowns.forEach(dd => {
        dd.classList.remove('open');
        const btn = dd.querySelector('.top-nav__dropdown-btn');
        if (btn) btn.setAttribute('aria-expanded', 'false');
      });
    });

    // Hamburger toggle
    const hamburger = nav.querySelector('.top-nav__hamburger');
    const mobileMenu = nav.querySelector('.top-nav__mobile-menu');

    if (hamburger && mobileMenu) {
      hamburger.addEventListener('click', () => {
        const open = mobileMenu.classList.toggle('open');
        hamburger.setAttribute('aria-expanded', open ? 'true' : 'false');
        // Animate hamburger lines
        const spans = hamburger.querySelectorAll('span');
        if (open) {
          spans[0].style.transform = 'translateY(7px) rotate(45deg)';
          spans[1].style.opacity = '0';
          spans[2].style.transform = 'translateY(-7px) rotate(-45deg)';
        } else {
          spans[0].style.transform = '';
          spans[1].style.opacity = '';
          spans[2].style.transform = '';
        }
      });
    }
  }

  function init() {
    let nav = document.getElementById('topNav');
    if (!nav) {
      nav = document.createElement('nav');
      nav.id = 'topNav';
      document.body.insertBefore(nav, document.body.firstChild);
    }
    nav.className = 'top-nav';
    nav.setAttribute('role', 'navigation');
    nav.setAttribute('aria-label', 'Site navigation');
    nav.innerHTML = buildNav();
    attachEvents(nav);
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
