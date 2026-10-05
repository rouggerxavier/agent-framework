---
name: hyperframes-creative
description: Use para direcao criativa nao animada em HyperFrames: design spec, paleta, tipografia, narracao, beats e padroes de composicao.
---

# HyperFrames Creative (agent-framework)

> Vendorizado de https://github.com/heygen-com/hyperframes @ 0d5e395 (Apache-2.0, ver `LICENSE`), CLI `hyperframes@0.8.134`.
> Trocado so o frontmatter e acrescentadas as secoes "Objetivo", "Regras do agent-framework", "Workflow", "Saida" e "Criterios";
> o corpo upstream vem depois da linha `<!-- upstream -->`, sem alteracao.

## Objetivo
Definir a direcao visual e o ritmo de um video HyperFrames.

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

# HyperFrames Creative

Brand, pacing, style, narration, and composition direction. Use after the technical contract from `hyperframes-core` is in place.

For motion patterns, scene blueprints, transitions, and CSS marker effects, use `hyperframes-animation` — this skill is intentionally non-animation.

> **Read these two FIRST for any non-trivial composition — they override web instincts:**
>
> - `references/house-style.md` — "interpret the prompt, generate real content," the lazy-default list, and the background/foreground layer recipe. This is what turns a literal restyle into a _concept_.
> - `references/video-composition.md` — video-medium scale, depth, and foreground detail. It explains how to avoid empty web-page layouts without imposing a universal element count.
>
> Skipping these is the single biggest cause of generic, web-page-looking output. They are not optional rows in the routing table below — for anything beyond a one-line edit, open both before you choose colors or write HTML.

## Workflow

1. If a project has a design spec, **read it first** and treat its frontmatter tokens as brand truth (colors, fonts, spacing, tone, constraints). Which file to read (precedence `frame.md` → `design.md` → `DESIGN.md`) and how to parse it (frontmatter = normative, prose = context) are defined once in [`references/design-spec.md`](references/design-spec.md) — resolve and load per that doc.
2. If no design spec exists and the user asks for visual direction, choose a route:
   - Ready-made frame-preset (optional) → `frame-presets/` (adopt a `FRAME.md` as `frame.md`; see `references/design-spec.md`)
   - Named style or mood → `references/visual-styles.md`
   - Fast defaults → `references/house-style.md`
   - Interactive selection → `references/design-picker.md`
3. For multi-scene work, plan beats and rhythm before writing HTML → `references/beat-direction.md`. For scene transitions, jump to `hyperframes-animation/transitions/`.
4. For motion-heavy work, read `references/motion-principles.md` (high-level guardrails), then go to `hyperframes-animation` for atomic rules.

## Routing

| Topic                                                                                                   | Read                                           |
| ------------------------------------------------------------------------------------------------------- | ---------------------------------------------- |
| Adopt a ready-made frame-preset as `frame.md` (optional)                                                | `frame-presets/` · `references/design-spec.md` |
| Default palettes, motion, typography, lazy defaults to question                                         | `references/house-style.md`                    |
| Named style presets, mood-to-style routing                                                              | `references/visual-styles.md`                  |
| Palette-specific color tokens                                                                           | `palettes/*.md`                                |
| Composition patterns — PiP, text-behind-subject, title card, slide show                                 | `references/composition-patterns.md`           |
| Stats / infographic presentation                                                                        | `references/data-in-motion.md`                 |
| Structured expansion for open-ended prompts                                                             | `references/prompt-expansion.md`               |
| Video-medium density, scale, color, frame composition                                                   | `references/video-composition.md`              |
| Per-beat direction, rhythm planning, transition timing                                                  | `references/beat-direction.md`                 |
| Post-authoring spec verification (colors, type, corners, spacing, depth)                                | `references/design-adherence.md`               |
| High-level motion guardrails and GSAP-quality rules                                                     | `references/motion-principles.md`              |
| Font selection, pairings, rendered-video type guardrails                                                | `references/typography.md`                     |
| Story doctrine — hook language, value-before-evidence, storyboard-as-proposal, source-traceable visuals | `references/story-spine.md`                    |
| Script pacing, tone, openings, number pronunciation                                                     | `references/narration.md`                      |
| Precomputed audio bands mapped to motion                                                                | `references/audio-reactive.md`                 |

## Scripts

- `scripts/contrast-report.mjs` — inspect contrast warnings from rendered frames.
- `scripts/extract-audio-data.py` — pre-extract audio bands for audio-reactive compositions.
- `scripts/package-loader.mjs` — support script for bundled creative tooling.

`contrast-report.mjs` resolves helper packages from the current project first, then can bootstrap the bundled HyperFrames package version. Set `HYPERFRAMES_SKILL_PKG_VERSION=<version>` only when running the skill outside the bundled CLI/skill install and you need to pin that bootstrap version explicitly.

Run with explicit paths, for example:

```bash
python <SKILL_DIR>/scripts/extract-audio-data.py <audio-file>
```

Animation analysis (`animation-map.mjs`) lives in `hyperframes-animation/scripts/`.

## Boundaries

- Do not override `hyperframes-core` technical rules.
- Do not require a design system for a minimal technical composition.
- Do not add extra scenes, narration, music, captions, or transitions unless the request calls for them or you first propose the expansion.
- Keep recipe references task-specific; do not read every reference for simple edits.
