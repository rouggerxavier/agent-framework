# Multimodal Realtime Streaming Design

## Informações Gerais
- **Nome do Serviço/Agente:**
- **Provedor LLM:** (ex: Gemini Live API via `google.genai`, OpenAI Realtime)
- **Protocolo de Transporte:** [ ] WebSocket | [ ] gRPC Bidirecional | [ ] WebRTC
- **Modalidades Ativas:** [ ] Áudio (Voz) | [ ] Vídeo/Visão Contínua | [ ] Texto/Eventos

---

## 1. Especificações de Mídia e Codecs
| Parâmetro | Entrada (Inbound) | Saída (Outbound) |
| :--- | :--- | :--- |
| Formato de Áudio | PCM / OGG-Opus | PCM / OGG-Opus |
| Taxa de Amostragem (Hz) | 16000 / 24000 | 24000 |
| Canais | Mono (1 canal) | Mono (1 canal) |
| Tamanho do Chunk / Frame | 100ms / 20ms | Stream contínuo |
| Resolução de Vídeo (se aplicável) | | Não aplicável |

---

## 2. Diagrama de Sequência e Sessão
```text
[Cliente]                      [Backend Gateway]                [Live API / LLM]
    │                                  │                                │
    ├─── 1. Auth & Ephemeral Token ───►│                                │
    │◄── 2. Token concedido ───────────┤                                │
    │                                  │                                │
    ├─── 3. Abre WebSocket Duplex ────►│─── Inicia Sessão Live (gRPC) ─►│
    │                                  │                                │
    ├─── 4. Streaming Chunks Áudio ───►│─── Envia Chunks de Entrada ───►│
    │                                  │                                │
    │◄── 6. Chunks de Áudio Gerado ────│◄── Stream Áudio Resposta ──────┤
    │                                  │                                │
    ├─── 7. User interrompe (Fala) ───►│─── Sinal de Interrupção ──────►│
    │◄── 8. Cancela Áudio Pendente ────│◄── Interrompe Geração ─────────┤
```

---

## 3. Gestão de Latência, Buffering e Barge-in
- **Configuração de VAD (Voice Activity Detection):**
- **Tratamento de Cancelamento de Áudio (Barge-in):**
- **Target de Latência (Time-to-First-Audio):**
- **Estratégia de Reconexão e Heartbeat:**

---

## 4. Chamadas de Ferramentas (Function Calling) em Tempo Real
- **Tools Disponíveis na Sessão:**
- **Comportamento de Áudio durante execução de Tool:** (ex: emitir tom de espera, falar frase de transição)
- **Timeouts e Fallbacks de Tool:**

---

## 5. Custos, Limites e Segurança
- **Duração Máxima da Sessão (Hard Timeout):** (ex: 15 minutos)
- **Política de Privacidade para Áudio Bruto:** (não persistir no disco após o turno)
- **Mecanismo de Fallback para Modo Turn-Based:**
