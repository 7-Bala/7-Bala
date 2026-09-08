import { useEffect, useMemo, useRef, useState } from 'react';
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

// Build slots with explicit collapse metadata so empty boxes are automatically removed
const buildSlots = (phrase, totalWidth) => {
  const clean = String(phrase ?? '').trim();
  const len = clean.length;
  const startIdx = Math.floor(Math.max(0, totalWidth - len) / 2);
  const endIdx = startIdx + len;

  const slots = [];
  for (let i = 0; i < totalWidth; i += 1) {
    if (i >= startIdx && i < endIdx) {
      const char = clean[i - startIdx] || ' ';
      slots.push({
        char,
        isCollapsed: false
      });
    } else {
      slots.push({
        char: ' ',
        isCollapsed: true
      });
    }
  }
  return slots;
};

const sampleChar = charset => charset.charAt(Math.floor(Math.random() * charset.length)) || 'a';

const buildSequence = (target, flips, charset) => {
  if (target === ' ') return [' '];
  // Distinct mechanical odometer tally roller for digits like '2'
  if (/\d/.test(target)) {
    const targetNum = parseInt(target, 10);
    const count = flips + 3; // rapid odometer drum spin
    let start = (targetNum - count + 100) % 10;
    const steps = [];
    for (let i = 0; i < count; i += 1) {
      steps.push(String((start + i) % 10));
    }
    steps.push(target);
    return steps;
  }
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
  flipDuration = 0.10,
  stagger = 0.04,
  cycleDelay = 2600,
  charset = 'alphanumeric',
  flipsPerChar = 6,
  tileColor = '#161b22',
  textColor = '#f8fafc',
  tileRadius = 7,
  gap = 6,
  fontSize = 38,
  loop = true,
  className = '',
  style = {},
  ...props
}) => {
  const prefersReducedMotion = usePrefersReducedMotion();
  const rafRef = useRef(null);
  const cycleTimerRef = useRef(null);

  const sourceWords = Array.isArray(words) && words.length > 0 ? words : DEFAULT_WORDS;
  const phrasesKey = typeof text === 'string' ? text : sourceWords.map(word => String(word ?? '')).join('\u001f');
  const phrases = useMemo(() => phrasesKey.split('\u001f'), [phrasesKey]);

  // Max width of all phrases
  const totalWidth = useMemo(() => {
    return Math.max(1, ...phrases.map(p => String(p ?? '').length));
  }, [phrases]);

  const [tiles, setTiles] = useState(() => {
    const initialSlots = buildSlots(phrases[0] || '', totalWidth);
    return initialSlots.map(s => ({
      current: s.char,
      next: s.char,
      flipping: false,
      isCollapsed: s.isCollapsed,
      tick: 0
    }));
  });

  const currentPhraseRef = useRef(phrases[0] || '');

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

    const firstWord = phrases[0] || '';
    currentPhraseRef.current = firstWord;
    const initialSlots = buildSlots(firstWord, totalWidth);
    setTiles(
      initialSlots.map(s => ({
        current: s.char,
        next: s.char,
        flipping: false,
        isCollapsed: s.isCollapsed,
        tick: 0
      }))
    );

    if (phrases.length <= 1 || typeof window === 'undefined') {
      return clearAnimation;
    }

    let phraseIndex = 0;
    let cancelled = false;

    const safeFlipMs = Math.max(35, (Number(flipDuration) || 0.10) * 1000);
    const safeStaggerMs = Math.max(0, (Number(stagger) || 0.04) * 1000);
    const safeCycleDelay = Math.max(400, Number(cycleDelay) || 2600);
    const safeFlips = Math.max(0, Math.floor(Number(flipsPerChar) || 0));
    const activeCharset = resolveCharset(charset);

    const animateTo = targetWord => {
      const targetSlots = buildSlots(targetWord, totalWidth);

      if (prefersReducedMotion) {
        currentPhraseRef.current = targetWord;
        setTiles(
          targetSlots.map(s => ({
            current: s.char,
            next: s.char,
            flipping: false,
            isCollapsed: s.isCollapsed,
            tick: 0
          }))
        );
        return 0;
      }

      const fromSlots = buildSlots(currentPhraseRef.current, totalWidth);

      const plans = targetSlots.map((targetSlot, index) => {
        const fromSlot = fromSlots[index] || { char: ' ', isCollapsed: true };
        const isChangingChar = fromSlot.char !== targetSlot.char;
        const isCollapseChanging = fromSlot.isCollapsed !== targetSlot.isCollapsed;

        if (!isChangingChar && !isCollapseChanging) return null;

        const sequence = targetSlot.isCollapsed
          ? [' ']
          : buildSequence(targetSlot.char, safeFlips, activeCharset);

        return {
          index,
          fromChar: fromSlot.char,
          targetChar: targetSlot.char,
          isCollapsed: targetSlot.isCollapsed,
          sequence,
          start: index * safeStaggerMs,
          step: -1,
          done: false
        };
      }).filter(Boolean);

      if (!plans.length) {
        currentPhraseRef.current = targetWord;
        setTiles(
          targetSlots.map(s => ({
            current: s.char,
            next: s.char,
            flipping: false,
            isCollapsed: s.isCollapsed,
            tick: 0
          }))
        );
        return 0;
      }

      // Pre-collapse or pre-expand slots smoothly
      setTiles(prev =>
        prev.map((tile, i) => {
          const targetSlot = targetSlots[i];
          if (!targetSlot) return tile;
          return {
            ...tile,
            isCollapsed: targetSlot.isCollapsed
          };
        })
      );

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
              flipping: !update.done && !update.isCollapsed,
              isCollapsed: update.isCollapsed,
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
                current: step === 0 ? plan.fromChar : plan.sequence[step - 1],
                next: plan.sequence[step],
                isCollapsed: plan.isCollapsed,
                done: false
              });
            }
          } else if (!plan.done) {
            plan.done = true;
            updates.push({
              index: plan.index,
              current: plan.targetChar,
              next: plan.targetChar,
              isCollapsed: plan.isCollapsed,
              done: true
            });
          }
        });

        if (updates.length > 0) updateTiles(updates);

        if (shouldContinue) {
          rafRef.current = requestAnimationFrame(tick);
        } else {
          currentPhraseRef.current = targetWord;
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
        if (nextIndex >= phrases.length && !loop) return;

        phraseIndex = nextIndex % phrases.length;
        const animationDuration = animateTo(phrases[phraseIndex]);
        scheduleNext(safeCycleDelay + animationDuration);
      }, delay);
    };

    scheduleNext(safeCycleDelay);

    return () => {
      cancelled = true;
      clearAnimation();
    };
  }, [phrases, totalWidth, loop, cycleDelay, flipDuration, stagger, flipsPerChar, charset, prefersReducedMotion]);

  const settledText = tiles
    .filter(t => !t.isCollapsed)
    .map(t => t.current)
    .join('');

  const componentStyle = {
    '--split-flap-tile-color': tileColor,
    '--split-flap-text-color': textColor,
    '--split-flap-radius': toCssUnit(tileRadius),
    '--split-flap-gap': toCssUnit(gap),
    '--split-flap-font-size': toCssUnit(fontSize),
    '--split-flap-flip-duration': `${Math.max(0.04, Number(flipDuration) || 0.10)}s`,
    ...style
  };

  return (
    <div
      className={`split-flap-text ${className}`.trim()}
      style={componentStyle}
      role="text"
      aria-label={settledText || undefined}
      {...props}
    >
      {tiles.map((tile, index) => {
        const slotClasses = [
          'split-flap-text__slot',
          tile.isCollapsed ? 'is-collapsed' : ''
        ].filter(Boolean).join(' ');

        const isDigit = /\d/.test(tile.current) || /\d/.test(tile.next);

        const tileClasses = [
          'split-flap-text__tile',
          tile.flipping ? 'split-flap-text__tile--flipping' : '',
          isDigit ? 'split-flap-text__tile--digit' : ''
        ].filter(Boolean).join(' ');

        const wobble = index % 2 === 0 ? 1 : -1;

        return (
          <div className={slotClasses} key={`slot-${index}-${totalWidth}`}>
            <span
              className={tileClasses}
              style={{ '--tile-wobble': wobble }}
              aria-hidden="true"
            >
              <span className="split-flap-text__half split-flap-text__half--top">
                <span className="split-flap-text__char">{tile.current === ' ' ? '\u00A0' : tile.current}</span>
              </span>
              <span className="split-flap-text__half split-flap-text__half--bottom">
                <span className="split-flap-text__char">{tile.flipping ? tile.next : tile.current}</span>
              </span>

              {tile.flipping && (
                <>
                  <span className="split-flap-text__ghost" key={`ghost-${index}-${tile.tick}`}>
                    <span className="split-flap-text__char">{tile.current === ' ' ? '\u00A0' : tile.current}</span>
                  </span>
                  <span className="split-flap-text__flap split-flap-text__flap--front" key={`front-${index}-${tile.tick}`}>
                    <span className="split-flap-text__char">{tile.current === ' ' ? '\u00A0' : tile.current}</span>
                  </span>
                  <span className="split-flap-text__flap split-flap-text__flap--back" key={`back-${index}-${tile.tick}`}>
                    <span className="split-flap-text__char">{tile.next === ' ' ? '\u00A0' : tile.next}</span>
                  </span>
                </>
              )}
            </span>
          </div>
        );
      })}
    </div>
  );
};

export default SplitFlapText;
