---
name: feature-logging-planner
description: Use para avaliar, planejar, implementar ou revisar logs proporcionais de features, cobrindo fluxos criticos sem overlogging nem vazamento.
---

# Feature Logging Planner

## Objetivo
Definir logs uteis e proporcionais para features que podem gerar bugs complexos, garantindo cobertura ponta a ponta sem logar cada linha de codigo.

## Quando usar
- Ao implementar feature com fluxo multi-etapa, estado, permissao, dados, jobs, filas, integracoes externas, agentes, tools ou fallback.
- Quando um bug seria dificil de reproduzir sem eventos, correlation id, payload resumido ou erro estruturado.
- Antes de release de mudanca que altera comportamento runtime, contrato, auth, dados, model/tool calls ou side effects.
- Ao revisar feature com logs demais, logs de menos, logs sem contexto ou logs com risco de segredo/dado sensivel.

## Quando nao usar
- Para copy, docs, UI trivial, config sem runtime ou mudanca sem risco de investigacao complexa.
- Para observabilidade ampla de agente; use `agent-observability-auditor`.
- Para criar logs por ansiedade; se nao houver pergunta de debug clara, recomende nao logar.

## Entradas esperadas
- Feature, fluxo ou diff a ser implementado/revisado.
- Pontos de entrada/saida, estado, side effects, erros esperados e integracoes.
- Dados sensiveis, politica de redaction e ambiente.
- Logs existentes, tracing/correlation id e incidentes/bugs conhecidos, se houver.

## Workflow
1. Classifique necessidade: `no logging`, `minimal`, `standard` ou `high signal`, com justificativa.
2. Liste perguntas de debug que os logs precisam responder; descarte logs sem pergunta clara.
3. Escolha pontos de log: entrada do fluxo, decisao critica, chamada externa, mutacao de estado, erro, retry/fallback e conclusao.
4. Defina nivel e campos: `debug`, `info`, `warn`, `error`, correlation id, ids seguros, status, duracao e resumo de payload.
5. Aplique seguranca: redaction, sem secrets/tokens/PII desnecessaria, limite de cardinalidade, sampling e volume esperado.
6. Se estiver implementando, adicione logs nos pontos aprovados e evite logs duplicados, ruidosos ou linha-a-linha.
7. Verifique com runtime/teste: logs aparecem no caminho feliz, falha relevante e caso de retry/fallback quando aplicavel.

## Saida obrigatoria
Preencha `../../templates/feature-logging-plan.md` com decisao, eventos, campos, riscos, patches recomendados e verificacao.

## Criterios de aceite
- Cada log proposto responde uma pergunta real de debug, operacao ou auditoria.
- Logs cobrem o fluxo ponta a ponta quando o risco justifica, sem overlogging.
- Campos sensiveis sao redigidos ou omitidos.
- Nivel, cardinalidade, volume e correlation id sao considerados.
- Verificacao confirma pelo menos um caminho feliz e uma falha relevante quando houver runtime.

## Arquivos de apoio
- Template: ../../templates/feature-logging-plan.md
- Observabilidade de agente: ../../skills/agent-observability-auditor/SKILL.md
- Runtime QA: ../../skills/runtime-qa-audit/SKILL.md
- Seguranca: ../../skills/security-privacy-audit/SKILL.md

## Exemplos de uso
- Codex: `$feature-logging-planner Avalie onde esta feature precisa de logs antes de implementar.`
- Claude Code: `/feature-logging-planner Revise logs desta mudanca para cobrir bugs complexos sem ruido.`
