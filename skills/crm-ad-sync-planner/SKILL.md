---
name: crm-ad-sync-planner
description: Use para planejar e validar a integração de dados de CRM com plataformas de anúncios, incluindo audiências Customer Match, exclusão de públicos e ingestão de conversões offline de leads com hashing e consentimento.
---

# CRM Ad Sync Planner

## Objetivo
Planejar, desenhar a arquitetura e validar fluxos de integração segura entre sistemas de CRM/bancos de dados de leads e plataformas de anúncios (como Google Ads Data Manager API / Customer Match), garantindo hashing de dados sensíveis (PII), conformidade com LGPD/GDPR e envio de conversões offline para otimização de lances.

## Quando usar
- Ao integrar leads gerados em canais proprietários (WhatsApp, Web, CRM Feirão, GranKasa) para sincronização de públicos com o Google Ads.
- Para planejar o envio de conversões offline (ex: lead que visitou stand, fez proposta ou assinou contrato).
- Ao desenhar fluxos de exclusão de audiência para evitar gastar verba com quem já virou cliente.
- Ao definir a arquitetura de hashing SHA-256 e consentimento (*Google Consent Mode v2*).
- Antes de implementar scripts ou pipelines de dados de sincronização de audiências.

## Quando nao usar
- Para auditar campanhas ou métricas de anúncios ativas (use `ads-performance-auditor`).
- Para disparar mensagens automáticas de WhatsApp ou e-mail marketing (use workflows de aplicação do produto).
- Para desenvolvimento de schema de banco sem relação com ingestão de anúncios.

## Entradas esperadas
- Fonte de dados de CRM (campos disponíveis: e-mail, telefone, endereço, CPF/documento, status do funil).
- Objetivo da sincronização: Customer Match (audiência de remarketing / lookalike), lista de exclusão, ou evento de conversão offline (*lead qualified*, *deal closed*).
- Regras de consentimento do usuário (opt-in coletado, flag de consentimento de marketing).
- Frequência desejada (tempo real via webhook, batch diário, batch semanal).

## Workflow
1. **Mapeamento e higienização de identificadores (PII):**
   - Identificar campos de identificação disponíveis: e-mail, telefone com DDI/DDD, primeiro e último nome.
   - Definir normalização: minúsculas, remoção de espaços e pontos, formatação E.164 para telefones (+55...).
   - Especificar hashing criptográfico: SHA-256 aplicado *antes* do envio para qualquer API de anúncio.

2. **Definição de tipos de audiência e eventos:**
   - **Customer Match:** listas para remarketing ou audiências semelhantes (ex: compradores de alto valor).
   - **Listas de Exclusão:** leads descartados ou compradores recentes para economizar verba.
   - **Offline Conversion Tracking (OCT):** mapear identificadores de clique (`gclid` / `wbraid` / `gbraid`) ou dados avançados de conversão (Enhanced Conversions for Leads) associados ao timestamp da conversão e valor gerado.

3. **Arquitetura do pipeline e isolamento:**
   - Escolher mecanismo de ingestão: Data Manager API, Google Ads API Upload, ou webhook intermediário.
   - Definir retenção de dados e política de descarte: logs não devem conter PII descriptografado.
   - Garantir verificação do `Google Consent Mode` (ad_user_data e ad_personalization).

4. **Tratamento de falhas e idempotência:**
   - Definir tratamento de erros de API (taxa de erro por registro inválido).
   - Mecanismo de reprocessamento seguro e deduplicação de eventos offline.

5. **Consolidar plano de integração:**
   - Preencher `templates/crm-ad-sync-plan.md`.
   - Validar com `security-privacy-audit` para certificar que nenhum dado pessoal vaza em logs ou payloads sem hash.

## Saida obrigatoria
- Plano técnico de sincronização contendo:
  - Dicionário de dados mapeado com regra de normalização e hash.
  - Diagrama de fluxo (CRM → Pipeline de Hashing → Ads API).
  - Políticas de consentimento e LGPD aplicadas.
  - Estratégia de fallback, deduplicação e monitoramento de falhas.

## Criterios de aceite
- Todos os campos de PII são anonimizados com SHA-256 antes da saída da infraestrutura local.
- O plano inclui tratamento explícito para o Consent Mode v2.
- A frequência e volume respeitam os limites de cota da API da plataforma de anúncios.
- Nenhum dado pessoal bruto é armazenado em logs de integração.

## Arquivos de apoio
- Template: `templates/crm-ad-sync-plan.md`
- Rubrics: `rubrics/security-privacy.md`, `rubrics/api-contract.md`

## Exemplos de uso
- "Planeje a sincronização dos leads do GranKasa para uma lista de Customer Match no Google Ads."
- "Como estruturar o envio de conversões offline quando um lead visita o imóvel para o Google Ads otimizar a campanha?"
- "Valide se nosso script de upload de audiência para o Google Ads está em conformidade com LGPD e hashing correto."
