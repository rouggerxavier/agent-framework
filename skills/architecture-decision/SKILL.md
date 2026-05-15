---
name: architecture-decision
description: Use para tomar ou documentar decisoes de arquitetura com contexto, opcoes, tradeoffs, riscos, decisao e consequencias.
---

# Architecture Decision

## Objetivo
Produzir decisao de arquitetura defensavel, rastreavel e pratica para guiar implementacao.

## Quando usar
- Ao escolher entre alternativas tecnicas relevantes.
- Quando a decisao afeta contratos, dados, custo, escala ou manutencao.
- Para documentar ADR curto.

## Quando nao usar
- Para preferencia local de estilo.
- Para decisao ja imposta sem tradeoff real.
- Para implementar sem avaliar impacto.

## Entradas esperadas
- Problema arquitetural.
- Contexto tecnico e restricoes.
- Opcoes consideradas.
- Requisitos nao funcionais.

## Workflow
1. Declare problema e contexto.
2. Liste requisitos funcionais e nao funcionais.
3. Compare opcoes viaveis com tradeoffs.
4. Escolha decisao e motivo.
5. Defina consequencias, riscos e criterio de revisao.

## Saida obrigatoria
- Contexto.
- Opcoes consideradas.
- Decisao.
- Consequencias.
- Riscos e mitigacoes.
- Validacao ou experimento recomendado.

## Criterios de aceite
- A decisao deve orientar codigo.
- Tradeoffs devem incluir manutencao e reversibilidade.
- Evite conclusao sem criterio.
- Indique quando revisar a decisao.

## Exemplos de uso
- Codex: `$architecture-decision Decida entre fila, cron ou webhook para processamento assincrono.`
- Claude Code: `/architecture-decision Documente PostgreSQL vs DynamoDB para este produto.`
