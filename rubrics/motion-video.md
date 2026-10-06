# Motion Video Rubric

Use com `skills/motion-video-director`. As tres regras sao obrigatorias e juntas.

## Ficha da cena (uma por cena)
```yaml
cena: 01-hook
duracao_s: 1.5          # e o total do video
resolucao: 1920x1080
fps: 60
tipografia_cinetica:    # o que entra, como (mascara, palavra a palavra), stagger
transicao_de_formas:    # morph/encaixe entre formas; nao so opacity
elementos_3d:           # objeto, profundidade, luz; ou "nenhum: <motivo>"
camera:                 # dolly, zoom, orbita, follow; de onde para onde
```

## Checklist
### 1. Direcao
- [ ] Toda cena tem ficha com `duracao_s`, `resolucao` e `fps`.
- [ ] Tipografia cinetica, transicao de formas, 3D (ou decisao registrada) e camera descritos.
- [ ] A ficha bate com o codigo (FPS, largura/altura e duracao da composicao).

### 2. Determinismo
- [ ] Grep vazio no codigo da cena (no HyperFrames, `@keyframes`/`animation:` e GSAP sob o adapter seekable sao permitidos; relogio e aleatorio nao):
  ```bash
  grep -rnE "Date\.now|new Date\(|performance\.now|Math\.random|setTimeout|setInterval|requestAnimationFrame|useFrame|@keyframes|animation:|transition:" src/
  ```
- [ ] Aleatorio so com semente (`random("id")` do Remotion ou PRNG semeado).
- [ ] Mesmo quadro, duas renderizacoes (aba nova e apos seek fora de ordem) = mesmo sha256.

### 3. Render
- [ ] Quadros capturados um a um em navegador headless (avanca quadro → screenshot), nunca gravacao de tela:
  ```bash
  grep -rnE "avfoundation|x11grab|gdigrab|recordVideo|screencapture" .
  ```
- [ ] Comando de referencia, preferido (HyperFrames; seek por quadro no Chrome headless + FFmpeg do sistema):
  ```bash
  HYPERFRAMES_NO_TELEMETRY=1 DO_NOT_TRACK=1 npx -y hyperframes@0.8.134 render --fps 60 --quality delivery --output out/video.mp4
  ```
- [ ] Alternativa (Remotion: composicao com `fps={60}`; sem ffmpeg no sistema, use `npx remotion ffmpeg`):
  ```bash
  npx remotion render src/index.ts Promo out/frames --sequence --image-format=png --image-sequence-pattern='frame-[frame].[ext]'
  ffmpeg -y -framerate 60 -i out/frames/frame-%04d.png [-i audio.wav -map 0:v -map 1:a -c:a aac -shortest] \
    -c:v libx264 -pix_fmt yuv420p -crf 16 -r 60 out/video.mp4
  ```
  Fora do Remotion: a pagina expoe `window.renderFrame(n)` puro; o script headless (Playwright/Puppeteer) chama `renderFrame(n)` e `page.screenshot()` para `n = 0..fps*segundos-1` e o ffmpeg acima junta.
  `npx remotion render` direto (MP4) tambem vale: e captura quadro a quadro + ffmpeg embutido.
- [ ] `ffprobe -v error -select_streams v:0 -show_entries stream=r_frame_rate,width,height,duration -of csv=p=0 out/video.mp4` mostra `60/1`, a resolucao e a duracao da ficha.

## Saida recomendada
| Regra | Onde (arquivo:linha) | Segue? | Evidencia |
|---|---|---|---|
