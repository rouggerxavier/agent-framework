# CRM to Ad Platform Sync Plan

## Informações Gerais
- **Sistema de Origem (CRM/DB):**
- **Plataforma de Destino (Ads):** (ex: Google Ads Customer Match / Data Manager API)
- **Tipo de Sincronização:** [ ] Customer Match (Público) | [ ] Lista de Exclusão | [ ] Conversão Offline (OCT)
- **Frequência:** [ ] Tempo Real / Webhook | [ ] Batch Diário | [ ] Batch Semanal

---

## 1. Mapeamento de Dados e Regras de Hashing
| Campo no CRM | Destino na API | Regra de Normalização | Hash Aplicado |
| :--- | :--- | :--- | :--- |
| Email | hashed_email | Trim, Lowercase | SHA-256 |
| Telefone | hashed_phone_number | E.164 (+55DDDNUMERO) | SHA-256 |
| Primeiro Nome | hashed_first_name | Trim, Lowercase | SHA-256 |
| Sobrenome | hashed_last_name | Trim, Lowercase | SHA-256 |
| Identificador de Clique | gclid / wbraid / gbraid | Raw string (sem hash) | Não aplicável |

---

## 2. Conformidade e Consentimento (LGPD / Consent Mode)
- **Status do Consentimento de Usuário no CRM:**
- **Mapeamento de Consent Mode:**
  - `ad_user_data`: GRANTED / DENIED
  - `ad_personalization`: GRANTED / DENIED
- **Política de Retenção e Descarte de Logs:**

---

## 3. Arquitetura do Pipeline
```text
[CRM Database/Webhook]
         ↓
[Worker de Higienização e Hashing SHA-256]
         ↓
[Verificação de Consentimento e Filtro]
         ↓
[Google Ads Data Manager / API Ingestion]
```

- **Ponto de Idempotência / Deduplicação:**
- **Tratamento de Rate Limits e Erros de Batch:**

---

## 4. Monitoramento e Alertas
- **Métricas de Sucesso:**
- **Alarme de Falha de Ingestão:**
- **Auditoria de Conformidade:**
