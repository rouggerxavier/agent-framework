---
name: model-routing
description: Use para escolher entre Codex, Claude Code, ChatGPT, modelos OpenAI ou outros agentes com base em tarefa, custo, latencia, risco e contexto.
---

# Model Routing

## Objetivo
Roteirizar trabalho para modelo, agente ou ferramenta adequada, com fallback, effort e formato de prompt.

## Quando usar
- Quando uma tarefa pode ir para varios modelos ou agentes.
- Ao montar workflow multiagente.
- Quando custo, latencia, contexto ou verificacao importam.

## Quando nao usar
- Para escolher por preferencia de marca sem criterio.
- Para tarefa simples com ferramenta obvia.
- Para substituir avaliacao de risco tecnico.

## Entradas esperadas
- Tarefa ou conjunto de tarefas.
- Modelos, agentes e ferramentas disponiveis.
- Restricoes de custo, latencia, privacidade, contexto e qualidade.

## Workflow
1. Classifique tarefas: codigo, pesquisa, escrita, visual, planejamento, QA ou decisao.
2. Avalie contexto, risco, ferramentas e verificacao.
3. Escolha agente/modelo primario e fallback.
4. Recomende effort e formato de prompt.
5. Indique quando escalar para humano ou dividir em fases.

## Saida obrigatoria
- Recomendacao principal.
- Tabela de roteamento por tarefa.
- Justificativa curta.
- Fallback e criterio de troca.
- Prompt shape recomendado.

## Criterios de aceite
- Considere custo, velocidade, privacidade e verificabilidade.
- Tarefas de codigo devem ir para agente com acesso ao repo quando necessario.
- Inclua validacao para alto impacto.
- Evite recomendacao vaga.

## Exemplos de uso
- Codex: `$model-routing Escolha modelos para auditar UI, corrigir codigo e escrever release notes.`
- Claude Code: `/model-routing Monte matriz Codex vs Claude vs ChatGPT para este fluxo.`
