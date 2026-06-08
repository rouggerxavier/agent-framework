---
name: model-flexibility-auditor
description: Use para auditar se agente ou backend agentico suporta modelo/provider configuravel, fallback, capability routing, limites de custo e troca segura.
---

# Model Flexibility Auditor

## Objetivo
Verificar se um agente pode trocar modelo, provider ou tier de forma controlada, sem quebrar contrato, custo, latencia, privacidade ou runtime.

## Quando usar
- Ao criar agente que pode rodar em mais de um modelo/provider.
- Antes de migrar modelo, adicionar fallback ou mudar tier de custo.
- Quando o agente tem tools, contexto grande, dados sensiveis, SLA ou comportamento critico.
- Em revisoes de model routing, config de provider, evals ou prompt contract.

## Quando nao usar
- Para escolher modelo por gosto ou benchmark solto.
- Para auditoria geral de hardcode; use `agent-anti-hardcode-auditor`.
- Para tarefas simples onde um modelo fixo e explicitamente requisito do produto.

## Entradas esperadas
- Modelo/provider atual e alternativas permitidas.
- Contrato do agente: inputs, outputs, tools, stop conditions e guardrails.
- Restricoes de custo, latencia, contexto, privacidade e qualidade.
- Evals, testes ou casos representativos, se existirem.

## Workflow
1. Identifique capacidades exigidas: tool use, reasoning, structured output, vision, long context, latency, privacy e cost ceiling.
2. Verifique se selecao de modelo/provider vem de policy/config, nao de chamada espalhada.
3. Audite fallback: criterio de troca, retry, timeout, degradacao, logs e comportamento quando provider falha.
4. Audite contratos: schema de saida, mensagens de erro, guardrails, contexto minimo e variance permitida.
5. Classifique maturidade:
   - `locked`: acoplado a um modelo/provider sem justificativa;
   - `configurable`: modelo vem de config, mas fallback/evals sao fracos;
   - `routable`: possui policy por capacidade e fallback verificavel;
   - `portable`: troca segura comprovada por evals/runtime QA.
6. Recomende mudanca minima, evals e criterio de rollout.

## Saida obrigatoria
Preencha `../../templates/model-flexibility-report.md` com maturidade, riscos, gaps, policy sugerida e verificacao.

## Criterios de aceite
- Diferenciar configurabilidade real de apenas trocar string de modelo.
- Incluir custo, latencia, contexto, privacidade e qualidade na decisao.
- Definir fallback com condicao objetiva, nao fallback sempre-on sem controle.
- Pedir eval/runtime QA quando a troca afeta comportamento do usuario.

## Arquivos de apoio
- Template: ../../templates/model-flexibility-report.md
- Routing: ../../skills/model-routing/SKILL.md
- QA: ../../skills/runtime-qa-audit/SKILL.md
- Testes: ../../skills/test-confidence-mapper/SKILL.md

## Exemplos de uso
- Codex: `$model-flexibility-auditor Audite este agente para suportar fallback de modelo.`
- Claude Code: `/model-flexibility-auditor Verifique se esta migracao de provider esta segura.`
