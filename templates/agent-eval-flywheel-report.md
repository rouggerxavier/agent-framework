# Agent Eval Flywheel Report

## Informações do Ciclo
- **Nome do Agente:**
- **Versão / Commit Base:**
- **Data do Ciclo:**
- **Origem dos Dados de Produção:** (ex: traces anonimizados do WhatsApp, tickets com fallback)
- **Tamanho Total do Dataset de Avaliação:**

---

## 1. Mapeamento e Clusterização de Falhas
| Cluster ID | Categoria da Falha | Severidade (P0/P1/P2) | Ocorrências no Traces | Causa Primária |
| :--- | :--- | :--- | :--- | :--- |
| CL-01 | Alucinação / Invenção factual | P0 | | Falta de grounding na base de dados |
| CL-02 | Fuga de escopo / Papel indevido | P1 | | Guardrail permissivo |
| CL-03 | Tom inadequado / Resposta longa | P2 | | Instrução de persona vaga |

---

## 2. Novos Casos de Teste Adicionados (Curados & Sintéticos)
- **Casos extraídos de produção:**
- **Casos sintéticos adversariais gerados:**
- **Rubricas de Julgamento Aplicadas:** (ex: `correctness`, `faithfulness`, `scope_adherence`)

---

## 3. Resultados Comparativos (Pré vs Pós-Intervenção)
| Métrica / Rubrica | Baseline (Antes) | Após Mudança | Variação (Δ) | Status |
| :--- | :--- | :--- | :--- | :--- |
| Taxa Global de Aprovação (%) | | | | |
| Conformidade P0 (Regras Críticas) | | | | |
| Aderência ao Escopo Comercial | | | | |
| Taxa de Regressão em Casos Antigos | 0% | 0% | 0% | [ ] APROVADO |

---

## 4. Mudanças Implementadas
- **Alterações em Prompts:**
- **Novos Guardrails / Validadores de Código:**
- **Ajustes de Next Action Policy:**

---

## 5. Próximas Ações
- [ ] Incorporar golden dataset ao runner de CI/CD.
- [ ] Monitorar traces em produção nas próximas 48h para avaliar novos clusters.
