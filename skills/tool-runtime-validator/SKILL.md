---
name: tool-runtime-validator
description: Use para validar tools de agente em execucao com casos reais, input invalido, falha externa, timeout, retry, logs e evidencias.
---

# Tool Runtime Validator

## Objetivo
Confirmar que uma tool funciona no runtime real, incluindo caminho feliz, entradas ruins, falhas externas, timeout, retry e logs seguros.

## Quando usar
- Depois de implementar ou alterar tool usada por agente.
- Antes de liberar tool com side effects, integracao externa, auth, dados sensiveis ou custo.
- Quando contrato parece correto, mas comportamento runtime ainda nao foi provado.
- Para reproduzir falhas intermitentes de tool, timeout ou provider.

## Quando nao usar
- Para auditoria somente estatica; use `tool-contract-auditor`.
- Para QA amplo do app/agente; use `runtime-qa-audit`.
- Quando nao ha ambiente executavel; gere plano de validacao e marque bloqueio.

## Entradas esperadas
- Como executar a tool ou o agente que chama a tool.
- Casos de teste permitidos, dados seguros e credenciais de teste.
- Contrato esperado, side effects e limites de ambiente.
- Logs, traces ou comandos relevantes.

## Workflow
1. Confirme ambiente, versao, config e dados de teste seguros.
2. Execute caso feliz com input minimo e input representativo.
3. Execute casos negativos: input invalido, falta de permissao, missing env, recurso ausente e unsafe request.
4. Simule ou force falhas: timeout, provider/API failure, rate limit, retry e partial success.
5. Verifique side effects, rollback/idempotencia, logs sem secrets e output consumivel pelo agente.
6. Registre evidencias, comandos, resultados, bugs e riscos residuais.

## Saida obrigatoria
Preencha `../../templates/tool-runtime-validation.md` com ambiente, cenarios, pass/fail, evidencias, bugs e riscos.

## Criterios de aceite
- Nao declarar aprovado sem listar cenarios executados.
- Side effects devem ser verificados ou explicitamente marcados como nao testados.
- Logs nao devem expor secrets, tokens, dados sensiveis ou payloads desnecessarios.
- Falhas devem retornar erro util para o agente decidir retry, fallback, pergunta ou stop.

## Arquivos de apoio
- Template: ../../templates/tool-runtime-validation.md
- Runtime QA: ../../skills/runtime-qa-audit/SKILL.md
- Testes: ../../skills/test-confidence-mapper/SKILL.md
- Seguranca: ../../skills/security-privacy-audit/SKILL.md

## Exemplos de uso
- Codex: `$tool-runtime-validator Valide esta tool localmente com input ruim e timeout.`
- Claude Code: `/tool-runtime-validator Execute casos reais e registre evidencias da tool.`
