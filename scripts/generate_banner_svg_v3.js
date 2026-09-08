const fs = require('fs');

const WIDTH = 840;
const HEIGHT = 220;
const TILE_W = 46;
const TILE_H = 64;
const TILE_R = 8;
const GAP = 6;
const STEP = TILE_W + GAP; // 52
const TOTAL_DURATION = 9.0; // 9.0s full relaxed cycle

const WORD1 = 'think2thrive'.split('');
const WORD2 = 'explore'.split('');

const TOTAL_W_12 = 12 * TILE_W + 11 * GAP; // 618
const START_X_12 = (WIDTH - TOTAL_W_12) / 2; // 111

const TOTAL_W_7 = 7 * TILE_W + 6 * GAP; // 358
const START_X_7 = (WIDTH - TOTAL_W_7) / 2; // 241
const Y = (HEIGHT - TILE_H) / 2; // 78

// Center shift for core slots 2..8
const CENTER_SHIFT = START_X_7 - (START_X_12 + 2 * STEP); // +26px

function pct(sec) {
  return ((sec / TOTAL_DURATION) * 100).toFixed(2) + '%';
}

// Curated high-contrast alphanumeric scramble characters (white)
const SCRAMBLE_SETS = [
  // 0: 't' -> scramble -> hidden -> scramble -> 't'
  { s1: ['8', 'q', 'm'], s2: ['4', 'k', 'r'] },
  // 1: 'h' -> scramble -> hidden -> scramble -> 'h'
  { s1: ['3', 'p', 'z'], s2: ['7', 'b', 'n'] },
  // 2: 'i' -> 'e' -> 'i'
  { s1: ['w', '5', 'x'], s2: ['j', '9', 'y'] },
  // 3: 'n' -> 'x' -> 'n'
  { s1: ['a', '2', 'u'], s2: ['c', '6', 'f'] },
  // 4: 'k' -> 'p' -> 'k'
  { s1: ['d', '8', 'v'], s2: ['g', '1', 'l'] },
  // 5: '2' -> 'l' -> '2'
  { s1: ['s', '9', 'h'], s2: ['o', '4', 't'] },
  // 6: 't' -> 'o' -> 't'
  { s1: ['m', '7', 'r'], s2: ['b', '3', 'e'] },
  // 7: 'h' -> 'r' -> 'h'
  { s1: ['k', '6', 'a'], s2: ['z', '8', 'w'] },
  // 8: 'r' -> 'e' -> 'r'
  { s1: ['p', '4', 'i'], s2: ['x', '5', 'm'] },
  // 9: 'i' -> scramble -> hidden -> scramble -> 'i'
  { s1: ['v', '1', 'd'], s2: ['y', '2', 'c'] },
  // 10: 'v' -> scramble -> hidden -> scramble -> 'v'
  { s1: ['g', '3', 't'], s2: ['n', '7', 'j'] },
  // 11: 'e' -> scramble -> hidden -> scramble -> 'e'
  { s1: ['l', '8', 'f'], s2: ['u', '6', 'q'] }
];

