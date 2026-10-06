---
name: hyperframes-animation
description: Use para animacao em HyperFrames: regras de movimento, blueprints de cena, transicoes e adapters seekable (GSAP, Lottie, Three.js, Anime.js, CSS, WAAPI).
---

# HyperFrames Animation (agent-framework)

> Vendorizado de https://github.com/heygen-com/hyperframes @ 0d5e395 (Apache-2.0, ver `LICENSE`), CLI `hyperframes@0.8.134`.
> Trocado so o frontmatter e acrescentadas as secoes "Objetivo", "Regras do agent-framework", "Workflow", "Saida" e "Criterios";
> o corpo upstream vem depois da linha `<!-- upstream -->`, sem alteracao.

## Objetivo
Animar composicoes HyperFrames com runtimes seekable (funcao do tempo, nao do relogio).

## Regras do agent-framework (prevalecem sobre o corpo upstream)
- CLI fixado: rode sempre `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_AUTO_INSTALL=1 HYPERFRAMES_SKIP_SKILLS=1 npx -y hyperframes@0.8.134 <comando>`. Onde o corpo diz `npx hyperframes` ou `npx hyperframes@latest`, use isto (e o "wrapper" que o upstream manda obedecer).
- Nao rode: `feedback` (envia o texto da busca), `usage` (le os tokens OAuth do Claude Code/Codex/Grok), `upgrade`, `skills update`/`skills add`, `telemetry enable`; `auth`, `cloud`, `lambda`, `cloudrun` e `publish` so com pedido explicito do usuario.
- Registry fixado: no `hyperframes.json` do projeto use `"registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/0d5e395cd31d0f491e9b26d0da110da6e231c512/registry"`; no lugar do `curl .../main/registry/registry.json`, use essa URL + `/registry.json`.
- Nao vendorizados: `/media-use` (telemetria propria) e os workflows fora do core (product-launch-video, pr-to-video etc.). Nao instale; diga ao usuario que nao estao disponiveis.
- Scripts que instalam dependencias (`scripts/package-loader.mjs`) pedem confirmacao; antes, exporte `HYPERFRAMES_SKILL_PKG_VERSION=0.8.134`.
- Render final a 60 FPS (`render --fps 60`), seguindo `motion-video-director` e `rubrics/motion-video.md`.

## Workflow
1. Aplique as regras acima a todo comando do corpo upstream.
2. Siga o corpo upstream abaixo.
3. Para video final, valide com o checklist de `../../rubrics/motion-video.md`.

## Saida
A do corpo upstream, com os comandos ja na forma fixada.

## Criterios de aceite
- Nenhum comando usou `npx hyperframes` sem `@0.8.134` nem sem as variaveis de opt-out.
- Nenhuma chamada a `feedback`, `usage`, `upgrade` ou `skills update/add`; registry so pela URL fixada.

<!-- upstream -->

**Plugin installs:** Before setup or freshness commands, follow [plugin execution rules](../hyperframes/references/plugin-installation.md) when this skill is inside a HyperFrames plugin. Standalone installs keep the update instructions below.

# HyperFrames Animation

All motion knowledge in one skill: **rules** (atomic recipes), **blueprints** (multi-phase scene templates), **transitions** (scene-to-scene), **techniques** (broader motion-design patterns), and **adapters** (per-runtime APIs).

For the composition contract (data attributes, sub-compositions, determinism) see `hyperframes-core`.

## Default: compose atomic rules

Pick 2-4 rules from `rules-index.md`, glue them together with a single paused GSAP timeline, done. This is faster and produces less code than starting from a blueprint.

## Load a blueprint when

- The scene matches an existing pre-designed multi-phase template (brand-reveal, social-proof, etc.) and reusing its phase pipeline saves real authoring time
- You want runnable ground-truth code for a complex 4-5 phase choreography

Blueprints live in `blueprints-index.md`. Each entry points to `blueprints/<id>.md` (recipe). Do not read it speculatively; load it when you've already decided you need scene-level orchestration.

## Routing

