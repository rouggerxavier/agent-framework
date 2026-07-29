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
1. Classifique conforme `kernel/test-policy.yaml`: business logic, bugfix,
   legacy, API, migration, integracao, UI, docs ou config.
2. Identifique contratos, regressao e caminhos criticos.
3. Aplique o default executavel ou registre override aprovado.
4. Defina comandos, estagios RED/GREEN/caracterizacao e cenarios runtime.
5. Declare lacunas; waiver exige justificativa e evidencia alternativa.
6. Persista a politica no contrato para validacao pelo `task-runner`.

## Saida obrigatoria
Preencha `../../templates/test-plan.md` (matriz risco->teste, comandos,
cenarios manuais, lacunas e aceite).

## Criterios de aceite
- Testes proporcionais ao risco; mudancas criticas com regressao explicita.
- Nao recomendar e2e pesado quando unit/integration cobre melhor.
- Declarar o que nao sera coberto.
- Mapa risco->cobertura: rubric de testes em Arquivos de apoio.
- A recomendacao deve ser consumivel por `validate-result`, nao apenas prosa.

## Arquivos de apoio
Nao copie a matriz de risco na skill; aplique a rubric e o template.
- Rubric: ../../rubrics/testing.md
- Template: ../../templates/test-plan.md
- Workflow: ../../workflows/bugfix.md
- Workflow: ../../workflows/feature-build.md
- Politica: ../../kernel/test-policy.yaml
- Executor: ../../skills/task-runner/SKILL.md

## Exemplos de uso
- Codex: `$test-strategy-builder Defina testes para esta mudanca de billing.`
- Claude Code: `/test-strategy-builder Que cobertura falta neste PR?`
