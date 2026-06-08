---
name: skill-quality-auditor
description: Use para auditar skills do agent-framework, revisando gatilho, escopo, duplicacao, estrutura, referencias, saida, criterios e verificacao.
---

# Skill Quality Auditor

## Objetivo
Avaliar se uma skill esta clara, acionavel, enxuta e bem integrada ao `agent-framework`, apontando problemas que afetariam disparo, execucao ou manutencao.

## Quando usar
- Ao criar, revisar ou refatorar uma skill.
- Antes de commit ou sincronizacao do framework.
- Quando uma skill parece generica, duplicada, longa ou dificil de aplicar.
- Ao comparar uma nova proposta com skills, rubrics, workflows e templates existentes.

## Quando nao usar
- Para revisar codigo de produto; use `diff-reviewer`.
- Para decidir se uma tarefa recorrente deve virar skill; use `skill-evolution-loop`.
- Para planejar uma feature comum; use `implementation-planner`.

## Entradas esperadas
- Caminho da skill alvo, normalmente `skills/<nome>/SKILL.md`.
- Padrao em `docs/skill-standards.md`.
- Lista de skills existentes em `skills/*/SKILL.md`.
- Rubrics, workflows ou templates referenciados pela skill, se houver.

## Workflow
1. Leia a skill alvo e confirme frontmatter, nome, description e secoes principais.
2. Compare nome e description com `docs/skill-standards.md`; verifique se o gatilho e especifico e curto.
3. Procure duplicacao ou sobreposicao lendo os frontmatters das skills existentes.
4. Verifique se a skill escolhe o asset certo: skill para procedimento, rubric para criterio, workflow para sequencia, template para formato.
5. Audite o corpo:
   - objetivo e claro;
   - quando usar e quando nao usar reduzem ambiguidade;
   - workflow tem passos executaveis;
   - saida obrigatoria e criterios de aceite sao verificaveis;
   - arquivos de apoio existem e nao carregam contexto desnecessario.
6. Rode `bash installers/verify-framework.sh` quando estiver no repo e houver mudancas locais relevantes.
7. Produza achados priorizados e recomende manter, ajustar, mesclar, dividir ou remover.

## Saida obrigatoria
- Veredito: `aprovada`, `aprovada com ajustes`, `bloqueada` ou `mesclar/remover`.
- Achados por severidade: `blocker`, `high`, `medium`, `low`.
- Evidencia com caminhos e trechos ou linhas relevantes.
- Recomendacao objetiva para cada achado.
- Verificacao executada ou motivo para nao executar.

## Criterios de aceite
- A auditoria separa fatos observados de opiniao arquitetural.
- Duplicacao e apontada com skill candidata a mescla, nao so como comentario generico.
- Nenhuma sugestao aumenta contexto sem ganho claro.
- O resultado permite editar a skill sem redescobrir o problema.

## Arquivos de apoio
- Padrao de skills: ../../docs/skill-standards.md
- Router: ../../skills/agent-framework-router/SKILL.md
- Verificacao: ../../installers/verify-framework.sh
- Memoria de recorrencia: ../../docs/task-memory.md

## Exemplos de uso
- Codex: `$skill-quality-auditor Audite skills/minha-skill/SKILL.md antes do commit.`
- Claude Code: `/skill-quality-auditor Revise esta skill nova e diga se duplica alguma existente.`
