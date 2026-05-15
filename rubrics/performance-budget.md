# Performance Budget Rubric

Use para revisar impacto de performance em frontend, backend e dados.

## Areas
- Bundle size, carregamento e renderizacao.
- Queries, indices e round trips.
- Cache, batching, pagination e streaming.
- Latencia de API e timeout.
- Memoria, CPU e tarefas em background.
- Percepcao de velocidade: skeleton, loading e feedback.

## Checklist
- Ha budget ou baseline conhecido.
- Mudanca nao aumenta trabalho em caminho critico sem justificativa.
- Queries novas tem filtros, limites e indices adequados.
- UI evita re-render ou assets pesados desnecessarios.
- Operacoes lentas tem feedback e timeout.
- Medicao ou verificacao foi registrada.

## Saida recomendada
- Risco de performance.
- Evidencia ou estimativa.
- Mitigacao.
- Medicao recomendada.
