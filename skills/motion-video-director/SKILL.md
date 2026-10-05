---
name: motion-video-director
description: Use para dirigir, implementar ou auditar video em motion (HyperFrames, Remotion, canvas, Three.js) com ficha de cena, animacao funcao do frame sem relogio/aleatorio e MP4 a 60 FPS quadro a quadro com ffmpeg.
---

# Motion Video Director

## Objetivo
Garantir que todo video em motion siga tres regras juntas e obrigatorias:
direcao de cena explicita, determinismo por numero do quadro e render quadro a
quadro em navegador headless juntado com ffmpeg. Uma regra faltando = video nao
pronto.

## Quando usar
- Ao criar, editar ou revisar video promocional, intro, logo animation, explainer ou reel feito em codigo.
- Ao auditar um projeto Remotion, canvas, WebGL/Three.js ou pagina HTML que vira MP4.
- Antes de entregar um render.

## Quando nao usar
- Microinteracao de UI do produto (hover, transicao de tela); use `ui-ux-pro-max-audit`.
- Detalhe de API do motor: `hyperframes-*` (vendorizados, CLI fixado) ou `remotion-*` (terceiros; nao editar), em especial `remotion-motion-graphics`, `remotion-markup` e `remotion-render`.

## Motor
- **Preferido: HyperFrames** (`skills/hyperframes`, `hyperframes-core`, `hyperframes-cli`): HTML + animacao seekable; o renderer da seek em cada quadro no Chrome headless e codifica com FFmpeg. Render: `HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 npx -y hyperframes@0.8.134 render --fps 60 --quality delivery --output out/video.mp4` (exige FFmpeg no sistema). Siga as regras do framework no topo de cada `hyperframes-*`.
- **Alternativa: Remotion**, quando o projeto ja e Remotion ou precisa de React: composicao com `fps={60}` e o comando quadro a quadro do rubric.

## Regras obrigatorias
1. **Direcao.** Cada cena e descrita como diretor: tipografia cinetica (o que entra, como e em que ritmo), transicao entre formas (morph/encaixe, nao so fade), elementos em 3D ou profundidade (ou a decisao registrada de nao usar), movimento de camera (dolly, zoom, orbita, follow) e a ficha: **duracao em segundos, resolucao e FPS**.
2. **Determinismo.** A animacao e funcao pura do quadro: `estado = f(frame)` (HyperFrames: timeline GSAP/CSS/WAAPI pausada e seekada pelo adapter; Remotion: `useCurrentFrame()`/`interpolate`/`spring`). Proibido relogio (`Date.now`, `new Date()`, `performance.now`, `setTimeout`, `setInterval`, `requestAnimationFrame`, `useFrame` do R3F, CSS `animation`/`transition`/`@keyframes` que corre sozinha, fora de um adapter seekable) e aleatorio sem semente (`Math.random`); use `random(seed)` do Remotion ou PRNG com semente fixa. Fontes e assets carregam antes do quadro (`delayRender`).
3. **Render.** MP4 a **60 FPS**, gerado fotografando cada quadro no navegador headless (avanca o quadro → captura) e juntando com ffmpeg. Nunca gravar a tela (`avfoundation`, `x11grab`, `gdigrab`, `recordVideo` do Playwright, gravador do SO).

## Workflow
1. Escreva a ficha da cena (template no rubric) antes de codar; sem ficha, pare.
2. Implemente com tempo centralizado (uma fonte de `FPS`, duracoes e offsets) e tudo derivado do quadro.
3. Rode o grep de determinismo do rubric; cada ocorrencia sai ou e justificada (ex.: script offline de asset com semente).
4. Prove determinismo: o mesmo quadro renderizado duas vezes (aba nova e depois de seek fora de ordem) da o mesmo hash.
5. Renderize a 60 FPS com o motor escolhido (HyperFrames `render --fps 60`; Remotion, o comando quadro a quadro do rubric); confira com `ffprobe` (fps, resolucao, duracao).
6. Extraia quadros (inicio/fim de cada cena), olhe e corrija antes de entregar.

## Saida obrigatoria
- Ficha de cada cena (segundos, resolucao, FPS, tipografia, transicao, 3D, camera).
- Tabela regra × evidencia `arquivo:linha` × segue/nao segue, preenchida com `../../rubrics/motion-video.md`.
- Saida do grep de determinismo, hashes do teste de quadro repetido e saida do `ffprobe` do MP4.

## Criterios de aceite
- As 3 regras tem evidencia; nenhuma fica "nao verificado".
- Grep de determinismo vazio no codigo da cena (ou excecao justificada fora do codigo da cena).
- `ffprobe` mostra 60 fps, a resolucao e a duracao da ficha.
- Nenhum comando de gravacao de tela no pipeline.

## Arquivos de apoio
- Rubric: ../../rubrics/motion-video.md
- HyperFrames (vendorizado @ 0d5e395, CLI 0.8.134): `hyperframes`, `hyperframes-core`, `hyperframes-cli`, `hyperframes-animation`, `hyperframes-keyframes`; detalhes em `../../docs/hyperframes.md`
- Remotion (terceiros, so referenciar): `remotion-motion-graphics`, `remotion-markup`, `remotion-render`

## Exemplos de uso
- Codex: `$motion-video-director Audite o video em motion/ contra as 3 regras.`
- Claude Code: `/motion-video-director Dirija a cena de abertura de 4 s em 1920x1080 a 60 FPS.`
