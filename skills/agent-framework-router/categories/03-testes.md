---
{
  "category": "testes",
  "keywords": [
    "teste",
    "cobertura",
    "esta pronto",
    "qa\\b",
    "verific"
  ],
  "required": []
}
---

# Testes e verificacao

Instrucao: aplique `test-strategy-builder` e `rubrics/testing.md`; verifique a
cobertura existente antes de criar testes e justifique lacunas ou nenhum teste
novo. Escolha o menor nivel que detecta a falha relevante, proporcional ao modo.
Agente: use o bloco 1 (`agent-eval-planner`, `agent-runtime-qa`).

| Situacao | Skill | Apoio |
|---|---|---|
| Estrategia de testes | test-strategy-builder | rubrics/testing, templates/test-plan |
| Mapa de confianca de testes | test-confidence-mapper | templates/test-confidence-map, test-strategy-builder |
| Verificar cobertura do objetivo | goal-coverage-verifier | templates/goal-coverage-report, diff-reviewer |
| QA app rodando | runtime-qa-audit | — |
