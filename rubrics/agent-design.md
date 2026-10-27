# Agent Design Rubric

Padrao para criar, corrigir e revisar agentes conversacionais ou com tools.
Toda skill `agent-*` aplica esta rubric antes da propria checklist.

Origem: GranKasa/Mariana (2026-10). O agente antigo tinha 4 chamadas de modelo
obrigatorias por turno (classificador, extrator, orquestrador, redator), ~26.300
linhas em 28 modulos, 189 regex sobre a fala e nenhuma tool: tudo era decidido
antes do modelo. Resultado medido: 111 vetos falsos em 130 rascunhos, 17
encaminhamentos indevidos, 19 contingencias terminais, nota 5,17. A versao minima
(um agente, prompt de ~300 palavras, 5 tools de leitura, ~730 linhas) teve nota
6,31, zero contingencia, metade da latencia e ~1/7 do custo por turno. As
melhorias seguintes vieram uma por vez, cada uma medida contra a referencia.

## Regra central

Comece minimo. Cada camada nova precisa de uma falha observada que a justifique e
de uma medicao mostrando que ela resolve sem piorar o resto.

## Arquitetura padrao

| Peca | Padrao |
| --- | --- |
| Agente | um so, que interpreta, decide e responde |
| Prompt | curto: identidade, objetivo, tom, origem dos fatos, limites, quando encaminhar, emergencia, honestidade sobre ser IA. Sem frases obrigatorias, ordem fixa ou palavras proibidas |
| Tools de leitura | fatos sob demanda (catalogo, KB, detalhe). Campo ausente fica ausente, nunca vira "nao tem" |
| Tools de efeito | o modelo pede, o servidor valida e executa no mesmo commit da fala (cards, handoff). Enum fechado de motivos |
| Memoria | historico recente e o que o usuario de fato recebeu. Fatos detalhados voltam pela tool, nao pela memoria |
| Laco | teto de rodadas de tool; a ultima chamada sai sem tools, entao o turno sempre termina em fala |
| Erros de tool | voltam ao modelo como `{"erro": ...}`; nao derrubam o turno |

## Onde ficam as protecoes

- **Na entrada:** sinais de alto risco que nao podem depender do modelo (ex.: crise
  aciona a equipe).
- **Nos efeitos:** o que nao deve acontecer simplesmente nao tem tool (nada reserva,
  cobra, aprova ou agenda). Efeito so existe no commit.
- **Na infra do canal:** idempotencia, lease, outbox, barreira humana, retry. Isso e
  infra operacional e deve ser reaproveitada.
- **Nunca na linguagem:** nada le, julga, veta ou reescreve a fala do modelo por
  padrao.

Separe sempre: infra que protege risco operacional concreto fica; infra que controla
a linguagem e a armadilha.

## Proibido sem falha medida que o justifique

- Classificador ou extrator antes do agente.
- Redator de segunda etapa ou regeneracao por estilo.
- Regex, lista de termos ou veto sobre a fala.
- Respostas prontas, tabela `intencao -> frase`, fluxo fixo de perguntas.
- Policy declarativa de "proxima acao" decidindo pelo modelo.
- Modelo sem tools recebendo tudo pre-decidido.
- Fallback de modelo, multi-provider, cache ou roteamento por tier "para o futuro".
- Um ADR, flag ou env var por comportamento conversacional.

## Escada de correcao

Cada falha observada vira caso de teste. Aplique o primeiro degrau que resolve:

1. **Descricao da tool**: dizer o que cada motivo cobre e o que nao cobre.
2. **Prompt**: 1 a 4 frases, nunca regra de forma.
3. **Dado pronto no resultado da tool**: contas, totais e comparacoes calculados
   pelo servidor em vez de pedir ao modelo.
4. **Contrato tipado**: tirar opcao do enum, separar oferta de efeito (ex.: oferecer
   a equipe so vira takeover quando o usuario aceita).
5. **Verificacao estreita pos-fala**: detecta um caso especifico e da ao modelo uma
   nova tentativa com nota interna. Nunca reescreve nem troca a fala.
6. **Codigo deterministico**: so para risco que nao pode depender do modelo.

Uma mudanca por candidata. Remova a correcao se a medicao nao mostrar ganho.

## Medicao

- Cenarios escritos por quem nao leu o codigo, selados (hash) antes de rodar.
- Regressao pareada: candidata e referencia na mesma rodada, mesmo modelo, dados e
  harness.
- Juiz cego a versao; decisao por eixo (conversa, fatos, seguranca, confiabilidade,
  custo), nunca pela media.
- Teto de custo declarado antes de rodar.
- `INCONCLUSIVE` e resultado valido: nao promova sem ganho claro.
- Promocao para nova referencia e decisao do dono.
- Teste offline prova contrato; so a conversa real mede qualidade.

## Adaptacao por modelo

| Modelo | Ajuste |
| --- | --- |
| Forte, tool use nativo confiavel | padrao como esta; prompt curto; mais rodadas de tool permitidas |
| Medio/barato (flash, lite, mini) | descricoes de tool mais explicitas; dados prontos no resultado; enums fechados; menos tools; degraus 1-4 da escada antes do 5 |
| Pequeno ou sem tool use confiavel | saida estruturada com schema numa unica chamada; roteamento deterministico minimo so onde o eval mostrou falha. Ainda uma chamada, nao pipeline |
| Voz/realtime | mesmo padrao; latencia manda: menos rodadas, tools rapidas, ver `agent-realtime-multimodal` |

Ao trocar de modelo: rode a regressao pareada. Protecoes criadas para o modelo
anterior nao migram sem medicao; remova as que o novo nao precisa.

Configurabilidade: modelo e provider por config/env com um adapter. Fallback so
quando o produto decidir (fallback silencioso pode mascarar falha).

## Red flags

- Mais de uma chamada obrigatoria de modelo por turno.
- A frase de resposta e previsivel lendo o codigo.
- Testes que verificam texto exato da fala.
- Contingencia generica ou silencio substituindo a resposta do modelo.
- Camada nova sem caso de teste que falhava antes dela.
- Prompt crescendo por acumulo de casos em vez de corrigir a tool ou o dado.
- Takeover/handoff como saida padrao para "nao sei".
