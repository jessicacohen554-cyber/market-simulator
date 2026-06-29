/**
 * shared.js — Codebase Explorer shared page utilities
 *
 * 1. Auto-builds floating right-rail mini-TOC from <h2>/<h3> inside <main>
 * 2. Highlights the currently-visible heading via IntersectionObserver
 * 3. Initialises GSAP ScrollTrigger for .story-section and .narrative-card
 * 4. Respects prefers-reduced-motion — disables all GSAP animations
 */

(function () {
  'use strict';

  const REDUCED_MOTION = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------------------------------------------------------------------------
     1. Mini-TOC Builder
     --------------------------------------------------------------------------- */

  function buildTOC() {
    const rail = document.querySelector('.toc-rail');
    if (!rail) return;

    const main = document.querySelector('main');
    if (!main) return;

    const headings = Array.from(main.querySelectorAll('h2, h3'));
    if (!headings.length) {
      rail.style.display = 'none';
      return;
    }

    // Ensure every heading has an id for anchor linking
    const slugCounts = {};
    headings.forEach(h => {
      if (!h.id) {
        let slug = h.textContent.trim()
          .toLowerCase()
          .replace(/[^a-z0-9]+/g, '-')
          .replace(/^-|-$/g, '');
        if (slugCounts[slug] !== undefined) {
          slugCounts[slug]++;
          slug = `${slug}-${slugCounts[slug]}`;
        } else {
          slugCounts[slug] = 0;
        }
        h.id = slug;
      }
    });

    // Build TOC HTML
    let listHTML = '';
    headings.forEach(h => {
      const isH3 = h.tagName === 'H3';
      const label = h.textContent.trim();
      listHTML += `
        <li class="toc-rail__item">
          <a class="toc-rail__link${isH3 ? ' toc-rail__link--h3' : ''}"
             href="#${h.id}"
             data-toc-id="${h.id}">${label}</a>
        </li>`;
    });

    rail.innerHTML = `
      <div class="toc-rail__title">On this page</div>
      <ul class="toc-rail__list">${listHTML}</ul>`;

    // Smooth scroll on click (accessibility: also works for keyboard Enter)
    rail.querySelectorAll('.toc-rail__link').forEach(link => {
      link.addEventListener('click', e => {
        e.preventDefault();
        const target = document.getElementById(link.dataset.tocId);
        if (target) {
          target.scrollIntoView({ behavior: REDUCED_MOTION ? 'auto' : 'smooth', block: 'start' });
          // Brief focus for screen readers
          target.setAttribute('tabindex', '-1');
          target.focus({ preventScroll: true });
        }
      });
    });

    observeHeadings(headings, rail);
  }

  /* ---------------------------------------------------------------------------
     2. Heading Intersection Observer (active highlight)
     --------------------------------------------------------------------------- */

  function observeHeadings(headings, rail) {
    if (!('IntersectionObserver' in window)) return;

    let activeId = null;

    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        const link = rail.querySelector(`[data-toc-id="${entry.target.id}"]`);
        if (!link) return;

        if (entry.isIntersecting) {
          // Set this heading as active if it's higher up (lower index) than current
          const headingIdx = headings.indexOf(entry.target);
          const curIdx = activeId ? headings.indexOf(document.getElementById(activeId)) : Infinity;

          if (headingIdx <= curIdx) {
            if (activeId) {
              const prev = rail.querySelector(`[data-toc-id="${activeId}"]`);
              if (prev) prev.classList.remove('active');
            }
            link.classList.add('active');
            activeId = entry.target.id;
          }
        } else {
          // Only deactivate if this was the active one
          if (entry.target.id === activeId) {
            link.classList.remove('active');
            activeId = null;

            // Find the nearest heading above the viewport to keep highlighted
            const scrollTop = window.scrollY;
            let best = null;
            headings.forEach(h => {
              if (h.getBoundingClientRect().top + scrollTop < scrollTop + 120) {
                best = h;
              }
            });
            if (best) {
              const newLink = rail.querySelector(`[data-toc-id="${best.id}"]`);
              if (newLink) {
                newLink.classList.add('active');
                activeId = best.id;
              }
            }
          }
        }
      });
    }, {
      rootMargin: '-80px 0px -60% 0px',
      threshold: 0,
    });

    headings.forEach(h => obs.observe(h));
  }

  /* ---------------------------------------------------------------------------
     3. GSAP Scroll Animations
     --------------------------------------------------------------------------- */

  function initGSAP() {
    if (REDUCED_MOTION) {
      // Make all animated elements immediately visible
      document.querySelectorAll('.story-section, .narrative-card').forEach(el => {
        el.classList.add('visible');
        el.style.opacity = '1';
        el.style.transform = 'none';
      });
      return;
    }

    // Check GSAP is available
    if (typeof gsap === 'undefined' || typeof ScrollTrigger === 'undefined') {
      // Fallback: use IntersectionObserver for CSS-class-based animations
      fallbackScrollAnimations();
      return;
    }

    gsap.registerPlugin(ScrollTrigger);

    // Animate .story-section elements
    gsap.utils.toArray('.story-section').forEach((el, i) => {
      gsap.fromTo(el,
        { opacity: 0, y: 30 },
        {
          opacity: 1,
          y: 0,
          duration: 0.65,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: el,
            start: 'top 85%',
            toggleActions: 'play none none none',
          },
        }
      );
    });

    // Animate .narrative-card elements (staggered if multiple in a row)
    const cardGroups = {};
    document.querySelectorAll('.narrative-card').forEach(card => {
      const parent = card.parentElement;
      const key = parent ? parent.id || parent.className : 'root';
      if (!cardGroups[key]) cardGroups[key] = [];
      cardGroups[key].push(card);
    });

    Object.values(cardGroups).forEach(cards => {
      cards.forEach((card, idx) => {
        gsap.fromTo(card,
          { opacity: 0, y: 32 },
          {
            opacity: 1,
            y: 0,
            duration: 0.60,
            delay: idx * 0.10,
            ease: 'power2.out',
            scrollTrigger: {
              trigger: card,
              start: 'top 88%',
              toggleActions: 'play none none none',
            },
          }
        );
      });
    });

    // Animate .headline-card in grid (staggered)
    const headlineCards = document.querySelectorAll('.headline-card, .stat-card');
    if (headlineCards.length) {
      gsap.fromTo(headlineCards,
        { opacity: 0, y: 20 },
        {
          opacity: 1,
          y: 0,
          duration: 0.50,
          stagger: 0.08,
          ease: 'power2.out',
          scrollTrigger: {
            trigger: headlineCards[0].parentElement,
            start: 'top 85%',
            toggleActions: 'play none none none',
          },
        }
      );
    }
  }

  /** IntersectionObserver fallback when GSAP is not loaded. */
  function fallbackScrollAnimations() {
    if (!('IntersectionObserver' in window)) {
      document.querySelectorAll('.story-section, .narrative-card').forEach(el => {
        el.classList.add('visible');
      });
      return;
    }

    const obs = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('visible');
          obs.unobserve(entry.target);
        }
      });
    }, { threshold: 0.12 });

    document.querySelectorAll('.story-section, .narrative-card').forEach(el => {
      obs.observe(el);
    });
  }

  /* ---------------------------------------------------------------------------
     4. Tab Component Initialisation
     --------------------------------------------------------------------------- */

  function initTabs() {
    document.querySelectorAll('.tabs').forEach(tabsEl => {
      const tabs = tabsEl.querySelectorAll('.tabs__tab');
      const panels = tabsEl.querySelectorAll('.tabs__panel');

      tabs.forEach((tab, idx) => {
        tab.addEventListener('click', () => {
          tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
          panels.forEach(p => p.classList.remove('active'));
          tab.classList.add('active');
          tab.setAttribute('aria-selected', 'true');
          if (panels[idx]) panels[idx].classList.add('active');
        });
      });
    });
  }

  /* ---------------------------------------------------------------------------
     5. Initialise expandable .fig panels
     --------------------------------------------------------------------------- */

  function initFigExpand() {
    document.querySelectorAll('.fig__expand-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const fig = btn.closest('.fig');
        if (!fig) return;
        const expanded = fig.classList.toggle('fig--expanded');
        btn.setAttribute('aria-expanded', expanded ? 'true' : 'false');
        btn.textContent = expanded ? '✕ Close' : '⤢ Expand';
        if (expanded) {
          document.body.style.overflow = 'hidden';
          document.addEventListener('keydown', closeOnEscape);
        } else {
          document.body.style.overflow = '';
          document.removeEventListener('keydown', closeOnEscape);
        }
      });
    });

    function closeOnEscape(e) {
      if (e.key === 'Escape') {
        document.querySelectorAll('.fig--expanded').forEach(fig => {
          fig.classList.remove('fig--expanded');
          const btn = fig.querySelector('.fig__expand-btn');
          if (btn) {
            btn.setAttribute('aria-expanded', 'false');
            btn.textContent = '⤢ Expand';
          }
        });
        document.body.style.overflow = '';
        document.removeEventListener('keydown', closeOnEscape);
      }
    }
  }

  /* ---------------------------------------------------------------------------
     Boot
     --------------------------------------------------------------------------- */

  function init() {
    buildTOC();
    initGSAP();
    initTabs();
    initFigExpand();
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();
