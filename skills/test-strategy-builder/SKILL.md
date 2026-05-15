---
name: test-strategy-builder
description: Use para escolher estrategia de testes por mudanca, cobrindo unit, integration, e2e, manual QA e comandos proporcionais ao risco.
---

# Test Strategy Builder

## Objetivo
Definir cobertura de testes suficiente para uma mudanca sem exagerar custo nem deixar riscos importantes descobertos.

## Quando usar
- Antes ou depois de implementar mudancas com risco funcional.
- Ao revisar PR sem clareza de cobertura.
- Antes de release ou bugfix critico.

## Quando nao usar
- Para apenas executar comandos ja definidos.
- Para mudanca puramente textual sem impacto funcional.
- Para substituir QA runtime quando precisa validar app real.

## Entradas esperadas
- Descricao da mudanca ou diff.
- Stack e comandos conhecidos.
- Risco, prazo e ambientes disponiveis.

## Workflow
1. Classifique a mudanca: UI, API, dados, auth, infra, refactor ou bugfix.
2. Identifique contratos, regressao e caminhos criticos.
3. Escolha testes por prioridade e profundidade.
4. Defina comandos e cenarios manuais.
5. Declare lacunas e aceite de risco.

## Saida obrigatoria
- Matriz risco -> teste.
- Testes recomendados por prioridade.
- Comandos de verificacao.
- Cenarios manuais, se necessarios.
- Lacunas e criterio de aceite.

## Criterios de aceite
- Testes proporcionais ao risco; mudancas criticas com regressao explicita.
- Nao recomendar e2e pesado quando unit/integration cobre melhor.
- Declarar o que nao sera coberto.
- Mapa risco->cobertura: rubric de testes em Arquivos de apoio.

## Arquivos de apoio
Nao copie a matriz de risco na skill; aplique a rubric.
- Rubric: ../../rubrics/testing.md
- Workflow: ../../workflows/bugfix.md
- Workflow: ../../workflows/feature-build.md

## Exemplos de uso
- Codex: `$test-strategy-builder Defina testes para esta mudanca de billing.`
- Claude Code: `/test-strategy-builder Que cobertura falta neste PR?`
