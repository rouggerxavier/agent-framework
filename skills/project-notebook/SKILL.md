---
name: project-notebook
description: Mantem notas persistentes do projeto com indice, perguntas pendentes, progresso e historico de fases sem duplicar evidence ou decisoes formais.
---

# Project Notebook

## Objetivo

Manter uma area humana e persistente para o orquestrador explicar o que aconteceu,
o que esta pendente, quais perguntas dependem do usuario e quais fases ja foram
implementadas.

O notebook nao substitui `DECISIONS.md`, `EVIDENCE.md`, `STATE.md` ou os
contratos. Ele aponta para essas fontes e resume o projeto para retomada rapida.

## Estrutura

Instancie em:

```text
.agent/notes/
  INDEX.md
  QUESTIONS.md
  PROGRESS.md
  PHASES.md
```

## Responsabilidades

### INDEX.md

Painel de entrada:

- objetivo atual;
- fase/spec ativa;
- worktrees/lanes em andamento;
- quantidade de perguntas pendentes;
- ultima entrega relevante;
- proxima operacao;
- links para as demais notas e artefatos formais.

### QUESTIONS.md

Fila de decisoes/perguntas para o usuario.

Cada pergunta tem:

- ID;
- status;
- data;
- task/dispatch/fase afetados;
- pergunta;
- contexto minimo;
- opcoes reais;
- recomendacao do orquestrador, quando houver;
- impacto de cada opcao;
- trabalho bloqueado;
- trabalho que pode continuar;
- resposta do usuario;
- decision ID criado apos resposta.

### PROGRESS.md

Diario conciso do que foi feito:

- specs criadas;
- implementacoes integradas;
- testes/reviews concluidos;
- correcoes relevantes;
- branches/worktrees integradas;
- proximo trabalho elegivel.

Nao copie logs ou evidence bruto.

### PHASES.md

Historico resumido de fases/specs:

- fase;
- objetivo;
- status;
- principais entregas;
- decisoes relevantes;
- tasks concluidas/pendentes;
- resultado de verificacao;
- data de inicio/fechamento;
- proxima fase relacionada.

## Pergunta pendente

Quando `decision-authority-router` classificar uma escolha como
`user_required`:

1. crie um ID `Q-###`;
2. adicione a entrada em `QUESTIONS.md`;
3. marque apenas os dispatches/tasks dependentes como `awaiting_decision`;
4. registre o ID da pergunta no estado de orquestracao;
5. atualize `INDEX.md`;
6. continue qualquer trabalho independente elegivel.

Quando o usuario responder:

1. atualize a pergunta com resposta e status `answered`;
2. crie/atualize a decisao formal em `DECISIONS.md`;
3. vincule o Decision ID na pergunta;
4. atualize spec/plano/dispatches afetados;
5. remova o bloqueio de decisao;
6. recoloque a tarefa na fila elegivel.

## Regras

- Nao guardar secrets, tokens ou dados pessoais desnecessarios.
- Nao transformar detalhe local de implementacao em pergunta.
- Nao usar o notebook como fonte de verdade quando um artefato formal existe.
- Atualizacoes devem ser curtas e navegaveis; detalhes ficam nos artefatos
  referenciados.
- O orquestrador e o unico writer padrao do notebook.

## Saida obrigatoria

Depois de uma mudanca relevante no ciclo, o notebook deve permitir responder
rapidamente:

- o que ja foi feito;
- o que esta rodando;
- o que esta bloqueado e por que;
- o que depende do usuario;
- quais fases ja terminaram;
- qual e o proximo trabalho independente.
