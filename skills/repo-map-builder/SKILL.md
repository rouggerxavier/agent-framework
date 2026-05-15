---
name: repo-map-builder
description: Use para mapear repositorios com modulos, entrypoints, rotas, contratos, dados, testes, configs e areas de risco.
---

# Repo Map Builder

## Objetivo
Produzir um mapa tecnico navegavel do repositorio para acelerar onboarding, refatoracao, auditoria e localizacao de bugs.

## Quando usar
- Ao analisar repo novo ou grande.
- Antes de mudancas cross-cutting.
- Quando e preciso localizar onde uma feature, bug ou contrato vive.

## Quando nao usar
- Para mudanca pequena em arquivo ja localizado.
- Quando ja existe mapa atualizado e confiavel.
- Para documentacao longa de produto.

## Entradas esperadas
- Caminho do repositorio.
- Objetivo do mapa.
- Escopo opcional: frontend, backend, API, infra ou testes.

## Workflow
1. Localize manifestos, entrypoints, roteadores, modulos e configs.
2. Identifique fronteiras: UI, API, jobs, banco, integracoes e testes.
3. Mapeie fluxos principais e dependencias internas.
4. Aponte arquivos de alto impacto e areas com pouca cobertura.
5. Entregue mapa orientado a acao.

## Saida obrigatoria
- Estrutura principal.
- Mapa de modulos e responsabilidades.
- Entry points e comandos.
- Areas de teste e cobertura aparente.
- Pontos de risco e leituras seguintes.

## Criterios de aceite
- Use caminhos reais e nomes reais de modulos.
- Marque incertezas em vez de concluir sem evidencia.
- Separe fato observado de opiniao arquitetural.
- O mapa deve reduzir tempo de navegacao no repo.

## Arquivos de apoio
Etapa inicial dos workflows abaixo; nao duplicar os passos deles aqui.
- Workflow: ../../workflows/api-refactor.md
- Workflow: ../../workflows/frontend-refactor.md

## Exemplos de uso
- Codex: `$repo-map-builder Crie um mapa do repo antes da refatoracao de API.`
- Claude Code: `/repo-map-builder Encontre entrypoints, rotas e testes deste projeto.`
