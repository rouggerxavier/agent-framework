---
name: agent-guardrails-implementer
description: Use para colocar protecoes em agentes na entrada, nos efeitos e nas permissoes de tool, sem vetar ou reescrever a fala, cada uma ligada a risco nomeado ou falha medida.
---

# Agent Guardrails Implementer

## Objetivo
Proteger o que nao pode depender do modelo (crise, pagamento, privacidade, efeitos
irreversiveis) no lugar certo: entrada, efeitos e permissoes. Nunca controlar a
linguagem. Regra completa em `../../rubrics/agent-design.md`.

## Quando usar
- Agente com tools de efeito, usuarios externos ou dados sensiveis.
- Risco nomeado que o prompt sozinho nao cobre (crise, opt-out, pagamento).
- Falha medida em conversa que a escada de correcao levou ate o degrau 4 ou 5.

## Quando nao usar
- Para "deixar o agente mais seguro" sem risco nomeado nem falha medida.
- Para corrigir tom, estilo ou frase: use `agent-prompt-refiner`.
- Para auditoria de ataque: use `agent-security-auditor`.
- Para tool isolada: use `agent-tool-designer` ou `tool-contract-auditor`.

## Entradas esperadas
- Risco nomeado ou falha medida (conversa, caso, frequencia).
- Tools e efeitos atuais, infra existente do canal.
- Correcoes ja tentadas nos degraus anteriores da escada.

## Workflow
1. Nomeie o risco ou a falha. Sem isso, pare e nao crie protecao.
2. Escolha o lugar, nesta ordem:
   - **efeito ausente**: remova ou nao crie a tool que faria o dano;
   - **servidor no efeito**: valide argumento, enum fechado, idempotencia, commit
     unico, so codigos publicaveis;
   - **entrada**: sinal de alto risco que aciona a equipe ou resposta segura;
   - **permissao**: menor privilegio, confirmacao humana para efeito irreversivel;
   - **verificacao estreita pos-fala**: so detecta um caso e da nova tentativa ao
     modelo com nota interna; nunca troca o texto.
3. Reuse a infra do canal (barreira humana, outbox, retry) antes de criar outra.
4. Escreva o caso que falhava antes e passa depois.
5. Meca contra a referencia (`agent-eval-planner`). Sem ganho, remova.

## Saida obrigatoria
Preencha `../../templates/agent-guardrails-plan.md`: risco, lugar, implementacao,
teste e motivo de nao usar degrau mais leve.

## Criterios de aceite
- Toda protecao aponta um risco nomeado ou uma falha medida.
- Nenhuma protecao veta, reescreve ou substitui a fala do modelo.
- Nenhuma regex ou lista de termos sobre a saida sem caso de teste real que a exija.
- Efeitos irreversiveis exigem tool explicita, validacao no servidor ou humano.
- Logs sem secrets nem dados pessoais desnecessarios.

## Arquivos de apoio
- Rubric: ../../rubrics/agent-design.md
- Template: ../../templates/agent-guardrails-plan.md
- Tools: ../../skills/agent-tool-designer/SKILL.md
- Seguranca: ../../skills/agent-security-auditor/SKILL.md

## Exemplos de uso
- Codex: `$agent-guardrails-implementer O agente aceita pedido de reserva; impeca isso.`
- Claude Code: `/agent-guardrails-implementer Crise apos takeover fica sem resposta; proteja.`
