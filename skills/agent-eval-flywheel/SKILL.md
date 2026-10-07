---
name: agent-eval-flywheel
description: Use para implementar e executar o ciclo de melhoria contínua (Eval Flywheel) de agentes, transformando traces de produção em datasets curados, gerando testes sintéticos, rodando LLM-as-judge e guiando refinos de prompt e guardrails.
---

# Agent Eval Flywheel

## Objetivo
Fechar o ciclo de qualidade contínua de agentes de IA através da metodologia *Eval Flywheel*: capturar e higienizar traces reais de produção, identificar clusters de falhas, gerar cenários de teste sintéticos, aplicar avaliações com LLM-as-a-judge e guiar melhorias quantificáveis em prompts, guardrails e políticas de decisão.

## Quando usar
- Ao estabelecer ou rodar o processo contínuo de qualidade de um agente em produção (ex: conversas reais de WhatsApp, web chat, chamadas de tools).
- Para transformar falhas pontuais relatadas por usuários em casos de teste reproduzíveis no dataset de benchmark.
- Ao gerar cenários sintéticos adversariais para testar robustez de guardrails.
- Para rodar rodadas de avaliação pré e pós-refatoração (A/B benchmark) garantindo ausência de regressão.
- Ao calibrar critérios de LLM-as-a-judge e rubricas automáticas de conformidade.

## Quando nao usar
- Para planejar do zero apenas a matriz inicial de testes sem dados de execução (use `agent-eval-planner`).
- Para rodar testes unitários tradicionais de software (use `test-strategy-builder`).
- Para inspeção manual de uma única mensagem de erro sem intenção de alimentar o dataset contínuo.

## Entradas esperadas
- Fonte de traces/conversas de produção (anonimizadas, sem PII).
- Agente alvo, com prompt atual, guardrails e definições de tools.
- Rubricas de avaliação esperadas (ex: fidelidade factual, ausência de alucinação, respeito ao tom, restrição de escopo).
- Critérios de sucesso quantitativos (ex: taxa de aprovação > 95%, regressão zero em regras P0).

## Workflow
1. **Coleta e anonimização de traces:**
   - Selecionar amostra de turnos ou sessões completas em produção.
   - Filtrar rigorosamente PII (nomes, telefones, e-mails, endereços, cartões) antes de compor o dataset de avaliação.
   - Isolar sessões com sinais de insatisfação: desistência precoce, fallback acionado, intervenção humana ou repetição de perguntas.

2. **Clusterização de falhas e análise de causa:**
   - Agrupar falhas por categoria:
     - Falha de recuperação/grounding (não encontrou dados).
     - Alucinação ou invenção de fatos comerciais.
     - Violação de guardrail (tentou chamar tool não autorizada).
     - Tom de voz ou insistência excessiva.
   - Priorizar os clusters por frequência e severidade (P0/P1/P2).

3. **Curadoria do Golden Dataset & geração sintética:**
   - Converter casos representativos em pares `(input_context, expected_behavior_rubric)`.
   - Gerar variações sintéticas dos casos de borda (*adversarial prompts*, ambiguidade) para evitar overfitting em um único exemplo literal.

4. **Execução do benchmark (LLM-as-a-Judge):**
   - Rodar o benchmark com o agente atual.
   - Aplicar avaliador automatizado com rubrica estruturada (veredicto booleano + justificativa concisa).
   - Registrar taxa de aprovação (*pass rate*) da linha de base.

5. **Iteração, mitigação e validação de regressão:**
   - Ajustar o prompt do agente, guardrails ou Next Action Policy para mitigar a falha identificada.
   - Reexecutar o benchmark completo:
     - Confirmar que a falha foi resolvida.
     - Garantir que nenhum caso de teste anterior quebrou (taxa de regressão zero).
   - Preencher `templates/agent-eval-flywheel-report.md`.

## Saida obrigatoria
- Relatório de ciclo de avaliação preenchido contendo:
  - Tamanho do dataset e fontes de amostragem.
  - Distribuição dos clusters de falha.
  - Resultados antes vs depois da intervenção (Pass Rate %).
  - Mudanças aplicadas em prompts/guardrails.
  - Verificação de não-regressão.

## Criterios de aceite
- Nenhum trace de teste contém dados pessoais reais desprotegidos.
- O julgamento (LLM-as-judge) tem justificativa auditável por trás de cada nota.
- A melhoria é comprovada por métrica comparativa antes e depois.
- A skill não propõe "prompt hacks" frágeis que resolvam um caso mas quebrem outros.

## Arquivos de apoio
- Template: `templates/agent-eval-flywheel-report.md`
- Skills relacionadas: `agent-eval-planner`, `agent-guardrails-implementer`, `skill-evolution-loop`

## Exemplos de uso
- "Pegue os últimos 50 chats com fallback no GranKasa, categorize as falhas e adicione ao dataset de eval do agente."
- "Execute uma rodada de eval flywheel para verificar se o novo prompt reduziu as invenções de horários de visita."
- "Gere 20 cenários sintéticos de teste adversariais para tentar burlar os limites de escopo do assistente."
