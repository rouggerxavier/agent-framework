# Skill vendorizada

Esta skill nao segue `docs/skill-standards.md` porque e importada verbatim de
um projeto de terceiros, para preservar o trigger e as instrucoes exatamente
como o autor original desenhou.

- Origem: https://github.com/pbakaus/impeccable
- Commit vendorizado: `114ea1d3838fca73b253af45f873b9c4f5f213c8` (2026-09-28)
- Versao da skill (frontmatter `SKILL.md`): 4.4.0
- Versao do launcher (`scripts/VERSION`): 0.1.6
- Licenca: Apache 2.0 (ver `LICENSE`); `NOTICE.md` cobre conteudo MIT embutido
  em `reference/ios.md` e `reference/android.md`.
- Conteudo copiado da variante `.claude/skills/impeccable/` do upstream
  (build especifico para Claude Code). O upstream tambem gera uma variante
  `.agents/skills/impeccable/` para harnesses genericos (Codex incluso), cuja
  unica diferenca funcional relevante e o caminho de fallback hardcoded do
  launcher (`.claude/skills/impeccable/scripts/...` vs
  `.agents/skills/impeccable/scripts/...`) e a sintaxe de exemplo do comando
  (`/impeccable` vs `$impeccable`). O mecanismo primario (resolucao dinamica
  de `<skill-base-dir>`) e identico nas duas variantes e independe desse
  texto; o caminho hardcoded so e usado como fallback quando o runtime falha
  em reportar seu proprio diretorio base. Por isso um unico source aqui serve
  tanto `installers/install-claude.sh` (`~/.claude/skills`) quanto
  `installers/install-codex.sh` (`~/.agents/skills`) sem alteracao.

## Atualizar esta skill

1. Clone `https://github.com/pbakaus/impeccable` numa pasta temporaria.
2. Copie `.claude/skills/impeccable/{SKILL.md,reference,scripts}` por cima
   deste diretorio, preservando `LICENSE`, `NOTICE.md` e este arquivo.
3. Atualize o commit, a versao do SKILL.md e a versao do launcher acima.
4. Rode `bash installers/verify-framework.sh`.

## Uso

Disponivel para Codex (`$impeccable`) e Claude Code (`/impeccable`). Ver
`docs/usage-claude.md` e `docs/usage-codex.md`. Quando o Claude Code for
mexer em frontend, use junto com a skill `design` (Claude-only); o Codex usa
`impeccable` sozinho, sem equivalente a `design`.
