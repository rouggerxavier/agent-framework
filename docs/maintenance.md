# Manutencao

## Regras

- Mantenha cada `SKILL.md` curto e modular.
- Mova conteudo longo para `rubrics/`, `workflows/`, `templates/` ou `docs/`.
- Nao salve secrets, tokens, senhas, `.env`, chaves privadas ou dados sensiveis.
- Revise `description` de cada skill para nao poluir contexto.
- Evite duplicar a mesma checklist em varias skills.
- Prefira exemplos curtos de uso para Codex e Claude Code.
- Rode `bash installers/verify-framework.sh` antes de commit.

## Atualizar uma skill

1. Edite `skills/<nome>/SKILL.md`.
2. Mantenha frontmatter `name` e `description`.
3. Atualize rubrics/workflows/templates se a skill depender deles.
4. Rode verificacao.
5. Instale com `bash installers/install-all.sh`.

## Adicionar uma skill

1. Crie `skills/<nome>/SKILL.md`.
2. Use nome em kebab-case.
3. Inclua objetivo, quando usar, quando nao usar, entradas, workflow, saida, aceite e exemplos.
4. Rode `verify-framework.sh`.
