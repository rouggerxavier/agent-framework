---
name: decision-authority-router
description: Classifica escolhas descobertas durante execucao como locais, registraveis pelo orquestrador ou obrigatorias para o usuario antes de continuar.
---

# Decision Authority Router

## Objetivo

Evitar dois extremos: perguntar ao usuario por detalhe irrelevante ou permitir
que um agente tome silenciosamente uma decisao material.

## Quando usar

- Quando um worker encontra mais de uma solucao plausivel.
- Quando a implementacao revela uma lacuna na spec ou no plano.
- Antes de transformar uma descoberta em entrada de `DECISIONS.md`.
- Quando o orquestrador precisa decidir se pausa o usuario ou continua sozinho.

## Workflow

1. Descreva a escolha concreta e as alternativas reais.
2. Compare a escolha com requisitos, spec, contratos e decisoes aceitas.
3. Classifique em uma das tres autoridades:
   - `local`: detalhe interno, reversivel e sem mudanca de contrato/semantica;
   - `record`: material e reutilizavel, mas dentro do objetivo aprovado e
     reversivel o suficiente para o orquestrador aceitar;
   - `user_required`: muda intencao, contrato externo, risco, custo, seguranca,
     dados, producao ou cria lock-in relevante.
4. Para `local`, devolva a escolha ao worker e nao crie decisao de projeto.
5. Para `record`, o orquestrador escolhe, registra contexto/consequencias em
   `DECISIONS.md` e atualiza dispatches afetados.
6. Para `user_required`, crie uma pergunta curta com contexto, opcoes,
   consequencias e recomendacao quando houver. Pause somente trabalho dependente.
7. Nunca use "preferencia pessoal" como justificativa para escalar.

## Saida obrigatoria

- classificacao;
- motivo;
- quem tem autoridade;
- artefatos/dispatches afetados;
- proxima acao.

## Criterios de aceite

- Decisoes locais nao poluem `DECISIONS.md`.
- Decisoes materiais nao ficam escondidas em conversa de worker.
- O usuario so e interrompido quando sua escolha realmente muda o produto,
  contrato, risco ou compromisso relevante.

## Arquivos de apoio

- Politica: ../../kernel/orchestration-policy.md
- Decisoes: ../../templates/project-decisions.md
- Dispatch: ../../templates/agent-dispatch.md
