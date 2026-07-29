---
name: test-strategy-builder
description: Use para escolher verificacao direcionada em fast, proporcional em standard ou completa/contratual em critical.
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
1. Confirme `mode` e classifique conforme `kernel/test-policy.yaml`.
2. Em `fast`, escolha o menor teste direcionado que prova a mudanca e inclua
   inspeção final do diff.
3. Em `standard`, mapeie riscos provaveis para testes proporcionais e review
   integrado.
4. Em `critical`, aplique RED/characterization, gates de contrato/migration/
   integracao/UI/config e persista a politica no contrato.
5. Declare lacunas e waivers sem inventar cobertura.
6. Aplique o verification budget operacional:
   - `fast`: target ratio `0.20`, no maximo 1 full review pass;
   - `standard`: target ratio `0.30`, no maximo 1 full review pass;
   - `critical`: proporcional ao risco, sem ratio fixo.
7. Ao exceder budget sem risco concreto restante, pare verificacoes
   especulativas, registre notas nao bloqueantes e conclua se o aceite importante
   estiver atendido.

## Saida obrigatoria
- `fast`: comando direcionado e resultado.
- `standard`: matriz curta risco → teste quando necessario.
- `critical`: preencha `../../templates/test-plan.md` para consumo contratual.

## Criterios de aceite
- Testes proporcionais ao risco; mudancas criticas com regressao explicita.
- Nao recomendar e2e pesado quando unit/integration cobre melhor.
- Declarar o que nao sera coberto.
- Mapa risco->cobertura: rubric de testes em Arquivos de apoio.
- Em `critical`, a recomendacao deve ser consumivel por `validate-result`.
- Em `fast`/`standard`, nao gerar plano de testes formal sem valor concreto.

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
