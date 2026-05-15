# agent-framework

Framework pessoal e versionavel de skills, rubrics, workflows, templates e docs para Codex e Claude Code.

## Objetivo

Manter `~/agent-framework` como fonte principal das suas skills reutilizaveis. Os installers sincronizam essas skills para:

- Codex: `~/.agents/skills`
- Claude Code: `~/.claude/skills`

O framework e seguro para Git privado quando usado sem secrets, tokens, senhas, `.env`, chaves privadas ou dados sensiveis.

## Estrutura

```text
agent-framework/
  README.md
  .gitignore
  skills/
  rubrics/
  workflows/
  templates/
  installers/
  docs/
```

## Instalar no Codex

```bash
bash ~/agent-framework/installers/install-codex.sh
```

Use skills com `$skill-name`:

```text
$project-context-loader Prepare contexto do repo.
$diff-reviewer Revise o diff atual.
```

## Instalar no Claude Code

```bash
bash ~/agent-framework/installers/install-claude.sh
```

Use skills com `/skill-name`:

```text
/repo-map-builder Mapeie entrypoints e rotas.
/bug-repro-lab Investigue este stack trace.
```

## Instalar em ambos

```bash
bash ~/agent-framework/installers/install-all.sh
```

Os installers copiam apenas diretorios em `skills/` que possuem `SKILL.md`. Skills externas que nao existem no framework nao sao removidas. Skills de mesmo nome sao movidas para backup oculto antes de copiar a versao do framework.

## Verificar

```bash
bash ~/agent-framework/installers/verify-framework.sh
```

## Atualizar em outro computador

```bash
cd ~/agent-framework
git pull --ff-only
bash installers/verify-framework.sh
bash installers/install-all.sh
```

Ou use:

```bash
bash ~/agent-framework/installers/update-framework.sh
bash ~/agent-framework/installers/install-all.sh
```

## Adicionar nova skill

```text
skills/nova-skill/
  SKILL.md
```

O `SKILL.md` deve ter frontmatter:

```yaml
---
name: nova-skill
description: Use para ...
---
```

Mantenha a skill curta. Conteudo longo deve ir para `rubrics/`, `workflows/`, `templates/` ou `docs/`.

## GitHub privado

```bash
cd ~/agent-framework
git init
git add .
git commit -m "Initial agent framework"
git branch -M main
git remote add origin git@github.com:SEU_USUARIO/agent-framework.git
git push -u origin main
```

Nao inclua secrets. Revise `.gitignore` antes do primeiro commit.

## Exemplos combinando skills

Bugfix:

```text
$project-context-loader Prepare contexto.
$bug-repro-lab Reproduza o bug.
$test-strategy-builder Defina regressao.
$diff-reviewer Revise o patch.
```

Refatoracao de API:

```text
$repo-map-builder Localize rotas e contratos.
$api-contract-auditor Avalie compatibilidade.
$implementation-planner Divida em fases.
$release-verifier Verifique readiness.
```

Handoff:

```text
$context-compressor Gere resumo de retomada.
$handoff-builder Monte handoff para Claude Code.
```
