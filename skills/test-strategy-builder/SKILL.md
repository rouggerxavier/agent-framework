---
name: test-strategy-builder
description: Use em toda alteracao de software para decidir quando criar, ampliar ou reaproveitar testes, escrever cobertura util e verificar comportamento conforme o risco.
---

# Test Strategy Builder

## Objetivo
Decidir e executar a cobertura que aumenta a confianca na mudanca, sem criar testes redundantes ou deixar riscos relevantes descobertos.

## Quando usar
- Em toda tarefa que altere software, inclusive `fast`, frontend, backend,
  refatoracao, configuracao ou documentacao do software.
- Antes de implementar e na revisao dos testes criados ou afetados.
- Ao revisar PR sem clareza de cobertura.
- Antes de release ou bugfix critico.

## Quando nao usar
- Para auditar toda a suite sem relacao com a tarefa.
- Para tarefas sem alteracao de software ou de sua documentacao/configuracao.
- Para substituir QA runtime quando precisa validar app real.

## Entradas esperadas
- Descricao da mudanca ou diff.
- Comportamento esperado, testes existentes e comandos do repositorio.
- Risco, prazo e ambientes disponiveis.

## Workflow
1. Confirme `mode`, comportamento alterado e falhas plausiveis. Inspecione
   cobertura, fixtures e comandos existentes apenas no escopo afetado.
2. Aplique `../../rubrics/testing.md` para decidir: reaproveitar testes
   suficientes, ampliar um caso existente, criar cobertura faltante ou justificar
   nenhum teste novo. Avaliar e obrigatorio; criar testes nao e automatico.
3. Para cada teste novo ou ampliado, identifique comportamento protegido,
   defeito que detectaria e lacuna existente. Escolha o menor nivel capaz de
   observar a falha real; nao use quantidade ou percentual como prova de valor.
4. Escreva os testes necessarios com fixtures e infraestrutura do repo. Para
   bugs, busque falha pelo defeito antes da correcao e sucesso depois; se um
   teste existente ja reproduz o bug, reaproveite-o. Ambiente indisponivel ou
   reproducao impossivel viram lacunas explicitas, nao evidencia inventada.
5. Execute a verificacao direcionada/proporcional e revise as assercoes dos
   testes criados ou afetados. Corrija testes que aceitariam o comportamento
   errado; nao amplie para uma auditoria de legado sem risco concreto.
6. Em `critical`, preserve RED/characterization, gates de contrato/migration/
   integracao/UI/config e politica no contrato conforme `kernel/test-policy.yaml`.
   A decisao de nao criar testes novos nao dispensa verificacao nem substitui
   waiver exigido.
7. Aplique o verification budget operacional:
   - `fast`: target ratio `0.20`, no maximo 1 full review pass;
   - `standard`: target ratio `0.30`, no maximo 1 full review pass;
   - `critical`: proporcional ao risco, sem ratio fixo.
8. Ao exceder budget sem risco concreto restante, pare verificacoes
   especulativas, registre notas nao bloqueantes e conclua se o aceite importante
   estiver atendido.

## Saida obrigatoria
- Sempre: decisao sobre testes novos, motivo, comandos/resultados e lacunas.
- `fast`: retorno curto; inclua a verificacao alternativa quando nenhum teste
  automatizado se aplicar.
- `standard`: matriz curta comportamento/falha → cobertura quando necessario.
- `critical`: preencha `../../templates/test-plan.md` para consumo contratual.

## Criterios de aceite
- Testes proporcionais ao risco; mudancas criticas com regressao explicita.
- Cada teste novo protege comportamento relevante e cobre uma lacuna identificada.
- Cobertura existente suficiente e reutilizada; nao criar teste novo exige motivo.
- Assercoes verificam resultados observaveis; mocks nao escondem a falha relevante.
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
