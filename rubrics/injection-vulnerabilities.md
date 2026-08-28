# Injection Vulnerabilities Rubric

Use para revisar codigo onde dado nao confiavel alcanca um sink perigoso.

Dado nao confiavel: request body/query/header/cookie, upload, webhook, fila,
scraping, arquivo importado, saida de LLM, tool output e dado vindo de outro
servico.

## Sinks por classe

| Classe | Sink tipico | Sinal de risco |
| --- | --- | --- |
| SQL injection | query, raw, execute, cursor, `$queryRaw`, ORM `where` textual | concatenacao ou interpolacao de string na query |
| XSS | template, `innerHTML`, `dangerouslySetInnerHTML`, `v-html`, `\|safe`, `mark_safe` | render de input sem escape ou sanitizacao |
| Command injection | `exec`, `system`, `popen`, `child_process`, `subprocess(shell=True)`, `eval` | argumento montado com string do usuario |
| XXE | parser XML, SAX, DOM, XSLT, SOAP, SVG, DOCX/XLSX | parser sem desabilitar DTD e entidades externas |
| Deserializacao insegura | `pickle`, `yaml.load`, `Marshal`, `ObjectInputStream`, `unserialize` | objeto serializado vindo do usuario ou de storage compartilhado |
| SSRF | http client, fetch, webhook, importar por URL, preview de link | URL de destino derivada de input |
| Open redirect | `redirect`, `Location`, `returnTo`, `next`, `callbackUrl` | destino vindo de parametro sem allowlist |
| Mass assignment | `Model(**body)`, `update(body)`, `Object.assign`, `save(req.body)` | bind direto de payload sem whitelist |
| Path traversal | `open`, `readFile`, `sendFile`, `join(base, input)` | caminho concatenado com nome vindo do usuario |
| Template/expression injection | template engine, expression language, formatter | template compilado a partir de input |

## Checklist
- Query usa parametro ligado, nunca concatenacao; identificadores dinamicos usam allowlist.
- Output e escapado no contexto certo (HTML, atributo, URL, JS, CSS); sanitizacao usa lib mantida, nao regex propria.
- Comando externo roda sem shell, com argumentos em lista e binario fixo.
- Parser XML/YAML desabilita DTD, entidades externas e tags de construcao de objeto.
- Deserializacao aceita apenas formato de dados (JSON) ou tipo explicitamente permitido.
- Requisicao com URL do usuario valida esquema, resolve DNS e bloqueia IP privado, loopback, link-local e metadata (`169.254.169.254`), inclusive apos redirect.
- Redirect valida destino contra allowlist ou aceita apenas caminho relativo.
- Bind de payload usa whitelist de campos; campos como `role`, `is_admin`, `owner_id` e `price` nunca vem do request.
- Caminho de arquivo e normalizado e confinado a um diretorio base.
- Validacao acontece no servidor, nao apenas no cliente.
- Existe teste negativo com payload de ataque para cada sink corrigido.

## Severidade
- Critical: execucao remota de codigo, leitura arbitraria de dados ou SSRF que alcanca metadata/rede interna.
- High: injecao explorabel limitada a um tenant, XSS armazenado ou mass assignment sobre campo de privilegio.
- Medium: XSS refletido com pre-condicao, open redirect ou path traversal contido.
- Low: hardening defensivo sem caminho de ataque demonstravel.

## Evidencia minima por achado
- Origem do dado, caminho ate o sink e arquivo:linha.
- Payload ou passo que demonstra o abuso.
- Correcao concreta e teste negativo que falha antes e passa depois.
