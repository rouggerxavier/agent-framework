---
name: execution-prompt-builder
description: Use para transformar brief ou plano de execucao em prompts por etapa para Codex, Claude Code, ChatGPT ou agentes, com verificacao, relatorio final e gate de code review.
---

# Execution Prompt Builder

## Objetivo
Converter um plano em prompts prontos para execucao, um por etapa ou por agente, mantendo contexto suficiente, escopo fechado, verificacao clara e uma obrigacao explicita de relatorio final antes do code review.

## Quando usar
- Depois de `execution-plan-builder`, `implementation-planner`, `backend-slice-planner` ou plano escrito por humano.
- Quando o usuario pedir "prompts por etapa", "prompt para o proximo agente", "delegar essa execucao" ou "quebrar em prompts".
- Quando cada etapa deve virar uma tarefa independente, auditavel e com saida padronizada.

## Quando nao usar
- Para criar o plano do zero; use `execution-plan-builder` primeiro.
- Para refinar um prompt unico simples; use `prompt-refiner`.
- Para revisar codigo ja feito; use `diff-reviewer` ou `code-review-gate`.

## Entradas esperadas
- Brief ou plano de execucao.
- Alvo: Codex, Claude Code, ChatGPT, subagent ou humano.
- Repositorio, branch, arquivos provaveis, restricoes e comandos de verificacao.
- Nivel de autonomia permitido e stop conditions.

## Workflow
1. Leia o plano e identifique etapas independentes ou sequenciais.
2. Para cada etapa, gere um prompt com objetivo, contexto minimo, read-first, escopo, restricoes, verificacao e saida esperada.
3. Inclua dependencias entre etapas e criterio de passagem para a proxima.
4. Marque pontos em que o agente deve parar e pedir decisao.
5. Adicione ao fim de todo prompt de execucao a instrucao obrigatoria de relatorio final.
6. No pacote final, indique que depois da execucao completa e hora de rodar `code-review-gate` ou `diff-reviewer`.

## Bloco obrigatorio nos prompts
Inclua este contrato, adaptando so o alvo e os comandos:

```text
Ao terminar, envie um relatorio final curto com: arquivos alterados, decisoes tomadas, comandos/testes executados e resultados, pendencias, riscos e recomendacao de proximo passo. Depois do relatorio, nao continue implementando; sinalize que e hora do code review.
```

## Saida obrigatoria
Preencha `../../templates/execution-prompt-package.md` com:
- Resumo do plano.
- Ordem dos prompts.
- Prompt por etapa.
- Dependencias e gates.
- Contrato de relatorio final.
- Recomendacao de code review.

## Criterios de aceite
- Cada prompt deve ser executavel sem depender de conversa anterior escondida.
- Cada prompt deve ter escopo pequeno e criterio de done verificavel.
- Nao criar prompts que autorizem refatoracao lateral ou expansao de escopo sem permissao.
- Todo prompt de implementacao deve exigir relatorio final e mencionar code review.
- Se o plano estiver vago, encaminhar antes para `plan-quality-checker`.
