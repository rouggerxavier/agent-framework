# Security Skills

Camada minima de seguranca para reviews rapidos com Codex/Claude Code.

Use quando uma mudanca tocar entrada externa, auth/authz, secrets, logs, dados, dependencias, agentes, tools ou release.

## Skills
- `skills/threat-model.md`: pense no abuso antes de implementar.
- `skills/secure-review.md`: revise bugs comuns de seguranca.
- `skills/authz-review.md`: revise acesso, roles e isolamento.
- `skills/release-check.md`: cheque antes de PR/release.

## Comando
```bash
make security:check
```

Ou:

```bash
./scripts/security-check
```

O script usa somente ferramentas nativas do repo/sistema. Sem dependencias novas.
