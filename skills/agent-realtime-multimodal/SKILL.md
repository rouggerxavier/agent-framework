---
name: agent-realtime-multimodal
description: Use para arquitetar e implementar fluxos de streaming bidirecional em tempo real para agentes de IA, cobrindo voz e áudio (PCM, OGG/Opus), visão contínua, WebSockets/gRPC e integração com Gemini Live API.
---

# Agent Realtime Multimodal

## Objetivo
Projetar e implementar arquiteturas de agentes com interação multimodal em tempo real (áudio bidirecional de baixa latência e visão contínua), utilizando protocolos de streaming (WebSockets, gRPC, WebRTC) e APIs nativas (como Gemini Live API / Multimodal Live Service).

## Quando usar
- Ao desenhar agentes com conversação por voz interativa (fala com interrupção em tempo real / *barge-in*).
- Para integrar suporte a áudio inbound/outbound contínuo (ex: WhatsApp PTT, chamadas WebRTC, streams OGG/Opus ou PCM).
- Ao processar feeds de vídeo ou screenshots em tempo real para agentes de suporte visual e inspeção.
- Ao estruturar gerenciamento de sessão, troca de contexto e reconexão em conexões de longa duração.
- Para definir arquitetura de buffer de áudio, detecção de atividade de voz (VAD) e fallback para modo turn-based.

## Quando nao usar
- Para processamento assíncrono de áudio batch (ex: apenas transcrever um arquivo estático com Whisper/STT; use chamadas de API padrão).
- Para chatbots puramente textuais sem streaming contínuo de mídia.
- Para tarefas de geração de imagem ou edição de vídeo estático (use `hyperframes` ou skills de mídia).

## Entradas esperadas
- Modos de entrada e saída requeridos (áudio para áudio, texto para áudio, visão + áudio para áudio).
- Formatos e taxas de amostragem de áudio (ex: PCM 16-bit 16kHz/24kHz, OGG/Opus, chunk size).
- Restrições de latência (ex: Time-to-First-Audio < 800ms) e largura de banda.
- Provedor de modelo (ex: Gemini Live API via `google.genai`, OpenAI Realtime, ou servidor local).

## Workflow
1. **Definição da topologia de conexão e transporte:**
   - Selecionar o canal de transporte: WebSockets com duplex completo ou streaming bidirecional gRPC.
   - Definir handshake de autenticação (troca de token efêmero para conexões de cliente, sem expor chaves de API mestre no frontend).
   - Estabelecer heartbeat (*ping/pong*) e política de reconexão resiliente.

2. **Gerenciamento de streams de áudio e mídia:**
   - Entrada: padronizar codificação (PCM 16-bit mono 16kHz ou 24kHz; empacotamento OGG/Opus quando pelo canal WhatsApp).
   - Implementação de buffers e chunks de áudio com mínimo de overhead.
   - Saída: streaming contínuo de áudio para o cliente, decodificação incremental e sincronização com transcrição textual para logging.

3. **Interrupção e detecção de voz (Barge-in / Turn Handling):**
   - Configurar VAD (Voice Activity Detection) e sinais de interrupção: quando o usuário fala por cima da resposta da IA, o streaming de saída deve ser cancelado imediatamente e o buffer limpo.
   - Tratar mensagens de `interrupted` no protocolo de streaming do modelo.

4. **Gerenciamento de Tools e Estado durante streaming:**
   - Definir como chamadas de ferramentas (*function calling*) ocorrem no fluxo contínuo sem travar o áudio do usuário.
   - Isolar o contexto de memória da sessão e salvar resumos consolidados ao término da conexão.

5. **Consolidar design técnico e limites de segurança:**
   - Preencher `templates/multimodal-streaming-design.md`.
   - Estabelecer salvaguardas: timeout de inatividade, limites máximos de duração de sessão para controle de custos, e política de privacidade para não retenção de raw audio.

## Saida obrigatoria
- Documento de design técnico contendo:
  - Diagrama de sequência de handshake e streaming de mídia.
  - Especificação dos codecs de entrada e saída (amostragem, chunking).
  - Mecanismo de barge-in / cancelamento de fala.
  - Estratégia de fallback para falha de conexão (reversão para turnos texto/áudio gravado).
  - Análise de latência e orçamento de custos da sessão.

## Criterios de aceite
- Nenhum segredo ou chave mestra trafega desprotegida para o cliente final.
- O fluxo trata reconexões e interrupções sem memory leak nos buffers de áudio.
- Há mecanismo de fallback claro se a conexão de baixa latência falhar.
- O formato de áudio respeita os limites e especificações do modelo e do canal.

## Arquivos de apoio
- Template: `templates/multimodal-streaming-design.md`
- Rubrics: `rubrics/architecture.md`, `rubrics/security-privacy.md`

## Exemplos de uso
- "Projete o pipeline de streaming de áudio do Gemini Live API para o atendente por voz."
- "Como tratar interrupções do usuário (barge-in) e cancelamento de resposta no WebSocket do agente?"
- "Estruture o gateway de mídia para converter áudio de WhatsApp OGG/Opus em streaming de tempo real."
