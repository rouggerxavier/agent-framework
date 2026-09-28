---
name: design
description: Use no Claude Code, antes de qualquer edicao de frontend/UI, para carregar a skill nativa de design do proprio harness Claude e combinar com impeccable.
---

# Design

## Objetivo
Garantir que o Claude Code, antes de tocar frontend, carregue a skill de
design nativa do proprio harness (nao vendorizada aqui) e execute o trabalho
em conjunto com `impeccable`, sem impor uma ordem ou metodo fixo.

## Quando usar
- Sempre que o Claude Code for criar, redesenhar, revisar ou ajustar UI,
  componente visual, layout, tema, copy visual ou qualquer artefato de
  frontend.
- Antes da primeira edicao de arquivo de frontend na tarefa, nao apenas no
  fechamento.

## Quando nao usar
- No Codex ou em qualquer outro harness sem skill de design nativa: use
  apenas `impeccable`. Esta skill so existe porque o Claude Code expoe uma
  skill de design propria do harness; nao ha equivalente para replicar em
  outro agente.
- Para trabalho puramente backend/nao-visual.
- Para o audit report do framework em si; depois de desenhar, use
  `ui-ux-pro-max-audit` se o pedido for uma auditoria formal com o template
  do framework.

## Entradas esperadas
- Descricao da tela, componente ou fluxo de frontend a criar/alterar.
- Contexto de produto, publico e restricoes visuais quando existirem.

## Workflow
1. Antes de qualquer edicao de arquivo de frontend, liste as skills
   disponiveis neste harness e identifique a skill de design nativa (por
   exemplo `artifact-design` ou outra skill de design/frontend embutida no
   Claude Code desta sessao). Carregue-a com a tool `Skill`.
2. Carregue tambem `impeccable` (ver `../impeccable/SKILL.md`) para o
   vocabulario de comandos (`shape`, `craft-floor`, `audit`, `critique`,
   `polish`, etc.) e a base de qualidade que ela aplica.
3. As duas skills sao obrigatorias juntas nesta etapa; a ordem entre elas e
   como combinar as duas orientacoes fica livre — siga o que fizer mais
   sentido para a tarefa, contanto que o resultado final respeite as duas.
4. Se o harness nao expuser nenhuma skill de design nativa nesta sessao,
   registre isso e prossiga apenas com `impeccable`; nao invente ou
   substitua por outra skill de terceiros.
5. Implemente o frontend informado pelas duas fontes de orientacao.

## Saida obrigatoria
- Confirmacao de que a skill de design nativa do harness foi carregada (ou
  registro explicito de que nao havia nenhuma disponivel) e de que
  `impeccable` foi usada junto.
- O frontend implementado ou revisado de acordo com as duas.

## Criterios de aceite
- Nenhuma edicao de frontend no Claude Code comeca sem antes carregar a
  skill de design nativa do harness, quando ela existir.
- `impeccable` nunca e substituida ou pulada em trabalho de frontend.
- Esta skill nao e usada, referenciada nem exigida no Codex.
- Nao duplique aqui o conteudo de `impeccable`; apenas referencie.

## Arquivos de apoio
- Skill irma: `../impeccable/SKILL.md`.

## Exemplos de uso
- Claude Code: `/design Redesenhe a tela de checkout seguindo o design nativo do harness junto com impeccable.`