| Want to…                                                                       | Read                                                |
| ------------------------------------------------------------------------------ | --------------------------------------------------- |
| Pick an atomic motion pattern by trigger / tag                                 | `rules-index.md`                                    |
| Read one rule's full HTML / CSS / GSAP recipe                                  | `rules/<name>.md`                                   |
| Pick a multi-phase scene template                                              | `blueprints-index.md`                               |
| Read one blueprint's full recipe                                               | `blueprints/<id>.md`                                |
| Author a scene transition (CSS-driven, between two clips)                      | `transitions/overview.md`, `transitions/catalog.md` |
| Look up a broader motion-design technique                                      | `techniques.md`                                     |
| Motion blur — shutter smear on an element, and when not to use it              | `references/motion-blur.md`                         |
| Analyze an existing composition's animation map                                | `scripts/animation-map.mjs`                         |
| GSAP API — timeline / tweens / position parameters                             | `adapters/gsap.md`                                  |
| GSAP — drop-in effect recipes                                                  | `rules/gsap-effects.md`                             |
| GSAP — transforms / perf                                                       | `adapters/gsap-transforms-and-perf.md`              |
| GSAP — eases / stagger                                                         | `adapters/gsap-easing-and-stagger.md`               |
| GSAP — timeline / labels                                                       | `adapters/gsap-timeline-and-labels.md`              |
| Lottie / dotLottie (After Effects exports, `window.__hfLottie`)                | `adapters/lottie.md`                                |
| Character animation (walk cycle, mascot, jointed puppet, gestures)             | `adapters/lottie.md` → Characters                   |
| Three.js / WebGL (3D scenes, `AnimationMixer`, `hf-seek`)                      | `adapters/three.md`                                 |
| Anime.js (`window.__hfAnime`)                                                  | `adapters/animejs.md`                               |
| CSS keyframes (`animation-delay` / `play-state` / `fill-mode`)                 | `adapters/css-animations.md`                        |
| Web Animations API (`element.animate()`, `currentTime` seek)                   | `adapters/waapi.md`                                 |
| TypeGPU / WebGPU (`navigator.gpu`, WGSL, compute pipelines)                    | `adapters/typegpu.md`                               |
| HTML-as-texture + WebGL/GLSL post-fx (capture live DOM via `drawElementImage`) | `adapters/html-in-canvas-patterns.md`               |
| Named text-animation effects (24 IDs via external `animate-text` skill)        | `adapters/animate-text.md`                          |

## Picking a runtime

- **GSAP** is the default for 95% of motion work — covers timeline orchestration, transforms, easing, stagger. All atomic rules in this skill are GSAP-based.
- **Lottie** when an asset has its own pre-baked timeline (typically After Effects exports), including characters that walk, gesture or react.
- **Three.js** for 3D scenes, camera motion, shader-driven visuals.
- **Anime.js** for lightweight tweening when GSAP is overkill.
- **CSS** for simple repeated motifs, decoration, shimmer — no JavaScript animation cost.
- **WAAPI** for native browser keyframes without a GSAP dependency.
- **TypeGPU / WebGPU** for GPU-rendered canvases (particles, liquid glass, custom shaders).

Multiple runtimes can coexist in one composition. Each registers its instances on the runtime-specific global so HyperFrames can seek all of them in one pass.

## Critical Constraints

**Prerequisite: `hyperframes-core` → One paused timeline + Non-negotiable rules** (single paused timeline, `data-duration` governs length, no `Math.random` / `Date.now` / `performance.now`, no `repeat: -1` without a finite root `data-duration`, no page-load `gsap.set` on later-scene clips, no `display` or raw `visibility` tweens, and register the timeline only after it is fully built, including when the build runs inside an async callback such as `document.fonts.ready`). GSAP `autoAlpha` and zero-duration visibility sets at explicit timeline boundaries remain allowed by core. Use those exceptions only on non-clip elements or wrappers inside a clip; the framework owns `.clip` lifecycle. Don't restate the full contract here.

Animation-craft additions on top of core's contract:

- **Pre-calculated layout constants** — never derive positions from `getBoundingClientRect()` at tween time. Tween-time DOM measurements desync because the renderer samples in parallel; compute coordinates once at composition setup and reuse.
- **Spatial motion uses GSAP transform aliases only** (`x`, `y`, `scale`, `rotation`). Core's allowlist also permits `opacity` / `color` / `backgroundColor` / `borderRadius` for non-spatial property tweens — but never `width` / `height` / `top` / `left` for layout changes.

## Scripts

```bash
node <SKILL_DIR>/scripts/animation-map.mjs <composition-dir> \
  --out <composition-dir>/.hyperframes/anim-map
```

Reads every GSAP timeline registered on `window.__timelines`, enumerates tweens, samples bboxes, computes flags, outputs `animation-map.json`. Use it to audit choreography (dead zones, stagger consistency, lifecycle warnings) after authoring.

`animation-map.mjs` resolves helper packages from the current project first, then can bootstrap the bundled HyperFrames package version. Set `HYPERFRAMES_SKILL_PKG_VERSION=<version>` only when running the skill outside the bundled CLI/skill install and you need to pin that bootstrap version explicitly.

## See Also

- `hyperframes-core` — composition structure, data attributes, sub-compositions, deterministic render contract
- `hyperframes-creative` — palettes, typography, narration, beat planning (non-animation creative direction)
- `hyperframes-cli` — `npx hyperframes lint / check / snapshot / preview / render`
