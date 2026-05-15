---
name: brainstorm-lab
description: Use para explorar ideias, alternativas, tradeoffs e caminhos iniciais quando o objetivo ainda esta aberto ou precisa de divergencia antes da decisao.
---

# Brainstorm Lab

## Objetivo
Gerar opcoes fortes, comparar caminhos e convergir para uma direcao pratica sem pular cedo para implementacao.

## Entrada esperada
- Objetivo, problema ou oportunidade.
- Contexto de negocio, usuario, produto ou codigo quando existir.
- Restricoes conhecidas: tempo, stack, custo, risco, prazo ou qualidade.

## Workflow objetivo
1. Reescreva o objetivo em uma frase clara.
2. Liste restricoes, incertezas e criterios de sucesso.
3. Gere de 3 a 7 abordagens distintas.
4. Compare impacto, esforco, risco e dependencia de cada abordagem.
5. Recomende um caminho e indique o primeiro experimento ou proxima acao.

## Saida obrigatoria
- Resumo do problema.
- Lista de opcoes com pros, contras e riscos.
- Recomendacao objetiva.
- Proximos passos em ordem.
- Perguntas em aberto somente se bloquearem a decisao.

## Criterios de qualidade
- As opcoes devem ser realmente diferentes, nao variacoes cosmeticas.
- A recomendacao deve considerar as restricoes fornecidas.
- Evite ideias vagas; cada opcao precisa ser acionavel.
- Declare suposicoes relevantes.

## Arquivos de apoio
Nao copie estes checklists na skill; aplique-os a partir daqui.
- Rubric: ../../rubrics/architecture.md (ao avaliar tradeoffs tecnicos)
- Template: ../../templates/prompt-package.md (ao empacotar a direcao escolhida)

## Exemplos curtos de uso
- `$brainstorm-lab Como podemos reduzir abandono no onboarding B2B?`
- `$brainstorm-lab Gere alternativas para migrar este app sem reescrever tudo.`
