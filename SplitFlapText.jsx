import React, { useEffect, useMemo, useRef, useState } from 'react';
import './SplitFlapText.css';

const DEFAULT_WORDS = ['think2thrive', 'explore'];

const CHARSETS = {
  alpha: 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ',
  alphanumeric: 'abcdefghijklmnopqrstuvwxyz0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ',
  numeric: '0123456789'
};

const toCssUnit = value => (typeof value === 'number' ? `${value}px` : value);

const resolveCharset = charset => {
  if (CHARSETS[charset]) return CHARSETS[charset];
  return typeof charset === 'string' && charset.length > 0 ? charset : CHARSETS.alphanumeric;
};

const centerPhrase = (phrase, totalWidth) => {
  const clean = String(phrase ?? '').trim();
  const len = clean.length;
  if (len >= totalWidth) return clean.slice(0, totalWidth);
  const leftPad = Math.floor((totalWidth - len) / 2);
  const rightPad = totalWidth - len - leftPad;
  return ' '.repeat(leftPad) + clean + ' '.repeat(rightPad);
};

const getActiveRange = phrase => {
  const str = String(phrase ?? '');
  const trimmed = str.trim();
  if (!trimmed) return { start: -1, end: -1 };
  const start = str.indexOf(trimmed);
  const end = start + trimmed.length;
  return { start, end };
};

const createTiles = phrase =>
  phrase.split('').map(char => ({
    current: char,
    next: char,
    flipping: false,
    tick: 0
  }));

const sampleChar = charset => charset.charAt(Math.floor(Math.random() * charset.length)) || 'a';

const buildSequence = (target, flips, charset) => {
  if (target === ' ') return [' '];
  const steps = [];
  for (let i = 0; i < flips; i += 1) {
    steps.push(sampleChar(charset));
  }
  steps.push(target);
  return steps;
};

const usePrefersReducedMotion = () => {
  const [prefersReduced, setPrefersReduced] = useState(false);

  useEffect(() => {
    if (typeof window === 'undefined' || !window.matchMedia) return;
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    const handleChange = () => setPrefersReduced(mediaQuery.matches);
    handleChange();
    mediaQuery.addEventListener('change', handleChange);
    return () => mediaQuery.removeEventListener('change', handleChange);
  }, []);

  return prefersReduced;
};

