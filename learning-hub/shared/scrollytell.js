// ============================================================================
// scrollytell.js — lightweight scrollytelling engine for the Learning Hub
// ============================================================================
// Detects which narrative step is in view with a single IntersectionObserver,
// emits 'step-enter' / 'step-exit' / 'step-progress' events, and optionally
// auto-advances each step through a sequence of animation states.
//
// No dependencies. The sticky chart panel is handled entirely in CSS
// (position: sticky); this engine only drives the narrative <-> chart sync.
//
// Usage:
//
//   var story = new Scrollytell({
//       container: '.scrolly',     // root element / selector
//       step:      '.scrolly-step',// step selector within the container
//       offset:    0.55            // trigger line, fraction of viewport height
//   });
//
//   story.on('step-enter', function (e) {
//       // e.index, e.element, e.direction ('down' | 'up')
//       drawChartForStep(e.index);
//   });
//
//   story.on('step-progress', function (e) {
//       // e.index, e.state, e.totalStates — fires once per animation state
//       advanceAnimation(e.index, e.state);
//   });
//
// Auto-advance: a step opts in via data attributes —
//
//   <section class="scrolly-step" data-states="4" data-autoplay="1400">
//
// On enter the engine emits step-progress for state 0, then every 1400 ms
// advances to the next state until `data-states - 1` is reached. Steps with
// prefers-reduced-motion jump straight to the final state.
//
// Events also dispatch as CustomEvents on the container element, so
// `container.addEventListener('step-enter', ...)` works too.
// ============================================================================

