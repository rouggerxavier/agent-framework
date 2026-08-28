# Access Control Rubric

Use para revisar autenticacao, sessao, autorizacao por recurso, autorizacao por
funcao, CSRF e fluxos de negocio que dependem de ordem ou de estado.

## Areas

| Classe | Pergunta central | Sinal de risco |
| --- | --- | --- |
| Autenticacao quebrada | Como o servidor prova quem e o chamador? | token estatico, JWT `alg: none`, segredo fraco, sem `exp`, refresh eterno |
| BOLA / IDOR | O dono do recurso foi verificado? | handler usa `id` da URL e busca sem filtrar por tenant/usuario |
| Autorizacao de funcao | O papel foi verificado neste endpoint? | rota admin protegida so pela UI, checagem em middleware parcial |
| Sessao | O identificador e imprevisivel e rotacionado? | id previsivel, sem rotacao apos login, sem invalidacao no logout |
| CSRF | Mutacao exige prova de intencao? | POST/PUT/DELETE por cookie sem token, sem `SameSite`, CORS com credenciais |
| Logica de negocio | A ordem e os invariantes sao impostos no servidor? | etapa pulavel, preco/quantidade do cliente, cupom reaplicavel, race em saldo |

## Checklist
- Toda decisao de acesso acontece no servidor, por requisicao, e nao depende de campo do cliente.
- Recurso e sempre buscado com o escopo do chamador na consulta (`where id = ? and tenant_id = ?`), nao filtrado depois.
- Endpoints administrativos negam por padrao; a checagem de papel esta no handler ou em policy central, e nao apenas na navegacao.
- Identificador de sessao e gerado por CSPRNG, rotacionado no login e invalidado no logout e na troca de senha.
- Cookie de sessao usa `HttpOnly`, `Secure` e `SameSite` adequado; token tem expiracao curta e revogacao possivel.
- JWT valida assinatura, algoritmo esperado, emissor, audiencia e expiracao; segredo/chave vem de config.
- Mutacoes por cookie exigem token anti-CSRF ou equivalente; CORS com credenciais nunca usa origem `*` nem reflete `Origin`.
- Fluxos com etapas obrigatorias validam estado anterior no servidor (pagamento antes de emissao, verificacao antes de acesso).
- Valores economicos (preco, desconto, saldo, limite) sao recalculados no servidor; operacoes concorrentes usam lock ou transacao.
- Enumeracao e brute force tem limite de tentativa e resposta uniforme.
- Falha de autorizacao gera log auditavel com ator, recurso, acao e resultado.
- Existe teste negativo por classe: outro usuario, outro tenant, papel menor, sem token, token expirado, etapa fora de ordem.

## Severidade
- Critical: bypass de autenticacao, acesso entre tenants, escalada para admin ou fluxo que move dinheiro sem validacao.
- High: IDOR sobre dado sensivel, endpoint admin sem checagem de papel, sessao sem rotacao ou CSRF em mutacao relevante.
- Medium: falta de rate limit, expiracao longa demais ou invariante de negocio validado so no cliente.
- Low: hardening sem caminho de abuso demonstravel.

## Evidencia minima por achado
- Ator atacante, ator vitima e recurso alvo.
- Requisicao concreta que demonstra o acesso indevido.
- Correcao e teste negativo correspondente.
