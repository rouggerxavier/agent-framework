# Crypto and Secrets Rubric

Use para revisar segredos no codigo e escolhas de criptografia, hash e
aleatoriedade.

## Segredos

| Classe | Onde procurar | Sinal de risco |
| --- | --- | --- |
| Segredo hardcoded | codigo, teste, fixture, script, notebook, IaC, CI, docs | chave, senha, token ou certificado literal |
| Segredo em bundle | frontend, mobile, app config, variavel `PUBLIC_`/`NEXT_PUBLIC_` | credencial servida ao cliente |
| Segredo em log | log, trace, mensagem de erro, telemetria, report de crash | header `Authorization`, body de auth, token em URL |
| Segredo versionado | historico do git, backup, dump, `.env` commitado | segredo presente em commit anterior |
| Chave sem rotacao | provider, KMS, CI | chave sem dono, sem expiracao e sem procedimento de rotacao |

## Criptografia

| Uso | Aceitavel | Rejeitar |
| --- | --- | --- |
| Hash de senha | argon2id, scrypt, bcrypt com custo atual | MD5, SHA1, SHA256 puro, hash sem salt, salt fixo |
| Integridade / assinatura | SHA-256+, HMAC-SHA256, Ed25519, RSA-PSS 2048+ | MD5, SHA1, RSA com chave curta |
| Cifra simetrica | AES-GCM, ChaCha20-Poly1305 | DES, 3DES, RC4, AES-ECB, AES-CBC sem MAC |
| Aleatoriedade | CSPRNG (`secrets`, `crypto.randomBytes`, `SecureRandom`) | `random`, `Math.random`, timestamp, contador |
| Transporte | TLS atual com verificacao de certificado | TLS desabilitado, `verify=False`, `rejectUnauthorized: false`, HTTP em rota autenticada |
| Comparacao de segredo | comparacao em tempo constante | `==` em token, HMAC ou senha |

## Checklist
- Nenhum segredo literal em codigo, teste, IaC ou pipeline; todos vem de env/secret manager.
- `.env.example` lista as chaves sem valores reais e `.env` esta ignorado.
- Segredo detectado no historico e tratado como vazado: rotacionar primeiro, remover depois.
- Logs e erros redigem credenciais, tokens, cookies e PII; token nunca viaja em query string.
- Hash de senha usa algoritmo de derivacao lenta com salt por usuario e parametros de custo configuraveis.
- Cifra usa modo autenticado, IV/nonce unico por operacao e chave vinda de config.
- Verificacao de certificado nunca e desligada, nem em cliente interno.
- Chaves tem dono, escopo minimo e procedimento de rotacao documentado.

## Severidade
- Critical: segredo valido em producao exposto, chave privada versionada ou cifra/assinatura quebravel em uso real.
- High: senha com hash fraco, TLS sem verificacao, aleatoriedade previsivel em token de seguranca.
- Medium: segredo em log, comparacao nao constante, chave sem rotacao.
- Low: algoritmo legado em uso nao sensivel, com plano de troca.

## Evidencia minima por achado
- Arquivo:linha e tipo do segredo ou primitiva.
- Se o segredo e valido, onde vale e desde quando esta exposto.
- Acao: rotacionar, remover, migrar algoritmo, e verificacao correspondente.
