---
name: agent-builder
description: Use para criar ou refatorar agentes (chat, WhatsApp, tools, assistente) comecando pela versao minima - um agente, prompt curto, tools - e so adicionando camadas por falha medida.
---

# Agent Builder

## Objetivo
Construir ou refatorar agentes pela menor arquitetura que faz o trabalho: um agente,
prompt curto, tools de leitura e efeitos executados pelo servidor. Camadas extras so
entram quando uma falha medida as justifica. Regra completa em
`../../rubrics/agent-design.md`.

## Quando usar
- Ao criar agente novo, subagente, assistente conversacional ou workflow agentico.
- Ao refatorar agente com pipeline de varias chamadas, vetos sobre a fala ou fluxo
  rigido.
- Ao decidir onde colocar uma protecao nova num agente existente.

## Quando nao usar
- Prompt simples sem tools, estado ou runtime.
- Ajuste pontual de comportamento ja medido: use `agent-prompt-refiner` ou a escada
  de correcao da rubric.
- Auditoria sem mudanca: use `agent-code-reviewer`.

## Entradas esperadas
- Objetivo do agente e quem conversa com ele.
- Fontes de fatos (catalogo, KB, API) e efeitos permitidos (handoff, envio, registro).
- Riscos que nao podem depender do modelo (crise, pagamento, privacidade).
- Modelo previsto, custo e latencia aceitaveis.

## Workflow
1. Leia `../../rubrics/agent-design.md` e reuse a infra existente do projeto (canal,
   persistencia, fila, auth). Nao reescreva infra operacional.
2. Preencha `../../templates/agent-design.md`. Secoes sem risco concreto ficam
   "nao se aplica"; nao invente protecao para preencher campo.
3. Liste as tools: leitura devolve fatos; efeito so prepara, o servidor valida e
   executa no commit. O que nao pode acontecer nao vira tool.
4. Escreva o prompt curto (identidade, objetivo, tom, origem dos fatos, limites,
   quando encaminhar, emergencia). Sem frases obrigatorias.
5. Ajuste pelo modelo (tabela "Adaptacao por modelo" da rubric).
6. Coloque protecoes so na entrada e nos efeitos. Nada le ou reescreve a fala.
7. Teste offline o contrato (laco limitado, tool com erro, isolamento, efeitos no
   commit). Depois rode conversas reais com `agent-eval-planner`.
8. Cada falha vira caso de teste e recebe o menor degrau da escada de correcao.

## Saida obrigatoria
- Design minimo preenchido, com a lista do que nao existe de proposito.
- Tools com tipo (leitura/efeito) e contrato.
- Protecoes de entrada e de efeito, cada uma ligada a um risco nomeado.
- Plano de medicao e criterio de decisao por eixo.

## Criterios de aceite
- Uma chamada obrigatoria de modelo por turno (+1 por rodada de tool).
- Nenhuma frase de resposta previsivel lendo o codigo.
- Nenhuma camada sem falha observada que a justifique.
- Infra operacional reaproveitada, nao duplicada.
- Modelo/provider por config; fallback so com decisao do produto.

## Arquivos de apoio
- Rubric: ../../rubrics/agent-design.md
- Template: ../../templates/agent-design.md
- Workflow: ../../workflows/agent-workflow.md
- Tools: ../../skills/agent-tool-designer/SKILL.md
- Medicao: ../../skills/agent-eval-planner/SKILL.md

## Exemplos de uso
- Codex: `$agent-builder Crie um agente de atendimento com busca no catalogo e handoff.`
- Claude Code: `/agent-builder Este agente tem classificador, extrator e redator; reduza ao minimo.`
