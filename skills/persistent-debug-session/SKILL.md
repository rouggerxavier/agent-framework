---
name: persistent-debug-session
description: Use para conduzir investigacao de bug longa com estado persistente, hipoteses, experimentos, evidencias, decisoes e retomada segura.
---

# Persistent Debug Session

## Objetivo
Manter uma investigacao de bug organizada entre contexto longo, tentativas, pausas e retomadas, sem perder hipoteses, evidencias ou comandos ja executados.

## Quando usar
- Bug intermitente, multi-camada, dificil de reproduzir ou que passa de uma sessao.
- Incidente backend envolvendo API, jobs, banco, cache, concorrencia, fila ou integracao.
- Quando `bug-repro-lab` nao basta por haver muitas hipoteses ou experimentos.
- Antes de trocar de agente mantendo a investigacao em aberto.

## Quando nao usar
- Para bug simples com reproducao clara e fix local.
- Para feature nova sem comportamento esperado.
- Para postmortem final; use handoff ou documento de incidente separado.

## Entradas esperadas
- Sintoma, impacto, ambiente e janela de ocorrencia.
- Logs, stack traces, testes falhando, traces ou comandos.
- Arquivo de sessao existente, se houver.
- Restricoes de seguranca: nao salvar secrets, dados pessoais sensiveis ou tokens.

## Workflow
1. Quando o kernel estiver ativo, registre blocker com evidencia, `blocked_from`
   e condicoes de desbloqueio antes de entrar em `blocked`.
2. Crie ou atualize sessao no artefato indicado ou em `docs/debug-sessions/`.
3. Registre esperado, obtido, impacto, ambiente e status atual.
4. Liste hipoteses com evidencia a favor/contra e proximo experimento.
5. Execute experimentos pequenos e registre comando, resultado e decisao no ledger.
6. Quando a causa surgir, proponha fix minimo e teste de regressao.
7. Resolva/escalone o blocker; revalide e retome somente `blocked_from`.
8. Se pausar, escreva retomada com ultimo estado, o que nao repetir e proximo passo.

## Saida obrigatoria
- Arquivo de sessao atualizado ou conteudo pronto para ele.
- Hipotese principal e alternativas descartadas.
- Evidencia e comandos executados.
- Proximo experimento ou fix minimo.
- Prompt curto de retomada se a investigacao continuar.
- Blocker resolvido/escalado e estado de retorno, quando usar o kernel.

## Criterios de aceite
- Nao repetir experimento ja registrado sem motivo novo.
- Distinguir fato, hipotese e inferencia.
- Nao salvar secrets ou dados sensiveis no arquivo de sessao.
- Cada proximo passo deve reduzir incerteza ou validar regressao.
- Experimento falho permanece no ledger; blocker nao e apagado sem evidencia.

## Arquivos de apoio
- Template: ../../templates/debug-session.md
- Bugfix: ../../skills/bug-repro-lab/SKILL.md
- Testes: ../../skills/test-strategy-builder/SKILL.md
- Handoff: ../../skills/handoff-builder/SKILL.md

## Exemplos de uso
- Codex: `$persistent-debug-session Abra uma sessao persistente para este bug intermitente.`
- Claude Code: `/persistent-debug-session Atualize a sessao de debug com estes logs e proximos experimentos.`
