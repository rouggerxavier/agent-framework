# Data Migration Rubric

Use para revisar migrations de schema e dados, backfill e rollback.

## Areas
- Mudanca de schema: coluna, indice, constraint, tipo, default.
- Dados: backfill, transformacao, dedupe, volume e tempo.
- Compatibilidade: codigo antigo e novo durante o deploy.
- Reversibilidade: down migration ou plano de rollback real.

## Checklist
- Estrategia expand/contract quando a mudanca e destrutiva.
- Migration e codigo entram em ordem segura (sem janela quebrada).
- Backfill em lote, idempotente e reexecutavel.
- Indice/constraint criados sem lock longo em tabela grande.
- Rollback testado ou risco de irreversibilidade declarado.
- Migration testada em copia com volume realista.
- Comandos e ordem de execucao registrados.

## Red flags
- Drop/rename de coluna no mesmo deploy do codigo que ainda a usa.
- Backfill single-shot sem batch nem retomada.
- Migration sem caminho de rollback e sem aviso.
- Mudanca destrutiva sem backup ou ponto de restauracao.
- Lock de tabela grande em horario de pico.
