---
{
  "category": "seguranca",
  "keywords": [
    "vulnerab",
    "seguranca",
    "auth",
    "segredo",
    "dados pessoais",
    "pen ?test",
    "xss\\b",
    "sqli\\b",
    "injection",
    "csrf\\b",
    "jwt\\b",
    "lgpd\\b"
  ],
  "required": []
}
---

# Seguranca

Instrucao: tocar area sensivel impede `fast`, mas nao escala para `critical`
sozinho. Escolha o auditor especifico; `security-audit` so para varredura completa.
Agente: `agent-security-auditor` (bloco 1).

| Situacao | Skill | Apoio |
|---|---|---|
| Seguranca/privacidade e dados pessoais | security-privacy-audit | rubrics/security-privacy, workflows/security-review, docs/security-coverage |
| Auditoria de seguranca completa / pen test do codigo | security-audit | security-privacy-audit, workflows/security-review |
| SQLi, XSS, RCE, XXE, SSRF, deserializacao, redirect, mass assignment | injection-vulnerability-auditor | rubrics/injection-vulnerabilities, templates/security-audit-report |
| Auth, JWT, sessao, CSRF, IDOR, papel admin, bypass de fluxo | authn-authz-auditor | rubrics/access-control, templates/security-audit-report |
| Segredo hardcoded, chave, hash fraco, TLS sem verificacao | crypto-secrets-auditor | rubrics/crypto-secrets, env-gitignore-auditor |
| Debug em producao, CORS, portas, Docker root, IaC, pipeline | infra-security-auditor | rubrics/infra-security, dependency-risk-auditor |
