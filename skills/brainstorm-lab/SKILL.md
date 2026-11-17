---
name: brainstorm-lab
description: Use para explorar caminhos quando o objetivo ou a abordagem ainda esta aberta - enquadra o problema, gera opcoes de mecanismos diferentes, compara pelos criterios do usuario e recomenda um caminho com primeiro teste.
---

# Brainstorm Lab

## Objetivo
Sair de um objetivo aberto para uma direcao escolhida e um primeiro teste barato,
sem pular para implementacao.

## Quando usar
- Objetivo, problema ou oportunidade ainda sem caminho definido.
- Varias abordagens possiveis e nenhuma claramente melhor.
- Usuario pede ideias, alternativas ou "como poderiamos".

## Quando nao usar
- Plano ou decisao ja formada que precisa de teste: `grilling`.
- Escolha tecnica entre opcoes ja conhecidas, a registrar: `architecture-decision`.
- Caminho ja escolhido, falta quebrar em etapas: `execution-plan-builder`.
- Pedido claro e executavel: execute.

## Entradas esperadas
- Objetivo, problema ou oportunidade.
- Contexto disponivel: codigo, docs, notas do projeto, tentativas anteriores.
- Restricoes: tempo, stack, custo, risco, prazo, qualidade.

## Workflow
1. **Ancore antes de idear.** Leia o que ja existe: codigo, docs, notas, o que ja
   foi tentado. Ideia que ignora o contexto e descartada.
2. **Enquadre.** Escreva o problema em uma frase, quem sente, e o criterio
   observavel de que foi resolvido. Pedido que ja vem como solucao ("quero um
   X"): suba um nivel e pergunte que resultado X deveria produzir.
3. **Pergunte so o que muda as opcoes.** No maximo 3 perguntas, todas de uma vez,
   cada uma com resposta recomendada. Nada bloqueia: declare a suposicao e siga.
4. **Divirja por mecanismo.** Gere 3 a 5 opcoes que diferem em *como* resolvem,
   nao em detalhe. Inclua sempre: nao fazer / versao minima, e reusar o que ja
   existe. Menos de 3 opcoes reais: diga isso, nao encha.
5. **Exponha a aposta de cada opcao.** Mecanismo em uma linha, o que precisa ser
   verdade para funcionar (suposicao mais arriscada) e quanto custa descobrir.
6. **Convirja.** Elimine opcoes dominadas. Compare as restantes pelos criterios e
   restricoes do usuario; impacto/esforco/risco so quando ele nao deu criterio.
7. **Recomende uma.** Diga o que faria mudar a recomendacao e defina o primeiro
   teste: acao pequena, sinal de passa/falha.
8. **Pare.** Nao implemente. Encaminhe: `grilling` para testar a escolha,
   `execution-plan-builder` para planejar.

## Saida obrigatoria
- Problema em uma frase e criterio de sucesso.
- Suposicoes declaradas.
- Tabela de opcoes: mecanismo | precisa ser verdade | pros | contras.
- Recomendacao unica, com o que a derrubaria.
- Primeiro teste: acao e sinal de passa/falha.
- Perguntas em aberto somente se bloquearem a decisao.

Proporcao: problema pequeno recebe poucas linhas, sem tabela.

## Criterios de aceite
- Opcoes diferem em mecanismo; nenhuma e variacao cosmetica de outra.
- "Nao fazer / versao minima" e "reusar o existente" foram consideradas.
- Cada opcao e acionavel e nomeia sua suposicao mais arriscada.
- A comparacao usa os criterios e restricoes do usuario.
- A recomendacao e uma so, com condicao de reversao e primeiro teste verificavel.
- Nenhuma implementacao iniciada.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Rubric: ../../rubrics/architecture.md (ao avaliar tradeoffs tecnicos)
- Template: ../../templates/prompt-package.md (ao empacotar a direcao escolhida)

## Exemplos de uso
- `$brainstorm-lab Como podemos reduzir abandono no onboarding B2B?`
- `$brainstorm-lab Gere alternativas para migrar este app sem reescrever tudo.`