(function (global) {
    'use strict';

    function resolve(target) {
        if (!target) return null;
        if (typeof target === 'string') return document.querySelector(target);
        return target.nodeType === 1 ? target : null;
    }

    function clampInt(value, fallback) {
        var n = parseInt(value, 10);
        return isNaN(n) ? fallback : n;
    }

    var prefersReducedMotion =
        global.matchMedia &&
        global.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // ------------------------------------------------------------------------
    function Scrollytell(options) {
        options = options || {};

        this.root = resolve(options.container || '.scrolly');
        if (!this.root) {
            throw new Error('Scrollytell: container element not found');
        }

        this.stepSelector = options.step || '.scrolly-step';
        this.activeClass = options.activeClass || 'is-active';

        // Trigger line as a fraction of viewport height (0 = top, 1 = bottom).
        var offset = typeof options.offset === 'number' ? options.offset : 0.55;
        this.offset = Math.min(Math.max(offset, 0), 1);

        this._handlers = {};        // eventName -> [fn, fn, ...]
        this._observer = null;
        this._steps = [];
        this._active = -1;          // index of the currently active step
        this._lastScrollY = global.scrollY || global.pageYOffset || 0;
        this._autoplayTimers = {};  // step index -> interval id

        this._onScroll = this._trackScrollDirection.bind(this);
        global.addEventListener('scroll', this._onScroll, { passive: true });

        this.refresh();
    }

    // ---- Public: (re)scan the DOM for steps and (re)build the observer -----
    Scrollytell.prototype.refresh = function () {
        this._teardownObserver();

        this._steps = Array.prototype.slice.call(
            this.root.querySelectorAll(this.stepSelector)
        );

        this._steps.forEach(function (el, i) {
            if (!el.hasAttribute('data-step')) {
                el.setAttribute('data-step', String(i));
            }
        });

        if (typeof IntersectionObserver === 'undefined') {
            // Fallback: no observer support — activate the first step so the
            // chart still renders something meaningful.
            if (this._steps.length) this._activate(0, 'down');
            return this;
        }

        // A zero-height trigger band positioned at `offset` down the viewport.
        // A step "enters" when it crosses that line.
        var topMargin = -(this.offset * 100);
        var bottomMargin = -(100 - this.offset * 100);
        var rootMargin = topMargin + '% 0px ' + bottomMargin + '% 0px';

        var self = this;
        this._observer = new IntersectionObserver(function (entries) {
            // Process in document order so direction handling is stable.
            entries
                .filter(function (entry) { return entry.isIntersecting; })
                .sort(function (a, b) {
                    return self._steps.indexOf(a.target) -
                           self._steps.indexOf(b.target);
                })
                .forEach(function (entry) {
                    var index = self._steps.indexOf(entry.target);
                    if (index === -1) return;
                    var dir = self._direction();
                    self._activate(index, dir);
                });
        }, { rootMargin: rootMargin, threshold: 0 });

        this._steps.forEach(function (el) {
            self._observer.observe(el);
        });

        return this;
    };

    // ---- Public: subscribe to an event ------------------------------------
    // Events: 'step-enter', 'step-exit', 'step-progress'
    Scrollytell.prototype.on = function (eventName, handler) {
        if (typeof handler !== 'function') return this;
        (this._handlers[eventName] = this._handlers[eventName] || []).push(handler);
        return this;
    };

    // ---- Public: unsubscribe ----------------------------------------------
    Scrollytell.prototype.off = function (eventName, handler) {
        var list = this._handlers[eventName];
        if (!list) return this;
        if (!handler) {
            delete this._handlers[eventName];
        } else {
            this._handlers[eventName] = list.filter(function (fn) {
                return fn !== handler;
            });
        }
        return this;
    };

    // ---- Public: index of the step currently in view ----------------------
    Scrollytell.prototype.getActiveIndex = function () {
        return this._active;
    };

    // ---- Public: total step count -----------------------------------------
    Scrollytell.prototype.getStepCount = function () {
        return this._steps.length;
    };

    // ---- Public: tear everything down -------------------------------------
    Scrollytell.prototype.destroy = function () {
        this._teardownObserver();
        global.removeEventListener('scroll', this._onScroll);
        this._handlers = {};
        this._steps = [];
        this._active = -1;
    };

    // ======================== internals ====================================

    Scrollytell.prototype._teardownObserver = function () {
        if (this._observer) {
            this._observer.disconnect();
            this._observer = null;
        }
        var self = this;
        Object.keys(this._autoplayTimers).forEach(function (key) {
            self._stopAutoplay(parseInt(key, 10));
        });
    };

    Scrollytell.prototype._trackScrollDirection = function () {
        this._lastScrollY = global.scrollY || global.pageYOffset || 0;
    };

    Scrollytell.prototype._direction = function () {
        var y = global.scrollY || global.pageYOffset || 0;
        return y >= this._lastScrollY ? 'down' : 'up';
    };

    // Make `index` the active step: exit the old one, enter the new one.
    Scrollytell.prototype._activate = function (index, direction) {
        if (index === this._active) return;

        var previous = this._active;

        if (previous !== -1 && this._steps[previous]) {
            this._steps[previous].classList.remove(this.activeClass);
            this._stopAutoplay(previous);
            this._emit('step-exit', {
                index: previous,
                element: this._steps[previous],
                direction: direction
            });
        }

        this._active = index;
        var el = this._steps[index];
        el.classList.add(this.activeClass);

        this._emit('step-enter', {
            index: index,
            element: el,
            direction: direction
        });

        this._beginStates(index, el);
    };

    // Drive the per-step animation-state sequence.
    Scrollytell.prototype._beginStates = function (index, el) {
        var totalStates = Math.max(1, clampInt(el.getAttribute('data-states'), 1));
        var interval = clampInt(el.getAttribute('data-autoplay'), 0);

        var emitState = function (state) {
            this._emit('step-progress', {
                index: index,
                element: el,
                state: state,
                totalStates: totalStates
            });
        }.bind(this);

        // Single-state step, or motion disabled — jump straight to the end.
        if (totalStates <= 1 || interval <= 0 || prefersReducedMotion) {
            emitState(totalStates - 1);
            return;
        }

        // Start at state 0, then advance on a timer.
        emitState(0);
        var current = 0;
        this._autoplayTimers[index] = global.setInterval(function () {
            current += 1;
            emitState(current);
            if (current >= totalStates - 1) {
                this._stopAutoplay(index);
            }
        }.bind(this), interval);
    };

    Scrollytell.prototype._stopAutoplay = function (index) {
        var timer = this._autoplayTimers[index];
        if (timer) {
            global.clearInterval(timer);
            delete this._autoplayTimers[index];
        }
    };

    // Dispatch to .on() subscribers and as a DOM CustomEvent on the container.
    Scrollytell.prototype._emit = function (eventName, detail) {
        var list = this._handlers[eventName];
        if (list) {
            list.slice().forEach(function (fn) {
                try {
                    fn(detail);
                } catch (err) {
                    if (global.console) global.console.error(err);
                }
            });
        }
        if (typeof CustomEvent === 'function') {
            this.root.dispatchEvent(new CustomEvent(eventName, { detail: detail }));
        }
    };

    // ---- Export ------------------------------------------------------------
    global.Scrollytell = Scrollytell;

    if (typeof module !== 'undefined' && module.exports) {
        module.exports = Scrollytell;
    }
})(typeof window !== 'undefined' ? window : this);
