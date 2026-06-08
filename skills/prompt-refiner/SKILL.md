---
name: prompt-refiner
description: Use para transformar pedidos brutos em prompts claros, testaveis e especificos para Codex, Claude Code, ChatGPT ou agentes.
---

# Prompt Refiner

## Objetivo
Converter uma intencao ambigua em prompt operacional com contexto, escopo, restricoes, saida esperada e criterios de aceite.

## Quando usar
- Antes de delegar tarefa para agente ou modelo.
- Quando o pedido tem ambiguidade, escopo amplo ou formato de saida indefinido.
- Quando e preciso adaptar o mesmo pedido para Codex, Claude Code ou ChatGPT.
- Quando o prompt precisa mudar de formato conforme a acao: implementation, debug, review, research, agent-build, runtime-qa ou security-audit.

## Quando nao usar
- Para tarefas triviais que ja estao claras.
- Para substituir leitura de codigo ou validacao real.
- Para esconder incertezas; marque-as explicitamente.

## Entradas esperadas
- Prompt original ou ideia solta.
- Ferramenta alvo.
- Resultado desejado, restricoes e contexto minimo.
- Modo da acao, se conhecido.

## Workflow
1. Escolha o modo: `implementation`, `debug`, `review`, `research`, `agent-build`, `runtime-qa`, `security-audit` ou `general`.
2. Extraia objetivo, contexto, escopo, restricoes e stop conditions.
3. Separe requisitos obrigatorios de preferencias.
4. Remova conflitos, ambiguidades e contexto desnecessario.
5. Adicione tools permitidas, output contract, criterios de aceite e verificacao proporcional ao risco.
6. Gere versao pronta para uso no alvo escolhido.

## Modos
| Modo | Foco do prompt | Verificacao minima |
| --- | --- | --- |
| `implementation` | arquivos, escopo, constraints, testes e review | comando/teste ou diff review |
| `debug` | reproducao, sintomas, hipoteses, logs e regressao | repro antes/depois |
| `review` | diff, risco, contratos, seguranca e testes faltantes | achados por severidade |
| `research` | pergunta, fontes permitidas, recencia e incertezas | citacoes ou evidencia |
| `agent-build` | objetivo, tools, memoria, modelo, guardrails e evals | agent design + runtime QA |
| `runtime-qa` | app/agente rodando, fluxos, erro e evidencias | passos executados |
| `security-audit` | dados, auth, secrets, permissoes e logs | achados + mitigacoes |
| `general` | objetivo claro e saida esperada | aceite simples |

## Saida obrigatoria
Para prompt simples, preencha `../../templates/prompt-package.md`. Para prompt por modo de acao, preencha `../../templates/action-prompt-package.md`.

## Criterios de aceite
- O prompt deve ser executavel sem explicacao adicional.
- Deve limitar escopo e preservar contexto essencial.
- Deve incluir verificacao quando houver codigo, UI, API ou release.
- Nao deve inventar contexto ausente.

## Arquivos de apoio
Nao copie a estrutura do pacote na skill; use o template.
- Template: ../../templates/prompt-package.md
- Template por acao: ../../templates/action-prompt-package.md
- Prompt de agente: ../../skills/agent-prompt-refiner/SKILL.md

## Exemplos de uso
- Codex: `$prompt-refiner Melhore este pedido para uma tarefa de bugfix.`
- Claude Code: `/prompt-refiner Transforme esta ideia em prompt para refatoracao segura.`
