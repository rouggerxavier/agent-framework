# HyperFrames no agent-framework

Motor preferido de render do `motion-video-director` (Remotion e a alternativa).
HTML + animacao seekable → MP4 deterministico: o renderer da seek em cada quadro no
Chrome headless e codifica com FFmpeg.

## Origem fixada
- Repo: https://github.com/heygen-com/hyperframes @ `0d5e395cd31d0f491e9b26d0da110da6e231c512` (Apache-2.0).
- CLI: `hyperframes@0.8.134` no npm (gitHead `0dc957f`, ancestral do `0d5e395`, sem diferenca em `packages/cli`).
- Vendorizados em `skills/` (core, sem `media-use`): `hyperframes`, `hyperframes-core`, `hyperframes-cli`,
  `hyperframes-animation`, `hyperframes-audio`, `hyperframes-creative`, `hyperframes-keyframes`,
  `hyperframes-registry`, `hyperframes-studio`. Cada um tem `LICENSE` e um cabecalho do framework;
  o corpo upstream fica depois de `<!-- upstream -->`, sem alteracao.
- Fora: `media-use` (scripts com telemetria PostHog ligada por padrao, que associa o email da conta
  HeyGen) e os workflows fora do core.

## Neutralizacoes (camada do framework, no cabecalho de cada skill)
| Upstream | No framework |
|---|---|
| `npx hyperframes …` / `@latest` | `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 HYPERFRAMES_NO_UPDATE_CHECK=1 HYPERFRAMES_NO_AUTO_INSTALL=1 HYPERFRAMES_SKIP_SKILLS=1 npx -y hyperframes@0.8.134 …` |
| Telemetria do CLI (PostHog, ligada por padrao) | desligada pelas variaveis acima em cada comando; `install-all.sh` tambem as exporta (vale so para o proprio instalador) |
| `npx hyperframes feedback` (envia o texto da busca) | nao usar |
| `npx hyperframes usage` (le tokens OAuth do Claude Code no Keychain e de `~/.codex/auth.json`) | nao usar |
| `upgrade`, `skills update`/`add` | nao usar; atualizar = revendorizar num commit novo |
| `curl …/hyperframes/main/registry/registry.json` e registry padrao em `main` | `"registry": "https://raw.githubusercontent.com/heygen-com/hyperframes/0d5e395cd31d0f491e9b26d0da110da6e231c512/registry"` no `hyperframes.json` |
| `package-loader.mjs` cai em `@latest` em install global | exportar `HYPERFRAMES_SKILL_PKG_VERSION=0.8.134` |

## Requisitos
Node.js 22+ e FFmpeg no sistema. Nada e instalado globalmente; o CLI roda por `npx -y`.

## Instalacao oficial (nao usada aqui)
`claude plugin marketplace add heygen-com/hyperframes` + `claude plugin install hyperframes@hyperframes`,
ou `npx hyperframes skills update`. Ambas puxam a versao mais nova e trazem `media-use`; so com
decisao explicita do usuario.

## Atualizar
Clonar o repo num commit novo, revisar scripts/rede/telemetria, recopiar os 9 skills, manter o
cabecalho e trocar SHA e versao aqui, nos cabecalhos e em `motion-video-director`/`rubrics/motion-video.md`.
