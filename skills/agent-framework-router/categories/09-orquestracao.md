---
{
  "category": "orquestracao",
  "keywords": [
    "varios agentes",
    "multi-?agente",
    "maestri",
    "worktree",
    "retom",
    "estado persistente",
    "handoff",
    "contexto cheio",
    "orquestr",
    "qual modelo"
  ],
  "required": []
}
---

# Orquestracao, estado e contexto

Instrucao: estado persistente so em retomada ou `critical`; a existencia de `.agent/`
nao obriga o kernel.

| Situacao | Skill | Apoio |
|---|---|---|
| Inicializar ou retomar estado persistente | framework-next | kernel/protocol, templates/project-state |
| Plano curto em `standard` ou fase persistente em `critical` | workflow-planner | execution-plan-builder, plan-quality-checker |
| Executar plano persistente | workflow-runner | task-runner, kernel/state-machine |
| Executar contrato de tarefa | task-runner | kernel/test-policy, templates/task-result |
| Escolher peso da tarefa | task-mode-router | workflow-orchestrator, test-strategy-builder |
| Orquestrar equipe multiagente/Maestri | team-orchestrator | workflows/multi-agent-development.md, decision-authority-router, templates/agent-dispatch |
| Preparar sessao limpa para nova task | fresh-task-session | kernel/context-budget-policy, templates/agent-dispatch |
| Gerir writers paralelos em worktrees | worktree-lane-manager | kernel/orchestration-policy, templates/orchestration-state |
| Manter notas/perguntas/progresso do projeto | project-notebook | templates/project-notes, workflows/decision-pause-and-continue |
| Classificar decisao descoberta na execucao | decision-authority-router | workflows/decision-pause-and-continue |
| Handoff entre agentes | handoff-builder | workflows/agent-handoff, templates/handoff-summary |
| Conversa longa / contexto cheio | context-compressor | workflows/long-conversation-handoff |
| Escolher Codex/Claude/ChatGPT/modelo para a tarefa | model-routing | — |
