# Agent Workflow

Use para criar, corrigir e entregar agentes. Regra de arquitetura:
`rubrics/agent-design.md` (comece minimo; camada nova so por falha medida).

O modo vem do `agent-framework-router`. Agente novo ou ajuste de comportamento e
`standard`. `critical` so quando o agente move dinheiro, executa efeito
irreversivel ou o dano grave foi nomeado.

## Standard: criar agente
1. `agent-builder`: design minimo em `templates/agent-design.md`, reaproveitando a
   infra do projeto.
2. `agent-tool-designer`: tools de leitura e de efeito.
3. `agent-prompt-refiner`: prompt curto e descricoes de tool.
4. Implementar com testes offline do contrato (laco, erro de tool, efeitos no
   commit, isolamento).
5. `agent-eval-planner`: cenarios de conversa e medicao contra a referencia (ou
   contra o agente antigo, se houver).
6. `agent-code-reviewer`: review integrada, incluindo excesso de infra.

## Standard: corrigir comportamento (falha em conversa ou eval)
1. Reproduza: a conversa, o turno e o que o modelo recebeu e chamou.
2. Escreva o caso que falha.
3. Aplique o menor degrau da escada de correcao (`rubrics/agent-design.md`):
   descricao de tool, prompt, dado pronto, contrato tipado, verificacao estreita,
   codigo. Uma mudanca por candidata.
4. Rode a regressao pareada so nos cenarios afetados mais uma amostra de controle.
5. Decida por eixo; `INCONCLUSIVE` nao promove. Promocao e do dono.

## Standard: trocar modelo
1. `model-flexibility-auditor` so se a troca exigir mudar config ou adapter.
2. Ajuste pelo tier do modelo novo (tabela da rubric).
3. Regressao pareada completa. Remova protecoes que o modelo novo nao precisa.

## Critical (acrescenta ao standard)
- `framework-next` e `workflows/high-risk-change.md` para estado persistente.
- `agent-guardrails-implementer` para cada dano grave nomeado.
- `agent-security-auditor` quando houver fonte nao confiavel com tool de efeito.
- `agent-runtime-qa` no ambiente real antes do release.
- Duas reviews independentes (`spec-compliance-reviewer`, `code-quality-reviewer`).

## Sob demanda (nao sao etapas)
- Custo ou latencia alto medido: `agent-optimization-auditor`.
- Falta de evidencia para debugar: `agent-observability-auditor`.
- Producao com conversas reais: `agent-eval-flywheel`.
- Deploy em nuvem: `agent-cloud-deployer`.
- Voz ou visao em tempo real: `agent-realtime-multimodal`.
- Doc para operacao: `agent-doc-writer`.

## Saidas
- Design minimo e lista do que nao existe de proposito.
- Casos de teste e resultado da medicao.
- Achados de review e correcoes.
