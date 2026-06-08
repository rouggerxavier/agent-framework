---
name: agent-anti-hardcode-auditor
description: Use para auditar agentes e codigo agentico contra hardcode de modelos, providers, prompts, tools, paths, env vars, magic constants e flags.
---

# Agent Anti Hardcode Auditor

## Objetivo
Encontrar acoplamentos rigidos que deixam agentes dificeis de evoluir, testar, portar ou operar em ambientes diferentes.

## Quando usar
- Ao revisar agente novo ou refatoracao de agente.
- Quando o codigo fixa modelo, provider, prompt, tool, path, URL, env var ou limite operacional.
- Antes de trocar modelo/provider, mover runtime ou transformar prompt em produto recorrente.
- Em diffs que tocam prompt, tools, config, memoria, runtime, evals ou guardrails.

## Quando nao usar
- Para decidir qual modelo usar; use `model-routing` ou `model-flexibility-auditor`.
- Para seguranca ampla sem foco em hardcode; use `security-privacy-audit`.
- Para constants intencionais com justificativa de dominio e baixo custo de mudanca.

## Entradas esperadas
- Arquivos ou diff do agente.
- Configs, env vars, prompt/system instructions e registro de tools.
- Politica de modelo/provider desejada, se existir.
- Ambientes de execucao: local, CI, staging, prod ou multi-tenant.

## Workflow
1. Mapeie superficies: prompt, model selection, tools, configs, paths, URLs, limites, estado e logs.
2. Procure hardcode de model IDs, provider IDs, tool names, prompt snippets, env names, absolute paths, URLs, magic constants e feature flags.
3. Classifique cada achado:
   - `acceptable`: constante de dominio, documentada e sem impacto operacional;
   - `extract config`: precisa virar config, env, policy, registry ou parametro;
   - `wrap adapter`: precisa de interface para provider/tool/runtime;
   - `remove`: duplicado, morto ou trava comportamento sem motivo.
4. Priorize por impacto: troca de modelo/provider, seguranca, teste, portabilidade, custo e manutencao.
5. Recomende patch minimo e verificacao para evitar regressao.

## Saida obrigatoria
Preencha `../../templates/agent-hardcode-report.md` com achados, evidencia, decisao e correcao recomendada.

## Criterios de aceite
- Cada achado aponta arquivo, trecho ou comportamento verificavel.
- Nao exigir configurabilidade quando a constante e claramente de dominio.
- Separar hardcode de modelo, prompt, tool, path, env e limite operacional.
- Recomendar a menor abstracao suficiente: config, adapter, registry ou documentacao.

## Arquivos de apoio
- Template: ../../templates/agent-hardcode-report.md
- Agente: ../../skills/agent-builder/SKILL.md
- Modelo: ../../skills/model-flexibility-auditor/SKILL.md
- Config: ../../skills/config-surface-auditor/SKILL.md

## Exemplos de uso
- Codex: `$agent-anti-hardcode-auditor Audite este agente antes de trocar de modelo.`
- Claude Code: `/agent-anti-hardcode-auditor Revise prompt, tools e configs deste diff.`
