---
name: agent-eval-planner
description: Use para planejar e decidir evals de agentes - cenarios de conversa selados, regressao pareada com a referencia, juiz cego, teto de custo e decisao por eixo.
---

# Agent Eval Planner

## Objetivo
Medir se uma mudanca de agente melhora a conversa sem piorar fatos, seguranca,
confiabilidade ou custo, com comparacao justa contra a referencia. Metodo em
`../../rubrics/agent-design.md` (secao Medicao).

## Quando usar
- Antes de promover qualquer mudanca de prompt, tool, modelo ou protecao.
- Ao criar agente: para comparar com o agente antigo ou com o baseline.
- Quando uma conversa real mostrou falha que deve virar caso.

## Quando nao usar
- Teste unitario de tool: use `tool-runtime-validator`.
- Ciclo continuo com dados de producao: use `agent-eval-flywheel`.
- Contrato offline (laco, erro, commit): teste comum, sem juiz.

## Entradas esperadas
- Candidata e referencia (commits), modelo e harness.
- Falha que motivou a mudanca e cenarios afetados.
- Orcamento maximo.

## Workflow
1. Defina cenarios: os afetados pela mudanca mais uma amostra de controle. Para
   agente novo, cenarios escritos por quem nao leu o codigo.
2. Sele os cenarios (hash) antes da primeira execucao.
3. Rode candidata e referencia na mesma rodada, mesmo modelo, dados e harness;
   repeticoes suficientes para variancia (>= 3 por cenario).
4. Juiz cego a versao, com rubrica por eixo: conversa, fatos, seguranca,
   confiabilidade, custo/latencia. Checagem deterministica onde der.
5. Declare antes: teto de custo e regra de decisao por eixo (ex.: qualquer falha
   grave de seguranca rejeita).
6. Leia as transcricoes das falhas graves; descarte falsos positivos com motivo.
7. Decida: `BETTER`, `WORSE` ou `INCONCLUSIVE`. So `BETTER` sem piora em eixo
   critico vai para o dono promover.

## Saida obrigatoria
Preencha `../../templates/agent-eval-plan.md` com cenarios, selo, referencia,
regra de decisao, custo e resultado por eixo.

## Criterios de aceite
- Comparacao na mesma rodada; numero de outra data so como contexto.
- Decisao por eixo, nunca por media.
- Custo real registrado contra o teto.
- Variacao do simulador de cliente ou do juiz apontada quando existir.
- Nada de afirmar comportamento do modelo antes da regressao.

## Arquivos de apoio
- Rubric: ../../rubrics/agent-design.md
- Template: ../../templates/agent-eval-plan.md
- Producao: ../../skills/agent-eval-flywheel/SKILL.md
- Runtime: ../../skills/agent-runtime-qa/SKILL.md

## Exemplos de uso
- Codex: `$agent-eval-planner Monte a regressao pareada da candidata contra a referencia.`
- Claude Code: `/agent-eval-planner Planeje os cenarios para medir o novo encaminhamento.`
