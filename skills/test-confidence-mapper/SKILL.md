---
name: test-confidence-mapper
description: "Use para mapear comandos de verificacao por nivel de confianca: inner loop, PR ready, merge/release e caminhos especiais de backend."
---

# Test Confidence Mapper

## Objetivo
Transformar comandos soltos de teste/build/QA em uma matriz de confianca proporcional ao risco, deixando claro o que basta para iterar, revisar, fazer merge ou release.

## Quando usar
- Ao entrar em repo backend sem saber quais comandos dao confianca real.
- Antes de PR, release, migration, refatoracao ou mudanca em contrato.
- Quando `test-strategy-builder` definiu cobertura, mas faltam comandos por nivel.
- Quando ha muitos scripts e nao esta claro quais bloqueiam merge.

## Quando nao usar
- Para apenas rodar um comando ja conhecido.
- Para inventar cobertura sem ler manifestos, CI ou docs locais.
- Para substituir estrategia de testes por mudanca; use `test-strategy-builder`.

## Entradas esperadas
- Manifestos: `package.json`, `pyproject.toml`, `Makefile`, CI, docs ou scripts equivalentes.
- Mudanca ou area de risco: API, dados, auth, jobs, infra, performance ou docs.
- Comandos conhecidos e tempo/custo aproximado, se houver.

## Workflow
1. Localize comandos em manifestos, README, CI e scripts.
2. Separe comandos por nivel:
   - `inner loop`: rapido durante edicao;
   - `pr ready`: antes de pedir review;
   - `merge/release`: paridade com CI ou gate mais forte;
   - `special paths`: migrations, Docker, auth, pagamentos, filas, integracoes externas.
3. Marque o que bloqueia merge, o que e opcional e o que e desconhecido.
4. Relacione risco da mudanca com nivel minimo recomendado.
5. Liste lacunas: comandos ausentes, testes nao conectados, CI sem paridade ou suite lenta demais.

## Saida obrigatoria
Preencha `../../templates/test-confidence-map.md` com niveis, comandos, cobertura, custo, gatilhos e lacunas.

## Criterios de aceite
- Diferenciar comando observado de comando inferido.
- Nao chamar de merge-ready se nao houver evidencia de CI/paridade.
- Incluir caminho especial para dados, auth, API publica ou dependencia externa quando aplicavel.
- Declarar quando nenhum comando confiavel foi encontrado.

## Arquivos de apoio
- Template: ../../templates/test-confidence-map.md
- Testes por risco: ../../skills/test-strategy-builder/SKILL.md
- Release: ../../skills/release-verifier/SKILL.md
- Cobertura final: ../../skills/goal-coverage-verifier/SKILL.md

## Exemplos de uso
- Codex: `$test-confidence-mapper Mapeie comandos de teste deste backend por nivel de confianca.`
- Claude Code: `/test-confidence-mapper Diga o minimo para PR ready e merge-ready neste repo.`
