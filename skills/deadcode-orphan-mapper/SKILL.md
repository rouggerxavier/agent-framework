---
name: deadcode-orphan-mapper
description: "Use para mapear codigo morto ou orfao: exports nao usados, rotas mortas, jobs sem trigger, configs antigas, prompts e tools desconectados."
---

# Deadcode Orphan Mapper

## Objetivo
Encontrar codigo, configs, prompts, rotas, jobs e tools que parecem desconectados, separando evidencias fortes de suspeitas antes de recomendar remocao.

## Quando usar
- Antes de refatoracao, limpeza de repo, reducao de contexto ou otimizacao.
- Quando ha prompts, tools, jobs, rotas, configs, exports ou modulos antigos sem dono claro.
- Ao auditar agentes com tools registradas mas nao chamadas, prompts sem runtime ou configs obsoletas.
- Quando map loader geral nao basta e o foco e codigo morto/orfao.

## Quando nao usar
- Para apagar codigo automaticamente.
- Para repo pequeno com escopo ja claro.
- Para performance sem suspeita de codigo morto; use `performance-budget-auditor`.

## Entradas esperadas
- Repo, area ou diff a auditar.
- Linguagem/framework e comandos de busca/teste conhecidos.
- Entry points, rotas, jobs, tool registries, prompts, configs e docs relevantes.
- Restricoes: codigo gerado, dynamic imports, reflection, feature flags e plugins.

## Workflow
1. Mapeie entrypoints: app, API, CLI, jobs, tests, tool registries, prompts, configs e docs.
2. Procure candidatos: exports nao usados, rotas sem caller, jobs sem trigger, configs antigas, prompts sem chamada e tools nao registradas/usadas.
3. Classifique evidencia:
   - `strong`: sem referencia estatica e sem entrada runtime conhecida;
   - `medium`: referencia indireta possivel, mas sem evidencia;
   - `weak`: dinamico, feature flag, plugin ou uso externo possivel.
4. Para cada candidato, indique risco de remocao e verificacao minima.
5. Recomende acao: remover, arquivar, documentar dono, adicionar teste, investigar ou manter.
6. Nunca trate ausencia de `rg` como prova quando ha dynamic import, reflection, registry ou integracao externa.

## Saida obrigatoria
Preencha `../../templates/deadcode-orphan-map.md` com candidatos, evidencia, risco, acao recomendada e verificacao.

## Criterios de aceite
- Separar fato observado, inferencia e suspeita.
- Candidato de remocao precisa de evidencia forte ou verificacao clara.
- Considerar uso dinamico, gerado, plugin, CI, cron, webhook e chamadas externas.
- Cada recomendacao deve ter proximo passo verificavel.

## Arquivos de apoio
- Template: ../../templates/deadcode-orphan-map.md
- Repo map: ../../skills/repo-map-builder/SKILL.md
- Review: ../../skills/diff-reviewer/SKILL.md
- Testes: ../../skills/test-confidence-mapper/SKILL.md

## Exemplos de uso
- Codex: `$deadcode-orphan-mapper Procure tools e prompts orfaos neste repo.`
- Claude Code: `/deadcode-orphan-mapper Mapeie codigo morto antes desta limpeza.`
