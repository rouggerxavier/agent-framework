---
name: skill-evolution-loop
description: Use para registrar tarefas recorrentes, manter memoria curta do agent-framework, decidir quando criar ou atualizar skills e preservar padroes do repo.
---

# Skill Evolution Loop

## Objetivo
Transformar repeticao real em aprendizado reutilizavel: registrar tarefas recorrentes, manter um log pequeno e criar ou atualizar skills quando houver evidencia suficiente.

## Quando usar
- Ao melhorar, auditar ou reorganizar o `agent-framework`.
- Quando o usuario mencionar uma tarefa recorrente, padrao de trabalho ou "isso sempre aparece".
- Ao final de uma tarefa que revelou um procedimento reutilizavel.
- Antes de criar uma skill nova por impulso, para confirmar recorrencia e encaixe.

## Quando nao usar
- Para uma tarefa unica, experimental ou muito especifica.
- Quando a recorrencia nao pode ser registrada sem salvar dado sensivel.
- Quando a solucao correta e atualizar uma rubric, workflow ou template existente.

## Entradas esperadas
- Pedido atual e resultado produzido.
- `docs/task-memory.md`, se existir.
- Padrao de skills em `docs/skill-standards.md`.
- Limite de memoria: use `AGENT_MEMORY_CHAR_LIMIT` se definido; caso contrario, use 6000 caracteres.

## Workflow
1. Leia `docs/task-memory.md`; se nao existir, crie a partir de `templates/task-memory.md`.
2. Classifique a tarefa em uma chave curta: verbo + objeto, por exemplo `review-api-contract` ou `build-release-checklist`.
3. Atualize ou adicione entrada com contagem, data, evidencia curta e decisao atual.
4. Mantenha o arquivo abaixo do limite: compacte exemplos antigos, remova detalhe redundante e preserve entradas com maior contagem ou risco.
5. Se a mesma chave atingir 3 ocorrencias distintas, decida a promocao:
   - criar skill quando houver workflow repetivel;
   - atualizar skill existente quando o padrao ja tiver dono;
   - criar ou atualizar rubric/template quando o valor for checklist ou formato de saida.
6. Ao criar skill, siga `docs/skill-standards.md` e rode `bash installers/verify-framework.sh`.
7. Registre no log a decisao tomada e o asset criado ou atualizado.

## Saida obrigatoria
- Entrada de memoria atualizada ou motivo para nao atualizar.
- Decisao: `observar`, `atualizar asset existente`, `criar skill`, `criar rubric/template` ou `ignorar`.
- Se houve promocao, arquivos alterados e verificacao executada.

## Criterios de aceite
- Nenhum segredo, dado pessoal sensivel ou contexto privado desnecessario foi salvo.
- `docs/task-memory.md` ficou dentro do limite de caracteres.
- A terceira ocorrencia vem de tarefas distintas, nao de tentativas repetidas da mesma sessao.
- A nova skill tem escopo claro, gatilho forte e nao duplica skill existente.

## Arquivos de apoio
- Memoria viva: ../../docs/task-memory.md
- Template de memoria: ../../templates/task-memory.md
- Padrao de skills: ../../docs/skill-standards.md
- Verificacao: ../../installers/verify-framework.sh

## Exemplos de uso
- Codex: `$skill-evolution-loop Registre este padrao recorrente e decida se ja virou skill.`
- Claude Code: `/skill-evolution-loop Atualize a memoria do framework apos esta tarefa.`
