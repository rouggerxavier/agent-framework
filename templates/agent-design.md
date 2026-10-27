# Agent Design

Siga `rubrics/agent-design.md`. Campo sem risco concreto: escreva "nao se aplica".

## Objective

## Users / Channel
-

## Model
- Modelo e tier (forte / medio / pequeno):
- Ajustes pelo tier:
- Config (env/adapter):
- Fallback: nenhum | decidido pelo produto porque...

## Turn Loop
- Chamadas obrigatorias por turno: 1
- Teto de rodadas de tool:
- Ultima chamada sem tools: sim

## Prompt
- Identidade e objetivo:
- Origem dos fatos:
- Limites comerciais/de dominio:
- Quando encaminhar:
- Emergencia:
- Tamanho (palavras):

## Tools
| Tool | Tipo (leitura/efeito) | Entrada | Saida | Garantia do servidor |
| --- | --- | --- | --- | --- |
|  |  |  |  |  |

Efeitos que NAO tem tool, de proposito:
-

## Memory
- Historico (quantas mensagens, filtro):
- Estado guardado:
- O que volta pela tool em vez da memoria:

## Protections
| Risco nomeado | Onde (entrada / efeito / infra) | Como | Teste |
| --- | --- | --- | --- |
|  |  |  |  |

## What Does Not Exist On Purpose
- classificador, extrator, redator, regex sobre a fala, regeneracao por veto:

## Reused Infra
-

## Measurement
- Testes offline (contrato):
- Cenarios de conversa (selados?):
- Referencia comparada:
- Eixos e criterio de decisao:
- Teto de custo:

## Known Risks
-
