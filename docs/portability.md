# Portabilidade

Fluxo recomendado para usar o framework em mais de um computador.

## No computador principal

```bash
cd ~/agent-framework
git add .
git commit -m "Update agent framework"
git push
```

## Em outro computador

```bash
git clone git@github.com:SEU_USUARIO/agent-framework.git ~/agent-framework
cd ~/agent-framework
bash installers/verify-framework.sh
bash installers/install-all.sh
```

Os installers sincronizam skills para Codex e Claude Code e, arquivo a arquivo,
`kernel/`, workflows, rubrics, templates, docs, scripts e installers para a raiz
de cada ferramenta.
Arquivos externos nao sao removidos; colisoes recebem backup.

## Atualizacoes futuras

```bash
cd ~/agent-framework
git pull --ff-only
bash installers/verify-framework.sh
bash installers/install-all.sh
```

Para projetos com estado persistente, confirme tambem:

```bash
python3 -m unittest discover -s tests -v
./scripts/framework-next --project /caminho/do/projeto
```

## Handoff entre computadores

O mesmo repositorio de trabalho pode ser clonado em caminhos diferentes em cada
maquina. `.agent/STATE.md` e versionado e compartilhado, entao nao guarda nenhum
caminho local.

```text
macOS    /Users/voce/dev/projeto
Linux    /home/voce/projeto
Windows  C:\Users\voce\dev\projeto
```

Nos tres casos o estado compartilhado registra apenas:

```json
"git": {
  "base_branch": "main",
  "working_branch": "feat/exemplo",
  "worktree": ".",
  "starting_commit": "..."
}
```

Regras:

- `git.worktree` e portatil; `.` representa a raiz do repositorio;
- a raiz absoluta e descoberta em runtime com `git rev-parse --show-toplevel`;
- caminhos absolutos sao formato legado, continuam carregando e nao invalidam o
  projeto;
- validacao nao modifica arquivos;
- normalizacao e uma operacao explicita;
- o mesmo branch pode ser usado em clones de maquinas diferentes.

O framework nao cria `.agent/STATE.local.*` para guardar o caminho do worktree:
o Git ja fornece essa informacao, entao nao ha estado local a manter.

Trocar de computador:

```bash
git pull --ff-only
./scripts/framework-next --project /caminho/local/do/projeto
```

`STATE.md` nao deve aparecer em `git status`. Se aparecer com uma mudanca de
`worktree`, o estado ainda esta no formato legado; normalize uma vez e commite:

```bash
./scripts/framework-next normalize-worktree --project /caminho/local/do/projeto
```

O comando funciona a partir da raiz do repositorio, de um subdiretorio, de uma
skill, do CLI, em CI e em um linked worktree.

## Regras de seguranca

- Edite skills somente em `~/agent-framework`.
- Nao salve `.env`, tokens, senhas, chaves privadas ou dados sensiveis.
- Use repositorio Git privado.
- Rode `verify-framework.sh` antes de instalar.
