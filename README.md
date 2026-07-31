<div align="center">

<img src="./ascii.svg" width="460" alt="explore"/>

<img src="./stats.svg" width="620" alt="Contributions in the last year"/>

[email](mailto:balachandran200707@gmail.com)

</div>

<img src="./hd-about.svg" width="620" alt="about"/>

> CS-minded builder, shipping across web, native, and AI agent tooling.<br>
> Deterministic logic does the heavy lifting; GenAI stays on a short leash.

Lately that's [Synapse](https://github.com/7-Bala/Synapse) — an execution<br>
environment for tracing deterministic multi-agent runtimes — and<br>
[AnyGate](https://github.com/7-Bala/AnyGate), an accessibility-first wayfinding<br>
assistant built around one rule: the LLM explains, it never decides.

<img src="./hd-stack.svg" width="620" alt="stack"/>

<samp>typescript &nbsp; python &nbsp; javascript &nbsp; swift &nbsp; react &nbsp; next.js &nbsp; tailwind &nbsp; docker &nbsp; git</samp>

<img src="./hd-projects.svg" width="620" alt="projects"/>

**[BloopDocs](https://github.com/7-Bala/BloopDocs)** &nbsp;·&nbsp; <samp>typescript, next.js, docker</samp><br>
Free document conversion platform on Next.js 16, powered by a headless<br>
LibreOffice engine — docx, xlsx, pptx, and PDF, converted either way.

**[Synapse](https://github.com/7-Bala/Synapse)** &nbsp;·&nbsp; <samp>python, typescript</samp><br>
An execution environment and debugger for deterministic multi-agent runtimes.<br>
Traces reasoning, evidence, and consensus loops in real time, not static metrics.

**[AnyGate](https://github.com/7-Bala/AnyGate)** &nbsp;·&nbsp; <samp>javascript, gemini</samp><br>
Accessibility-first wayfinding for stadium-scale events. A deterministic engine<br>
filters and ranks routes; the LLM's only job is explaining the recommendation.

**[ClaudePet](https://github.com/7-Bala/ClaudePet)** &nbsp;·&nbsp; <samp>swift, appkit</samp><br>
A pixel-art mascot on the macOS Dock that reacts in real time to a running<br>
Claude Code session — jumps on tool calls, waves when it needs input.

<img src="./hd-stats.svg" width="620" alt="stats"/>

<div align="center">

<img src="./streak.svg" width="620" alt="Current and longest streak"/>

<img src="./langs.svg" width="620" alt="Top languages by bytes and by repo"/>

<img src="./year.svg" width="620" alt="The last year, one character per day"/>

</div>

<img src="./hd-about-this-page.svg" width="620" alt="about this page"/>

Every graphic here is generated, not embedded from anyone else's server.<br>
`ascii.svg` — the compass — is drawn by<br>
[`scripts/make_wordmark.py`](scripts/make_wordmark.py): the bezel draws itself<br>
in, the needle spins and settles like it's found a direction, then the word<br>
wipes in. The stat graphics and these section headings are drawn by<br>
[a scheduled action](.github/workflows/stats.yml) straight from the GitHub<br>
GraphQL API, once a day, committing only what changed.

They animate with SMIL inside the SVG, because GitHub strips scripts from<br>
READMEs — and since nothing loads from a third party, nothing here can<br>
rate-limit or go dark. The headings are SVGs for the same reason: GitHub also<br>
strips CSS, so an image is the only way to put this page's own typeface on them.

Two typefaces are inlined as base64, since an external font URL can't work<br>
here — the SVGs load through `<img>`, and browsers refuse subresource fetches<br>
for image documents. [JetBrains Mono](scripts/fonts) draws the data graphics<br>
and headings; [Fredoka](scripts/fonts/fredoka-explore.woff2) sets the word<br>
under the compass, subset to just the letters it spells. The compass face<br>
itself is plain SVG shapes, no font involved.

Language totals cover public repositories only. `year.svg` uses the same<br>
character ramp: `:` `+` `#` `@`, quiet to loud.
