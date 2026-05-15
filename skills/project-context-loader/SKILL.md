---
name: project-context-loader
description: Use para carregar contexto essencial de um projeto antes de trabalhar, resumindo stack, comandos, padroes, arquitetura e restricoes locais.
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
1. Localize manifestos, configs, docs e scripts.
2. Identifique stack, runtime, comandos e entrypoints.
3. Resuma padroes de arquitetura, estilo e testes.
4. Liste riscos, lacunas e arquivos relevantes.
5. Entregue contexto curto para reuso em prompts ou handoffs.

## Saida obrigatoria
- Stack e runtime.
- Comandos relevantes.
- Estrutura principal.
- Padroes locais observados.
- Riscos, lacunas e proximas leituras.

## Criterios de aceite
- Diferencie fato observado de inferencia.
- Inclua caminhos reais quando houver evidencia.
- Nao invente comandos ausentes.
- O resumo deve caber em prompt de retomada.

## Arquivos de apoio
Etapa inicial dos workflows abaixo; nao duplicar os passos deles aqui.
- Workflow: ../../workflows/feature-build.md
- Workflow: ../../workflows/bugfix.md
- Rubric: ../../rubrics/coding-standards.md (padroes a observar no repo)

## Exemplos de uso
- Codex: `$project-context-loader Prepare contexto para implementar login neste repo.`
- Claude Code: `/project-context-loader Mapeie stack, comandos e convencoes antes do bugfix.`
