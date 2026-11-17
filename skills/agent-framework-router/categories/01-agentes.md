---
{
  "category": "agentes",
  "keywords": [
    "agente",
    "llm",
    "prompt",
    "chatbot",
    "whatsapp",
    "assistente",
    "eval",
    "guardrail",
    "provider",
    "troca de modelo"
  ],
  "required": [
    "rubrics/agent-design.md"
  ]
}
---

# Agentes de IA

Instrucao obrigatoria, em qualquer modo e fora do limite de 4: aplique
`rubrics/agent-design.md`. Comece minimo (um agente, prompt curto, tools); camada
nova so por falha medida; protecao na entrada e nos efeitos, nunca na fala; corrija
pela escada (descricao de tool, prompt, dado pronto, contrato tipado, verificacao
estreita, codigo). Sequencia em `workflows/agent-workflow.md`. Infra de canal
(fila, outbox, webhook, persistencia) e desenvolvimento de software comum: reuse,
nao duplique.

| Situacao | Skill | Apoio |
|---|---|---|
| Criar ou refatorar agente | agent-builder | templates/agent-design, agent-tool-designer, agent-eval-planner |
| Corrigir comportamento (encaminha demais, inventa, nao chama tool) | agent-prompt-refiner | agent-eval-planner, agent-builder |
| Desenhar tool de agente | agent-tool-designer | templates/agent-tool-design, tool-contract-auditor |
| Auditar contrato de tool | tool-contract-auditor | templates/tool-contract-report, api-contract-auditor |
| Validar tool em runtime | tool-runtime-validator | templates/tool-runtime-validation, runtime-qa-audit |
| Protecao para risco nomeado (crise, pagamento, efeito irreversivel) | agent-guardrails-implementer | templates/agent-guardrails-plan, agent-security-auditor |
| Medir mudanca / regressao pareada | agent-eval-planner | templates/agent-eval-plan, test-confidence-mapper |
| Ciclo com conversas de producao (Eval Flywheel) | agent-eval-flywheel | templates/agent-eval-flywheel-report, agent-eval-planner, skill-evolution-loop |
| Trocar modelo/provider | model-flexibility-auditor | templates/model-flexibility-report, agent-eval-planner |
| Custo, latencia, tokens | agent-optimization-auditor | templates/agent-optimization-report, model-routing |
| Logs/traces/custo por turno | agent-observability-auditor | templates/agent-observability-report, persistent-debug-session |
| Seguranca de agente (injection, exfiltracao, tool insegura) | agent-security-auditor | templates/agent-security-report, templates/prompt-injection-eval |
| Hardcode de comportamento, modelo, provider | agent-anti-hardcode-auditor | templates/agent-hardcode-report, config-surface-auditor |
| QA do agente rodando | agent-runtime-qa | templates/agent-runtime-qa-report, tool-runtime-validator |
| Revisar diff de agente | agent-code-reviewer | templates/agent-code-review-report, diff-reviewer |
| Documentar agente | agent-doc-writer | templates/agent-doc, docs-sync-auditor |
| Voz/visao em tempo real | agent-realtime-multimodal | templates/multimodal-streaming-design, architecture-decision |
| Deploy de agente em nuvem (Cloud Run/GCP) | agent-cloud-deployer | templates/agent-cloud-deploy-spec, infra-security-auditor |
