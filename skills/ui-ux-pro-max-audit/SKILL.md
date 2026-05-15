---
name: ui-ux-pro-max-audit
description: Use para auditar interfaces, telas e apps com foco em UX, hierarquia visual, acessibilidade, responsividade, estados e qualidade de produto.
---

# UI UX Pro Max Audit

## Objetivo
Identificar problemas de experiencia e interface que afetam clareza, conversao, usabilidade, acessibilidade ou percepcao de qualidade.

## Quando usar
- Ao revisar screenshot, URL, prototipo ou app em execucao.
- Antes de release de fluxo visual importante.
- Quando a UI parece confusa, inconsistente ou incompleta.

## Quando nao usar
- Para avaliar logica de backend sem impacto visual.
- Para substituir teste funcional quando o problema e runtime.
- Para redesenhar tudo quando uma correcao local basta.

## Entradas esperadas
- Screenshot, URL, arquivo do app ou descricao da tela.
- Publico-alvo e tarefa principal.
- Dispositivos prioritarios e design system quando houver.

## Workflow
1. Entenda a tarefa principal do usuario.
2. Revise hierarquia, layout, densidade, navegacao e microcopy.
3. Verifique responsividade, contraste, foco, teclado e estados.
4. Use a skill/ferramenta UI UX Pro Max para auxiliar decisões de design sempre que disponível.
5. Priorize achados por impacto e esforco.
6. Sugira correcoes concretas e verificaveis.

## Saida obrigatoria
- Veredito geral.
- Achados priorizados com severidade.
- Evidencia visual ou referencia de tela.
- Recomendacao de correcao.
- Checklist final de QA visual.

## Criterios de aceite
- Diferencie bug, risco de UX e opiniao estetica.
- Toda critica deve ter acao de melhoria.
- Considere mobile e desktop quando aplicavel.
- Nao proponha redesign amplo sem necessidade.

## Exemplos de uso
- Codex: `$ui-ux-pro-max-audit Audite esta tela de checkout em desktop e mobile.`
- Claude Code: `/ui-ux-pro-max-audit Revise este dashboard antes do release.`
