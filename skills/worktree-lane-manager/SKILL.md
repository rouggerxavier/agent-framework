---
name: worktree-lane-manager
description: Use para criar e coordenar lanes paralelas em Git worktrees para dispatches independentes, evitando conflitos e preservando ordem segura de integracao.
---

# Worktree Lane Manager

## Objetivo

Permitir que o orquestrador mantenha varios workers produtivos ao mesmo tempo sem
colocar dois writers no mesmo checkout ou no mesmo write scope.

## Quando usar

- Dois ou mais dispatches elegiveis podem escrever em paralelo.
- O checkout principal tem mudancas que nao pertencem ao worker.
- Um developer precisa trabalhar enquanto outro branch aguarda testes, review ou
  decisao.
- Uma nova spec/fase aprovada pode avancar sem depender da lane bloqueada.

## Quando nao usar

- Os dispatches alteram os mesmos arquivos ou contratos compartilhados.
- Uma tarefa depende do resultado ainda nao integrado da outra.
- Migration/schema, lockfile, configuracao central ou outro recurso serializado
  cria conflito inevitavel.
- O trabalho e read-only; nesse caso nao precisa de worktree exclusiva.

## Elegibilidade

Antes de abrir lanes em paralelo, confirme:

1. dependencias satisfeitas;
2. `allowed_files` disjuntos, incluindo arquivos gerados/contratos afetados;
3. nenhum shared mutable contract editado por duas lanes;
4. base commit conhecida;
5. ordem de integracao definida;
6. cada writer recebe branch e worktree exclusivas.

Se houver duvida real de conflito, serialize.

## Lane identity

Persista apenas dados portaveis:

- lane id;
- task/dispatch id;
- branch;
- base commit;
- write scope;
- status.

O caminho absoluto da worktree e runtime-only e nao deve ir para artefatos
versionados.

Branch sugerida:

`agent/<run-id>/<task-id>-<slug>`

A localizacao fisica da worktree e escolha do ambiente/Maestri.

## Workflow

1. Calcule dispatches elegiveis.
2. Detecte sobreposicao de `allowed_files` e contratos compartilhados.
3. Para cada writer independente, reserve uma lane.
4. Crie branch/worktree a partir da base correta. Em Git puro, a forma esperada
   e equivalente a:

```bash
git worktree add <runtime-path> -b agent/<run-id>/<task-id>-<slug> <base-sha>
```

   O caminho e escolhido no runtime e nao e persistido.
5. Valide `git status --short --branch` dentro da nova worktree antes de
   despachar.
6. Registre lane + branch + base commit em `ORCHESTRATION.md` e no notebook.
7. Entregue ao worker o dispatch e a lane; ele nao troca de branch/worktree.
8. Ao retornar:
   - valide resultado, diff e branch;
   - rode testes/review previstos;
   - marque a lane `ready_to_integrate`, `changes_required`,
     `awaiting_decision` ou `blocked`.
9. Integre na ordem de dependencias. Antes de integrar uma lane tardia, atualize-a
   contra a base resultante quando necessario e revalide o que foi afetado.
10. So depois de integracao/abandono limpe branch/worktree; nao remova worktree
    ambigua ou com mudancas nao preservadas. A limpeza e equivalente a:

```bash
git worktree remove <runtime-path>
git branch -d <lane-branch>   # somente quando integrada/segura
```

## Decisoes durante uma lane

Se surgir `user_required`:

- mantenha branch/worktree intacta;
- marque a lane `awaiting_decision`;
- registre `Q-###`;
- libere o agente/lane logica para outro trabalho apenas se o estado local estiver
  preservado com seguranca;
- preencha outra lane com trabalho independente.

## Saida obrigatoria

- lanes criadas ou recusadas com motivo;
- branch/base/write scope de cada writer;
- status e ordem de integracao;
- worktrees seguras para dispatch ou limpeza.

## Criterios de aceite

- Nenhum writer compartilha checkout.
- Nenhum write scope conflitante roda em paralelo.
- O orquestrador sabe base/branch/owner/status de toda lane.
- Uma lane bloqueada nao impede scheduling independente.
- Integracao respeita dependencias e revalida conflitos reais.
