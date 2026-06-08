---
name: coding-standards-enforcer
description: Use para descobrir e aplicar padroes locais (nomes, estrutura, estilo, erros, testes) antes de refatorar, gerar patch ou criar arquivo, evitando abstracoes novas e mudancas fora do padrao do repo.
---

# Coding Standards Enforcer

## Objetivo
Descobrir as convencoes reais do repositorio e aplica-las antes de gerar ou alterar codigo, para que a mudanca pareca escrita por quem mantem o projeto.

## Quando usar
- Antes de refatorar, gerar patch ou criar arquivo novo em repo com convencoes ja estabelecidas.
- Quando o codigo gerado tende a introduzir abstracao, lib ou estilo fora do padrao local.
- Ao revisar diff cujo risco principal e aderencia ao padrao, nao bug funcional.
- Em repo desconhecido, antes de escrever a primeira linha.

## Quando nao usar
- Para revisar risco funcional ou regressao; use `diff-reviewer`.
- Para definir um padrao novo do zero; use `architecture-decision`.
- Para mudanca trivial em arquivo que ja segue o padrao visivel.

## Entradas esperadas
- Objetivo da mudanca e arquivos/area afetados.
- Codigo vizinho representativo (mesmo modulo, mesma camada).
- Configs de lint/format/tsconfig/editorconfig, se existirem.
- Padroes declarados em CLAUDE.md, AGENTS.md, README ou docs.

## Workflow
1. Localize 2-3 arquivos vizinhos e configs de lint/format como fonte de verdade do padrao.
2. Extraia convencoes: nomes, estrutura de arquivo, imports, tratamento de erro, logging, testes e comentarios.
3. Compare o codigo proposto ou alterado com essas convencoes e liste divergencias.
4. Classifique por severidade: bloqueia merge, ajustar agora ou opcional.
5. Aplique a correcao minima para alinhar ao padrao, sem refatorar alem do objetivo.
6. Aponte quando o padrao local conflita com o objetivo e exige decisao (ADR) em vez de ajuste silencioso.

## Saida obrigatoria
Conforme `../../templates/audit-report.md`, com status (`aprovado`, `aprovado com ressalvas` ou `bloqueado`), divergencias por severidade com evidencia (arquivo vizinho ou config que define o padrao) e verificacoes (lint/format/test).

## Criterios de aceite
- Padrao vem de evidencia no repo (arquivo ou config), nao de preferencia pessoal.
- Escopo do ajuste fica preso ao objetivo; sem refatoracao oportunista.
- Conflito entre padrao e objetivo vira decisao explicita, nao mudanca silenciosa de contrato.
- Demais criterios: rubric em Arquivos de apoio.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Rubric: ../../rubrics/coding-standards.md
- Template: ../../templates/audit-report.md
- Contexto: ../../skills/repo-map-builder/SKILL.md
- Review de risco: ../../skills/diff-reviewer/SKILL.md

## Exemplos de uso
- Codex: `$coding-standards-enforcer Alinhe este patch aos padroes do modulo antes do commit.`
- Claude Code: `/coding-standards-enforcer Descubra e aplique as convencoes locais antes de refatorar este arquivo.`
