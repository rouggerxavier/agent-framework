---
name: bug-repro-lab
description: Use para investigar bugs com reproducao, hipoteses, evidencia, causa provavel, correcao minima e verificacao de regressao.
---

# Bug Repro Lab

## Objetivo
Transformar um sintoma em bug reproduzivel, causa provavel e correcao minima validada.

## Quando usar
- Para bug report, stack trace, teste falhando ou comportamento inesperado.
- Antes de corrigir area pouco conhecida.
- Quando a reproducao ainda nao esta clara.

## Quando nao usar
- Para feature nova sem comportamento esperado.
- Para ajuste visual simples sem bug reproduzivel.
- Para mudanca ampla sem escopo de bug.

## Entradas esperadas
- Sintoma, erro, teste falhando ou passos conhecidos.
- Ambiente e comandos disponiveis.
- Escopo permitido para investigacao e correcao.

## Workflow
1. Registre esperado, obtido, ambiente e passos conhecidos.
2. Reproduza ou documente por que nao foi possivel reproduzir.
3. Levante hipoteses e valide por codigo, logs ou testes.
4. Aplique ou recomende fix minimo.
5. Execute verificacao focada e registre risco de regressao.

## Saida obrigatoria
- Passos de reproducao ou tentativa.
- Esperado vs obtido.
- Causa provavel com evidencia.
- Mudanca aplicada ou recomendada.
- Verificacao e riscos restantes.

## Criterios de aceite
- Nao corrigir apenas por palpite quando houver caminho de reproducao.
- Bug nao reproduzido deve sair como hipotese.
- Fix deve ser pequeno e alinhado ao sistema.
- Inclua teste de regressao ou justificativa.

## Exemplos de uso
- Codex: `$bug-repro-lab Reproduza e corrija o erro no checkout.`
- Claude Code: `/bug-repro-lab Investigue este stack trace e proponha fix minimo.`
