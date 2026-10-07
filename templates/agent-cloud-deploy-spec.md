# Agent Cloud Deploy Specification

## Informações Gerais
- **Nome do Serviço:**
- **Plataforma de Nuvem:** Google Cloud Run
- **Região:** (ex: `southamerica-east1` ou `us-central1`)
- **Container / Imagem:**
- **Porta do Container:** (ex: 8080)

---

## 1. Dimensionamento e Parâmetros de Execução
| Parâmetro | Valor Configurado | Justificativa |
| :--- | :--- | :--- |
| CPU | 1 ou 2 vCPUs | Processamento de requisições assíncronas |
| Memória | 1GiB ou 2GiB | Buffer de sessões e parsing de contexto |
| Request Timeout | 300s (5 min) | Suporte a streaming de texto e turnos de IA |
| Concorrência | 80 | Conexões simultâneas por instância |
| Instâncias Mínimas | 1 | Prevenção de cold start para canais em tempo real |
| Instâncias Máximas | 10 | Proteção contra explosão de custos |
| Egress de Rede | Direct VPC / Private | Comunicação interna com bancos e Redis |

---

## 2. Injeção de Segredos e Variáveis de Ambiente
| Variável | Origem | Descrição |
| :--- | :--- | :--- |
| `GEMINI_API_KEY` | Secret Manager: `projects/.../secrets/gemini-api-key:latest` | Chave de API do provedor LLM |
| `DATABASE_URL` | Secret Manager: `projects/.../secrets/db-conn-string:latest` | Conexão segura com banco de dados |
| `CHANNEL_AUTH_SECRET` | Secret Manager: `projects/.../secrets/channel-secret:latest` | Token de validação de webhooks |
| `APP_ENV` | Literal: `production` | Ambiente de execução |
| `LOG_LEVEL` | Literal: `INFO` | Nível de detalhamento de logs |

---

## 3. Observabilidade e Queries Estruturadas

### Consulta Cloud Logging (LQL) para Erros e Rate Limits (429)
```text
resource.type="cloud_run_revision"
resource.labels.service_name="NOME_DO_SERVICO"
severity>=ERROR OR jsonPayload.status_code=429
```

### Consulta Cloud Logging (LQL) para Rastreio de Turno Específico
```text
resource.type="cloud_run_revision"
resource.labels.service_name="NOME_DO_SERVICO"
jsonPayload.session_id="SESSION_ID_AQUI"
```

### Consulta PromQL (Cloud Monitoring) para Taxa de Erro 5xx
```promql
sum(rate(run_googleapis_com:request_count{response_code_class="5xx", service_name="NOME_DO_SERVICO"}[5m]))
/
sum(rate(run_googleapis_com:request_count{service_name="NOME_DO_SERVICO"}[5m]))
```

---

## 4. Checklist de Pré-Deploy
- [ ] Container roda como usuário não-root.
- [ ] Endpoint `/health` não chama LLM diretamente.
- [ ] Service Account possui apenas permissões mínimas no IAM.
- [ ] Segredos configurados no Secret Manager e liberados para a Service Account.
- [ ] Timeout de streaming alinhado com o cliente frontend/gateway.
