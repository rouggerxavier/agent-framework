---
name: project-context-loader
description: Use para grounding focado e reutilizavel; persistencia e varredura ampla dependem do modo e de invalidacao concreta.
---

# Project Context Loader

## Objetivo
Criar um resumo curto e reutilizavel do projeto para reduzir repeticao de contexto antes de implementar, revisar, testar ou planejar.

## Quando usar
- Ao entrar em repo desconhecido.
- Antes de tarefas longas em codigo.
- Quando a conversa perdeu contexto de stack, comandos ou convencoes.

## Quando nao usar
- Para pergunta pontual sobre arquivo ja informado.
- Quando o contexto do projeto ja esta claro e recente.
- Para substituir leitura detalhada exigida pela tarefa.

## Entradas esperadas
- Caminho do repositorio.
- Objetivo da tarefa seguinte.
- Areas de interesse, se houver.

## Workflow
1. Receba goal, mode e contexto ja disponivel.
2. Em `fast`, leia somente arquivos relevantes e padroes locais necessarios.
3. Em `standard`, faca grounding focado de modulos/contratos envolvidos.
4. Em `critical`, localize manifestos, configs, docs, scripts e artefatos
   persistentes necessarios.
5. Identifique stack, comandos, entrypoints e padroes apenas na profundidade
   proporcional ao modo.
6. Separe fatos, inferencias, assumptions e unknowns; registre arquivos lidos.
7. Reutilize o contexto. Regrounding completo so ocorre se commit mudou
   materialmente, escopo mudou, arquivos centrais surgiram, contexto ficou stale
   ou houve contradicao.
8. Persista em `.agent/CONTEXT.md` somente quando o kernel `critical` estiver
   ativo; `standard` pode persistir resumo leve quando houver necessidade real.

## Saida obrigatoria
- Stack e runtime.
- Comandos relevantes.
- Estrutura principal.
- Padroes locais observados.
- Riscos, lacunas e proximas leituras.
- Metadados: `generated_at`, `source_commit`, `branch`, `files_inspected`,
  `commands_verified`, `facts`, `assumptions`, `unknowns`, `stale_after`.

## Criterios de aceite
- Diferencie fato observado de inferencia.
- Inclua caminhos reais quando houver evidencia.
- Nao invente comandos ausentes.
- O resumo deve caber em prompt de retomada.
- Informacao nao verificada nunca aparece como fato.
- O contexto nao substitui `STATE.md` e deve ser revalidado quando stale.
- Skills/reviewers recebem o pacote minimo e nao repetem grounding completo.

## Arquivos de apoio
Etapa inicial dos workflows abaixo; nao duplicar os passos deles aqui.
- Workflow: ../../workflows/feature-build.md
- Workflow: ../../workflows/bugfix.md
- Rubric: ../../rubrics/coding-standards.md (padroes a observar no repo)

## Exemplos de uso
- Codex: `$project-context-loader Prepare contexto para implementar login neste repo.`
- Claude Code: `/project-context-loader Mapeie stack, comandos e convencoes antes do bugfix.`
