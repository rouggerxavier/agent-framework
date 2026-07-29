---
name: plan-quality-checker
description: Use para checar plano curto quando houver risco concreto em standard ou aplicar o plan gate formal em critical; nunca e obrigatorio em fast.
---

# Plan Quality Checker

## Objetivo
Verificar se um plano esta pronto para execucao por agente ou humano sem depender de adivinhacao, retrabalho ou criterios subjetivos.

## Quando usar
- Em `standard`, quando o plano curto tem dependencias ou incerteza relevante.
- Em `critical`, antes de executar plano, migration, API sensivel ou feature de
  alto risco.
- Depois de `backend-slice-planner`, `implementation-planner` ou plano escrito por outro agente.
- Quando o plano parece plausivel, mas pode estar vago ou incompleto.
- Antes de delegar execucao para outro agente.

## Quando nao usar
- Para revisar codigo ja implementado; use `diff-reviewer`.
- Para criar o plano do zero; use `backend-slice-planner` ou `implementation-planner`.
- Para tarefa trivial classificada como `fast`.
- Para exigir contrato integral ou gate persistente em `standard`.

## Entradas esperadas
- Plano, PRD, issue ou lista de tarefas.
- Objetivo e restricoes conhecidas.
- Mapa do repo ou arquivos citados no plano.
- Rubrics relevantes: API, dados, testes, seguranca ou performance.

## Workflow
1. Confirme `mode`, objetivo, escopo e criterio de done.
2. Cheque atomicidade: cada tarefa deve ter uma responsabilidade clara.
3. Cheque `read_first`: arquivos a editar, contratos e testes relevantes devem ser lidos antes.
4. Cheque acoes: rejeite verbos vagos como "alinhar", "melhorar" ou "ajustar" sem mudanca concreta.
5. Cheque aceite: cada criterio deve ser verificavel por teste, comportamento, comando ou evidencia.
6. Cheque dependencias e ordem: migrations, contratos e callers devem entrar em sequencia segura.
7. Cheque gates backend: API, dados, auth, security, dependencies, rollback e docs quando aplicavel.
8. Em `standard`, limite-se a clareza, passos, dependencias, aceite e verificacao;
   emita correcoes minimas sem template/ledger obrigatorio.
9. Em `critical`, valide contrato integral, grafo sem ciclos/conflitos, risco,
   politica de testes, evidencia esperada e isolamento.
10. Somente em `critical`, `approved` autoriza
   `specified → planned`.

## Saida obrigatoria
- `standard`: veredito curto no proprio plano/retorno.
- `critical`: preencha `../../templates/plan-quality-report.md` e registre em
  `EVIDENCE.md`/`STATE.md.gates.plan_quality`.

## Criterios de aceite
- Achados aparecem antes do resumo.
- Cada blocker/high tem evidencia no plano ou lacuna concreta.
- Nao exigir burocracia para tarefa de baixo risco.
- O resultado diz exatamente o que editar no plano.
- Em `standard`, nao exigir artefatos formais por default.
- Em `critical`, contrato ausente, dependencia invalida, aceite sem evidencia ou
  risco nao classificado bloqueia `planned`.

## Arquivos de apoio
- Template: ../../templates/plan-quality-report.md
- Padrao backend: ../../templates/backend-slice-plan.md
- Rubric de testes: ../../rubrics/testing.md
- API: ../../rubrics/api-contract.md
- Dados: ../../rubrics/data-migration.md

## Exemplos de uso
- Codex: `$plan-quality-checker Audite este plano backend antes de executar.`
- Claude Code: `/plan-quality-checker Encontre tarefas vagas e gates ausentes neste plano.`
