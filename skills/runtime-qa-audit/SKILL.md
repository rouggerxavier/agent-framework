---
name: runtime-qa-audit
description: Use para testar app em execucao, validar fluxos reais, reproduzir bugs, coletar evidencias e gerar achados de QA runtime.
---

# Runtime QA Audit

## Objetivo
Validar comportamento real do software em execucao, cobrindo fluxos criticos, erros, estados de UI, logs e regressao basica.

## Quando usar
- Quando ha URL, dev server ou build executavel.
- Antes de release ou merge de fluxo critico.
- Para confirmar se bug foi corrigido no runtime.

## Quando nao usar
- Para revisar somente codigo sem app executavel.
- Para substituir testes automatizados.
- Para auditoria visual pura; use `ui-ux-pro-max-audit`.

## Entradas esperadas
- Como iniciar o app ou URL.
- Fluxos criticos e usuarios-alvo.
- Credenciais de teste e dados permitidos, se necessario.

## Workflow
1. Confirme ambiente, versao e comandos usados.
2. Execute smoke test dos fluxos principais.
3. Teste erro, loading, empty state e entrada invalida.
4. Registre evidencias, logs e passos de reproducao.
5. Classifique bloqueadores antes de melhorias.

## Saida obrigatoria
- Ambiente testado.
- Cenarios executados.
- Resultado pass/fail por cenario.
- Bugs com severidade, passos, esperado, obtido e evidencia.
- Riscos residuais e lacunas.

## Criterios de aceite
- Nao declarar aprovado sem dizer o que foi testado.
- Bugs devem ser reproduziveis ou marcados como intermitentes.
- Logs relevantes devem ser resumidos.
- Separe falha funcional de ajuste visual.

## Exemplos de uso
- Codex: `$runtime-qa-audit Rode QA no fluxo de signup local.`
- Claude Code: `/runtime-qa-audit Valide esta build antes do deploy.`
