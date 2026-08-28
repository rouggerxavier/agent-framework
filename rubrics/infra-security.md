# Infra and Container Security Rubric

Use para revisar configuracao de runtime, containers, IaC, pipeline e superficie
de rede.

## Areas

| Classe | Onde procurar | Sinal de risco |
| --- | --- | --- |
| Configuracao insegura | settings de app, framework, feature flags | `DEBUG=true`, stack trace exposto, admin/console habilitado, `ALLOWED_HOSTS=*` |
| CORS e headers | middleware, gateway, CDN | `Access-Control-Allow-Origin: *` com credenciais, origem refletida, ausencia de CSP/HSTS |
| Superficie de rede | compose, k8s, terraform, security group | porta de banco/cache/admin publicada, `0.0.0.0/0`, servico interno exposto |
| Container | Dockerfile, imagem base | roda como root, sem `USER`, base `latest` ou sem patch, segredo em `ENV`/`ARG`, `--privileged` |
| IaC e manifests | terraform, k8s, helm, compose, CI | senha em YAML, bucket publico, criptografia desligada, log desativado |
| Pipeline | CI/CD, actions | secret impresso, artefato publico, action sem versao fixada, permissao ampla de token |
| Defaults de deploy | ambientes | credencial padrao mantida, ambiente de teste com dado real |

## Checklist
- Debug, profiler, console interativo e paginas de erro detalhadas ficam desligados fora de desenvolvimento.
- CORS declara origens explicitas; `*` nunca aparece junto de credenciais; `Origin` nao e refletido sem allowlist.
- Headers de seguranca aplicados na borda: CSP, HSTS, `X-Content-Type-Options`, `Referrer-Policy`.
- Somente as portas necessarias sao publicadas; banco, cache, fila e paineis administrativos ficam em rede interna.
- Container roda com usuario nao root, sistema de arquivos somente leitura quando possivel e sem capacidades extras.
- Imagem base e pinada por versao ou digest e tem origem confiavel; build nao deixa segredo em camada.
- IaC nao carrega segredo em texto; storage tem criptografia e acesso privado por padrao; logs de auditoria ligados.
- Pipeline usa token com permissao minima, mascara segredos e fixa versoes de acao/imagem.
- Credenciais padrao sao trocadas; ambiente nao produtivo nao usa dado real sem mascaramento.
- Mudanca de infra tem rollback descrito e e verificavel por comando.

## Severidade
- Critical: servico com dado sensivel exposto a internet, segredo em manifest aplicado ou credencial padrao ativa.
- High: container root com montagem sensivel, CORS permissivo com credenciais, storage publico.
- Medium: debug ligado em ambiente compartilhado, imagem sem pin, header de seguranca ausente.
- Low: hardening recomendado sem exposicao real.

## Evidencia minima por achado
- Arquivo:linha ou recurso e ambiente afetado.
- O que fica acessivel e para quem.
- Correcao concreta e comando/checagem que confirma o fechamento.