function buildSvg() {
  // Timeline breakdown (TOTAL = 9.0s):
  // 0.0s - 3.2s: think2thrive hold (0% - 35.56%)
  // 3.2s - 4.6s: transition 1 (think2thrive -> explore)
  //   3.2s - 3.8s: flank collapse
  //   3.25s - 4.4s: core slots flip & scramble into 'explore'
  //   3.3s - 4.1s: core group slides +26px
  // 4.6s - 7.4s: explore hold (51.11% - 82.22%) (2.8 seconds hold)
  // 7.4s - 8.6s: transition 2 (explore -> think2thrive)
  //   7.4s - 8.3s: flank stretch out with spring bounce
  //   7.45s - 8.5s: all 12 slots flip & scramble into 'think2thrive'
  //   7.5s - 8.2s: core group slides back to 0px
  // 8.6s - 9.0s: think2thrive settle & hold (95.56% - 100%) (matches 0.0s!)

  let css = `
    * { box-sizing: border-box; }
    .tile-text {
      font-family: ui-monospace, SFMono-Regular, "Roboto Mono", "Cascadia Code", "Liberation Mono", Menlo, Consolas, monospace;
      font-size: 38px;
      font-weight: 760;
      fill: #ffffff;
      text-anchor: middle;
      dominant-baseline: central;
    }
    .crease-dark { stroke: #090d12; stroke-width: 1.5; }
    .crease-light { stroke: rgba(255, 255, 255, 0.12); stroke-width: 0.8; }

    /* Ambient CRT glow breathing */
    @keyframes glowPulse {
      0%, 100% { opacity: 0.85; transform: scale(1); }
      50% { opacity: 1; transform: scale(1.04); }
    }
    .crt-glow {
      transform-origin: 420px 110px;
      animation: glowPulse 6s ease-in-out infinite;
    }

    /* Core slide: shifts +26px during explore to dead-center the 7 letters */
    @keyframes coreSlide {
      0%, ${pct(3.2)} {
        transform: translateX(0px);
      }
      ${pct(4.2)}, ${pct(7.4)} {
        transform: translateX(${CENTER_SHIFT}px);
      }
      ${pct(8.4)}, 100% {
        transform: translateX(0px);
      }
    }
    .core-slide {
      animation: coreSlide ${TOTAL_DURATION}s cubic-bezier(0.34, 1.3, 0.64, 1) infinite;
    }
  `;

  // Flank configurations with accordion stretch
  // Flanks 0, 1 collapse towards X=241
  // Flanks 9, 10, 11 collapse towards X=553 (the left of tile 8)
  const flankDefs = [
    { idx: 0, delta: 130, cStart: 3.20, sStart: 7.50 },
    { idx: 1, delta: 78,  cStart: 3.28, sStart: 7.42 },
    { idx: 9, delta: -26, cStart: 3.28, sStart: 7.42 },
    { idx: 10, delta: -78, cStart: 3.24, sStart: 7.46 },
    { idx: 11, delta: -130, cStart: 3.20, sStart: 7.50 }
  ];

  for (const f of flankDefs) {
    const cEnd = f.cStart + 0.50;
    const sOvershoot = f.sStart + 0.42;
    const sEnd = sOvershoot + 0.28;

    css += `
      @keyframes flankAnim${f.idx} {
        0%, ${pct(3.2)} {
          transform: translateX(0px) scaleX(1);
          opacity: 1;
          visibility: visible;
        }
        ${pct(cEnd)}, ${pct(7.35)} {
          transform: translateX(${f.delta}px) scaleX(0);
          opacity: 0;
          visibility: hidden;
        }
        ${pct(sOvershoot)} {
          transform: translateX(${f.delta * -0.06}px) scaleX(1.15);
          opacity: 1;
          visibility: visible;
        }
        ${pct(sEnd)}, 100% {
          transform: translateX(0px) scaleX(1);
          opacity: 1;
          visibility: visible;
        }
      }
      .flank-anim-${f.idx} {
        transform-origin: ${f.delta > 0 ? '46px 32px' : '0px 32px'};
        animation: flankAnim${f.idx} ${TOTAL_DURATION}s cubic-bezier(0.34, 1.45, 0.64, 1) infinite;
      }
    `;
  }

  // Flap flip and Scramble switching per slot
  for (let i = 0; i < 12; i++) {
    const isCore = i >= 2 && i <= 8;
    // Stagger starts
    const t1 = 3.25 + (isCore ? (i - 2) * 0.055 : (i < 2 ? i * 0.04 : (i - 9) * 0.04));
    const t2 = 7.45 + (isCore ? (i - 2) * 0.055 : (i < 2 ? (1 - i) * 0.08 : (i - 8) * 0.06));

    // Flip flap folds (3 rapid flap folds during each transition)
    css += `
      @keyframes flapFlip${i} {
        0%, ${pct(t1)} { transform: scaleY(1); }
        ${pct(t1 + 0.08)} { transform: scaleY(0.12); }
        ${pct(t1 + 0.16)} { transform: scaleY(1); }
        ${pct(t1 + 0.24)} { transform: scaleY(0.12); }
        ${pct(t1 + 0.32)} { transform: scaleY(1); }
        ${pct(t1 + 0.40)} { transform: scaleY(0.12); }
        ${pct(t1 + 0.48)}, ${pct(t2)} { transform: scaleY(1); }
        ${pct(t2 + 0.08)} { transform: scaleY(0.12); }
        ${pct(t2 + 0.16)} { transform: scaleY(1); }
        ${pct(t2 + 0.24)} { transform: scaleY(0.12); }
        ${pct(t2 + 0.32)} { transform: scaleY(1); }
        ${pct(t2 + 0.40)} { transform: scaleY(0.12); }
        ${pct(t2 + 0.48)}, 100% { transform: scaleY(1); }
      }
      .flap-anim-${i} {
        transform-origin: 23px 32px;
        animation: flapFlip${i} ${TOTAL_DURATION}s ease-in-out infinite;
      }
    `;

    // Character switching
    // Phases in Transition 1:
    // [0s, t1 + 0.08s]: Char 1 (from think2thrive)
    // [t1 + 0.08s, t1 + 0.24s]: Scramble 1A
    // [t1 + 0.24s, t1 + 0.40s]: Scramble 1B
    // [t1 + 0.40s, t2 + 0.08s]: Target (explore char for core slots, or blank/last for flank)
    // Phases in Transition 2:
    // [t2 + 0.08s, t2 + 0.24s]: Scramble 2A
    // [t2 + 0.24s, t2 + 0.40s]: Scramble 2B
    // [t2 + 0.40s, 9.0s]: Char 1 (think2thrive settled!)

    const p0 = pct(t1 + 0.08);
    const p1 = pct(t1 + 0.24);
    const p2 = pct(t1 + 0.40);
    const p3 = pct(t2 + 0.08);
    const p4 = pct(t2 + 0.24);
    const p5 = pct(t2 + 0.40);

    // Initial Char (WORD1[i])
    css += `
      @keyframes char${i}_w1 {
        0%, ${p0} { opacity: 1; }
        ${pct(t1 + 0.09)}, ${p5} { opacity: 0; }
        ${pct(t2 + 0.41)}, 100% { opacity: 1; }
      }
      .c-${i}-w1 { animation: char${i}_w1 ${TOTAL_DURATION}s step-end infinite; }
    `;

    // Scramble 1A
    css += `
      @keyframes char${i}_s1a {
        0%, ${p0} { opacity: 0; }
        ${pct(t1 + 0.09)}, ${p1} { opacity: 1; }
        ${pct(t1 + 0.25)}, 100% { opacity: 0; }
      }
      .c-${i}-s1a { animation: char${i}_s1a ${TOTAL_DURATION}s step-end infinite; }
    `;

    // Scramble 1B
    css += `
      @keyframes char${i}_s1b {
        0%, ${p1} { opacity: 0; }
        ${pct(t1 + 0.25)}, ${p2} { opacity: 1; }
        ${pct(t1 + 0.41)}, 100% { opacity: 0; }
      }
      .c-${i}-s1b { animation: char${i}_s1b ${TOTAL_DURATION}s step-end infinite; }
    `;

    if (isCore) {
      // Word 2 Char (explore)
      css += `
        @keyframes char${i}_w2 {
          0%, ${p2} { opacity: 0; }
          ${pct(t1 + 0.41)}, ${p3} { opacity: 1; }
          ${pct(t2 + 0.09)}, 100% { opacity: 0; }
        }
        .c-${i}-w2 { animation: char${i}_w2 ${TOTAL_DURATION}s step-end infinite; }
      `;
    }

    // Scramble 2A
    css += `
      @keyframes char${i}_s2a {
        0%, ${p3} { opacity: 0; }
        ${pct(t2 + 0.09)}, ${p4} { opacity: 1; }
        ${pct(t2 + 0.25)}, 100% { opacity: 0; }
      }
      .c-${i}-s2a { animation: char${i}_s2a ${TOTAL_DURATION}s step-end infinite; }
    `;

    // Scramble 2B
    css += `
      @keyframes char${i}_s2b {
        0%, ${p4} { opacity: 0; }
        ${pct(t2 + 0.25)}, ${p5} { opacity: 1; }
        ${pct(t2 + 0.41)}, 100% { opacity: 0; }
      }
      .c-${i}-s2b { animation: char${i}_s2b ${TOTAL_DURATION}s step-end infinite; }
    `;
  }

  // Helper to render texts for slot i
  function renderTexts(i) {
    const isCore = i >= 2 && i <= 8;
    const w1 = WORD1[i];
    const w2 = isCore ? WORD2[i - 2] : '';
    const set = SCRAMBLE_SETS[i];

    let t = `<text x="${TILE_W/2}" y="32" class="tile-text c-${i}-w1">${w1}</text>`;
    t += `<text x="${TILE_W/2}" y="32" class="tile-text c-${i}-s1a">${set.s1[0]}</text>`;
    t += `<text x="${TILE_W/2}" y="32" class="tile-text c-${i}-s1b">${set.s1[1]}</text>`;
    if (isCore) {
      t += `<text x="${TILE_W/2}" y="32" class="tile-text c-${i}-w2">${w2}</text>`;
    }
    t += `<text x="${TILE_W/2}" y="32" class="tile-text c-${i}-s2a">${set.s2[0]}</text>`;
    t += `<text x="${TILE_W/2}" y="32" class="tile-text c-${i}-s2b">${set.s2[1]}</text>`;
    return t;
  }

  let svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 ${WIDTH} ${HEIGHT}" width="${WIDTH}" height="${HEIGHT}">
  <defs>
    <!-- Background Cosmic Violet Glow -->
    <radialGradient id="crtGlow" cx="50%" cy="50%" r="55%">
      <stop offset="0%" stop-color="#c755f7" stop-opacity="0.28" />
      <stop offset="45%" stop-color="#9333ea" stop-opacity="0.14" />
      <stop offset="75%" stop-color="#3b0764" stop-opacity="0.05" />
      <stop offset="100%" stop-color="#0d1117" stop-opacity="0" />
    </radialGradient>

    <!-- Tile Gradients -->
    <linearGradient id="tileTopGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#242b35" />
      <stop offset="100%" stop-color="#161b22" />
    </linearGradient>
    <linearGradient id="tileBottomGrad" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0%" stop-color="#161b22" />
      <stop offset="100%" stop-color="#0d1117" />
    </linearGradient>

    <!-- Tile Clip Paths (Local to 0,0 46x64) -->
    <clipPath id="tileTopClip">
      <rect x="0" y="0" width="${TILE_W}" height="32" rx="${TILE_R}" />
    </clipPath>
    <clipPath id="tileBottomClip">
      <rect x="0" y="32" width="${TILE_W}" height="32" rx="${TILE_R}" />
    </clipPath>

    <!-- CRT Scanlines Pattern -->
    <pattern id="scanlines" width="100%" height="3" patternUnits="userSpaceOnUse">
      <line x1="0" y1="0" x2="${WIDTH}" y2="0" stroke="rgba(0, 0, 0, 0.28)" stroke-width="1.2" />
    </pattern>

    <!-- Board Violet Drop Shadow -->
    <filter id="tileShadow" x="-30%" y="-30%" width="160%" height="160%">
      <feDropShadow dx="0" dy="6" stdDeviation="14" flood-color="#c755f7" flood-opacity="0.28" />
      <feDropShadow dx="0" dy="3" stdDeviation="4" flood-color="#000000" flood-opacity="0.6" />
    </filter>
  </defs>

  <style>
${css}
  </style>

  <!-- ─── Background Layer ─── -->
  <rect width="${WIDTH}" height="${HEIGHT}" fill="#0d1117" />
  
  <!-- Cosmic Violet Radial Plasma -->
  <ellipse cx="${WIDTH/2}" cy="${HEIGHT/2}" rx="380" ry="105" fill="url(#crtGlow)" class="crt-glow" />

  <!-- CRT Scanlines Overlay -->
  <rect width="${WIDTH}" height="${HEIGHT}" fill="url(#scanlines)" pointer-events="none" />

  <!-- Outer Frame Subtle Border -->
  <rect x="1" y="1" width="${WIDTH - 2}" height="${HEIGHT - 2}" rx="12" fill="none" stroke="#21262d" stroke-width="1" />

  <!-- ─── Split-Flap Board Layer ─── -->
  <g filter="url(#tileShadow)">
  `;

  // Left flanks: 0, 1
  for (let i = 0; i < 2; i++) {
    const x = START_X_12 + i * STEP;
    svg += `
    <g transform="translate(${x}, ${Y})">
      <g class="flank-anim-${i}">
        <g class="flap-anim-${i}">
          <rect width="${TILE_W}" height="${TILE_H}" rx="${TILE_R}" fill="#161b22" stroke="#30363d" stroke-width="1" />
          <g clip-path="url(#tileTopClip)">
            <rect width="${TILE_W}" height="32" fill="url(#tileTopGrad)" />
            ${renderTexts(i)}
          </g>
          <g clip-path="url(#tileBottomClip)">
            <rect y="32" width="${TILE_W}" height="32" fill="url(#tileBottomGrad)" />
            ${renderTexts(i)}
          </g>
          <line x1="0" y1="31.5" x2="${TILE_W}" y2="31.5" class="crease-dark" />
          <line x1="0" y1="32.5" x2="${TILE_W}" y2="32.5" class="crease-light" />
        </g>
      </g>
    </g>
    `;
  }

  // Core slots: 2..8
  svg += `<g class="core-slide">`;
  for (let i = 2; i <= 8; i++) {
    const x = START_X_12 + i * STEP;
    svg += `
    <g transform="translate(${x}, ${Y})">
      <g class="flap-anim-${i}">
        <rect width="${TILE_W}" height="${TILE_H}" rx="${TILE_R}" fill="#161b22" stroke="#30363d" stroke-width="1" />
        <g clip-path="url(#tileTopClip)">
          <rect width="${TILE_W}" height="32" fill="url(#tileTopGrad)" />
          ${renderTexts(i)}
        </g>
        <g clip-path="url(#tileBottomClip)">
          <rect y="32" width="${TILE_W}" height="32" fill="url(#tileBottomGrad)" />
          ${renderTexts(i)}
        </g>
        <line x1="0" y1="31.5" x2="${TILE_W}" y2="31.5" class="crease-dark" />
        <line x1="0" y1="32.5" x2="${TILE_W}" y2="32.5" class="crease-light" />
      </g>
    </g>
    `;
  }
  svg += `</g>`;

  // Right flanks: 9, 10, 11
  for (let i = 9; i < 12; i++) {
    const x = START_X_12 + i * STEP;
    svg += `
    <g transform="translate(${x}, ${Y})">
      <g class="flank-anim-${i}">
        <g class="flap-anim-${i}">
          <rect width="${TILE_W}" height="${TILE_H}" rx="${TILE_R}" fill="#161b22" stroke="#30363d" stroke-width="1" />
          <g clip-path="url(#tileTopClip)">
            <rect width="${TILE_W}" height="32" fill="url(#tileTopGrad)" />
            ${renderTexts(i)}
          </g>
          <g clip-path="url(#tileBottomClip)">
            <rect y="32" width="${TILE_W}" height="32" fill="url(#tileBottomGrad)" />
            ${renderTexts(i)}
          </g>
          <line x1="0" y1="31.5" x2="${TILE_W}" y2="31.5" class="crease-dark" />
          <line x1="0" y1="32.5" x2="${TILE_W}" y2="32.5" class="crease-light" />
        </g>
      </g>
    </g>
    `;
  }

  svg += `
  </g>
</svg>`;
  return svg;
}

const finalSvg = buildSvg();
fs.writeFileSync('banner.svg', finalSvg);
console.log('Saved banner.svg (' + finalSvg.length + ' bytes)');