const SplitFlapText = ({
  words = ['think2thrive', 'explore'],
  text,
  flipDuration = 0.11,
  stagger = 0.05,
  cycleDelay = 2400,
  charset = 'alphanumeric',
  flipsPerChar = 8,
  tileColor = '#161b22',
  textColor = '#ffffff',
  tileRadius = 8,
  gap = 6,
  fontSize = 46,
  loop = true,
  padTo = 12,
  className = '',
  style = {},
  ...props
}) => {
  const prefersReducedMotion = usePrefersReducedMotion();
  const rafRef = useRef(null);
  const cycleTimerRef = useRef(null);
  const currentTextRef = useRef('');

  const sourceWords = Array.isArray(words) && words.length > 0 ? words : DEFAULT_WORDS;
  const phrasesKey = typeof text === 'string' ? text : sourceWords.map(word => String(word ?? '')).join('\u001f');
  const phrases = useMemo(() => phrasesKey.split('\u001f'), [phrasesKey]);

  const width = useMemo(() => {
    const longest = phrases.reduce((max, phrase) => Math.max(max, String(phrase ?? '').trim().length), 1);
    return Math.max(1, Math.ceil(Number(padTo) || 0), longest);
  }, [padTo, phrases]);

  const normalizedPhrases = useMemo(
    () => phrases.map(phrase => centerPhrase(phrase, width)),
    [phrases, width]
  );

  const [tiles, setTiles] = useState(() => createTiles(normalizedPhrases[0] || ''));
  const [activeTargetPhrase, setActiveTargetPhrase] = useState(() => normalizedPhrases[0] || '');
  // isExpanding: true means we are going from shorter -> longer word (explore -> think2thrive)
  // isCollapsing: true means going from longer -> shorter (think2thrive -> explore)
  const [isExpanding, setIsExpanding] = useState(false);
  const [isCollapsing, setIsCollapsing] = useState(false);

  useEffect(() => {
    const clearAnimation = () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
        rafRef.current = null;
      }
      if (cycleTimerRef.current) {
        clearTimeout(cycleTimerRef.current);
        cycleTimerRef.current = null;
      }
    };

    clearAnimation();

    const firstPhrase = normalizedPhrases[0] || '';
    currentTextRef.current = firstPhrase;
    setActiveTargetPhrase(firstPhrase);
    setTiles(createTiles(firstPhrase));
    setIsExpanding(false);
    setIsCollapsing(false);

    if (normalizedPhrases.length <= 1 || typeof window === 'undefined') {
      return clearAnimation;
    }

    let phraseIndex = 0;
    let cancelled = false;

    const safeFlipMs = Math.max(35, (Number(flipDuration) || 0.11) * 1000);
    const safeStaggerMs = Math.max(0, (Number(stagger) || 0) * 1000);
    const safeCycleDelay = Math.max(400, Number(cycleDelay) || 2400);
    const safeFlips = Math.max(0, Math.floor(Number(flipsPerChar) || 0));
    const activeCharset = resolveCharset(charset);

    const animateTo = targetPhrase => {
      setActiveTargetPhrase(targetPhrase);

      const prevClean = String(currentTextRef.current ?? '').trim();
      const nextClean = String(targetPhrase ?? '').trim();

      if (nextClean.length > prevClean.length) {
        // Expanding: explore -> think2thrive
        setIsExpanding(true);
        setIsCollapsing(false);
        window.setTimeout(() => setIsExpanding(false), 550);
      } else if (nextClean.length < prevClean.length) {
        // Collapsing: think2thrive -> explore
        setIsCollapsing(true);
        setIsExpanding(false);
        window.setTimeout(() => setIsCollapsing(false), 500);
      } else {
        setIsExpanding(false);
        setIsCollapsing(false);
      }

      if (prefersReducedMotion) {
        currentTextRef.current = targetPhrase;
        setTiles(createTiles(targetPhrase));
        return 0;
      }

      const fromPhrase = centerPhrase(currentTextRef.current, width);
      const targetChars = targetPhrase.split('');

      const plans = targetChars
        .map((targetChar, index) => {
          const fromChar = fromPhrase[index] || ' ';
          if (fromChar === targetChar) return null;
          return {
            index,
            from: fromChar,
            target: targetChar,
            sequence: buildSequence(targetChar, safeFlips, activeCharset),
            start: index * safeStaggerMs,
            step: -1,
            done: false
          };
        })
        .filter(Boolean);

      if (!plans.length) {
        currentTextRef.current = targetPhrase;
        setTiles(createTiles(targetPhrase));
        return 0;
      }

      const totalDuration = plans.reduce(
        (max, plan) => Math.max(max, plan.start + plan.sequence.length * safeFlipMs),
        0
      );
      const startedAt = performance.now();

      const updateTiles = updates => {
        setTiles(previous => {
          const nextTiles = [...previous];
          updates.forEach(update => {
            const tile = nextTiles[update.index];
            if (!tile) return;
            nextTiles[update.index] = {
              current: update.current,
              next: update.next,
              flipping: !update.done,
              tick: tile.tick + 1
            };
          });
          return nextTiles;
        });
      };

      const tick = now => {
        if (cancelled) return;

        const elapsed = now - startedAt;
        const updates = [];
        let shouldContinue = false;

        plans.forEach(plan => {
          const localElapsed = elapsed - plan.start;

          if (localElapsed < 0) {
            shouldContinue = true;
            return;
          }

          const step = Math.floor(localElapsed / safeFlipMs);

          if (step < plan.sequence.length) {
            shouldContinue = true;

            if (step !== plan.step) {
              plan.step = step;
              updates.push({
                index: plan.index,
                current: step === 0 ? plan.from : plan.sequence[step - 1],
                next: plan.sequence[step],
                done: false
              });
            }
          } else if (!plan.done) {
            plan.done = true;
            updates.push({
              index: plan.index,
              current: plan.target,
              next: plan.target,
              done: true
            });
          }
        });

        if (updates.length > 0) updateTiles(updates);

        if (shouldContinue) {
          rafRef.current = requestAnimationFrame(tick);
        } else {
          currentTextRef.current = targetPhrase;
          rafRef.current = null;
        }
      };

      rafRef.current = requestAnimationFrame(tick);
      return totalDuration;
    };

    const scheduleNext = delay => {
      cycleTimerRef.current = window.setTimeout(() => {
        if (cancelled) return;

        const nextIndex = phraseIndex + 1;
        if (nextIndex >= normalizedPhrases.length && !loop) return;

        phraseIndex = nextIndex % normalizedPhrases.length;
        const animationDuration = animateTo(normalizedPhrases[phraseIndex]);
        scheduleNext(safeCycleDelay + animationDuration);
      }, delay);
    };

    scheduleNext(safeCycleDelay);

    return () => {
      cancelled = true;
      clearAnimation();
    };
  }, [normalizedPhrases, width, loop, cycleDelay, flipDuration, stagger, flipsPerChar, charset, prefersReducedMotion]);

  const settledText = tiles
    .map(tile => tile.current)
    .join('')
    .trimEnd();

  const componentStyle = {
    '--split-flap-tile-color': tileColor,
    '--split-flap-text-color': textColor,
    '--split-flap-radius': toCssUnit(tileRadius),
    '--split-flap-gap': toCssUnit(gap),
    '--split-flap-font-size': toCssUnit(fontSize),
    '--split-flap-flip-duration': `${Math.max(0.04, Number(flipDuration) || 0.11)}s`,
    ...style
  };

  const { start: activeStart, end: activeEnd } = getActiveRange(activeTargetPhrase);

  // Core range = range of the shortest word when centered
  const shortestPhrase = useMemo(() => {
    return phrases.reduce(
      (min, p) => (String(p ?? '').trim().length < String(min ?? '').trim().length ? p : min),
      phrases[0] || ''
    );
  }, [phrases]);

  const coreRange = useMemo(
    () => getActiveRange(centerPhrase(shortestPhrase, width)),
    [shortestPhrase, width]
  );

  const coreStart = coreRange.start !== -1 ? coreRange.start : 2;
  const coreEnd = coreRange.end !== -1 ? coreRange.end : 9;

  // Gap size in CSS units
  const halfGapPx = `calc(${toCssUnit(gap)} / 2)`;
  // Normal slot width in em
  const slotWidth = '0.78em';

  return React.createElement(
    'div',
    {
      className: `split-flap-text ${className}`.trim(),
      style: componentStyle,
      role: 'text',
      'aria-label': settledText || undefined,
      ...props
    },
    tiles.map((tile, index) => {
      const isOutsideActive = activeStart !== -1 && (index < activeStart || index >= activeEnd);
      const isLeftFlank = index < coreStart;
      const isRightFlank = index >= coreEnd;
      const isLeftAnchor = index === coreStart;
      const isRightAnchor = index === coreEnd - 1;

      // Distance from the core boundary (1-indexed: closest = 1)
      let flankDist = 0;
      let slotClasses = '';
      let expandDelay = 0;
      let collapseDelay = 0;

      if (isLeftFlank) {
        flankDist = coreStart - index; // 1 for closest, higher for further
        // Expand from inside-out: closest tile stretches first
        expandDelay = (flankDist - 1) * 0.07;
        // Collapse from outside-in: furthest tile collapses first
        collapseDelay = (flankDist - 1) * 0.06;
        slotClasses = 'slot-flank';
      } else if (isRightFlank) {
        flankDist = index - coreEnd + 1; // 1 for closest
        expandDelay = (flankDist - 1) * 0.07;
        collapseDelay = (flankDist - 1) * 0.06;
        slotClasses = 'slot-flank';
      } else if (isLeftAnchor) {
        slotClasses = `slot-anchor-left${isExpanding ? ' is-stretching' : ''}`;
      } else if (isRightAnchor) {
        slotClasses = `slot-anchor-right${isExpanding ? ' is-stretching' : ''}`;
      }

      const isFlank = isLeftFlank || isRightFlank;
      const isEmpty = isFlank && isOutsideActive;

      if (isFlank) {
        slotClasses += isEmpty ? ' is-empty' : '';
        if (isCollapsing) slotClasses += ' is-collapsing';
      }

      // Inline styles drive the actual geometry — transition in CSS handles the animation
      const slotStyle = {};

      if (isFlank) {
        // When visible: normal width + gap margin
        // When empty: width=0, margin=0 (set via CSS .is-empty)
        slotStyle.width = isEmpty ? '0' : slotWidth;
        slotStyle.marginLeft = isEmpty ? '0' : halfGapPx;
        slotStyle.marginRight = isEmpty ? '0' : halfGapPx;
        slotStyle.transitionDelay = isEmpty
          ? `${collapseDelay.toFixed(3)}s`
          : `${expandDelay.toFixed(3)}s`;
      } else {
        slotStyle.width = slotWidth;
        slotStyle.marginLeft = halfGapPx;
        slotStyle.marginRight = halfGapPx;
      }

      return React.createElement(
        'span',
        {
          className: `split-flap-text__slot ${slotClasses}`.trim(),
          style: slotStyle,
          'aria-hidden': 'true',
          key: `slot-${index}`
        },
        React.createElement(
          'span',
          { className: 'split-flap-text__tile' },
          // Top static half
          React.createElement(
            'span',
            { className: 'split-flap-text__half split-flap-text__half--top' },
            React.createElement(
              'span',
              { className: 'split-flap-text__char' },
              tile.current === ' ' ? '\u00A0' : tile.current
            )
          ),
          // Bottom static half
          React.createElement(
            'span',
            { className: 'split-flap-text__half split-flap-text__half--bottom' },
            React.createElement(
              'span',
              { className: 'split-flap-text__char' },
              tile.flipping ? tile.next : tile.current
            )
          ),
          // Animated flap pair — only when flipping
          tile.flipping
            ? React.createElement(
                React.Fragment,
                null,
                React.createElement(
                  'span',
                  {
                    className: 'split-flap-text__flap split-flap-text__flap--front',
                    key: `front-${index}-${tile.tick}`
                  },
                  React.createElement(
                    'span',
                    { className: 'split-flap-text__char' },
                    tile.current === ' ' ? '\u00A0' : tile.current
                  )
                ),
                React.createElement(
                  'span',
                  {
                    className: 'split-flap-text__flap split-flap-text__flap--back',
                    key: `back-${index}-${tile.tick}`
                  },
                  React.createElement(
                    'span',
                    { className: 'split-flap-text__char' },
                    tile.next === ' ' ? '\u00A0' : tile.next
                  )
                )
              )
            : null
        )
      );
    })
  );
};

export default SplitFlapText;
