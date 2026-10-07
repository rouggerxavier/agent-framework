---
name: agent-cloud-deployer
description: Use para planejar, configurar e validar o deploy seguro de agentes de IA em nuvem (Cloud Run/GCP), incluindo VPC isolada, segredos, SSE/streaming de longa duração e observabilidade via queries LQL e PromQL.
---

# Agent Cloud Deployer

## Objetivo
Projetar, configurar e validar a implantação segura e resiliente de agentes de IA em infraestruturas em nuvem (como Google Cloud Run e serviços gerenciados), garantindo isolamento de rede (VPC privada), injeção segura de segredos, ajuste de timeouts para streaming SSE/WebSockets e observabilidade operacional com consultas estruturadas de Cloud Logging (LQL) e Cloud Monitoring (PromQL).

## Quando usar
- Ao preparar agentes ou serviços de orquestração para release em produção em ambientes Cloud (Cloud Run, GKE ou VMs).
- Para configurar tempos limite de requisição (*request timeout*) e concorrência para streaming de respostas (Server-Sent Events / SSE) de LLMs.
- Ao definir conexões seguras com bancos de dados (ex: Cloud SQL, AlloyDB, Redis) via VPC Connector ou Direct VPC egress sem expor IPs públicos.
- Ao gerenciar chaves de provedores de IA (Gemini, Anthropic, OpenAI) através de Secret Manager e IAM Workload Identity Federation.
- Para gerar consultas de depuração rápida em Cloud Logging (LQL) e painéis de métricas/alertas de SLO em Cloud Monitoring (PromQL).

## Quando nao usar
- Para criar migrations de banco de dados locais (use `data-migration-auditor`).
- Para deploy em bare-metal sem nuvem gerenciada.
- Para empacotar apenas código e tags de versão de backend simples (use `backend-release-packager`).

## Entradas esperadas
- Especificação do serviço do agente (porta, variáveis de ambiente, dependências de banco e APIs externas).
- Plataforma de destino (ex: Google Cloud Run, Cloud Functions v2, GKE).
- Requisitos de concorrência e streaming (ex: até 80 conexões simultâneas por instância, timeout de 300s para respostas longas de IA).
- Nível de segurança e segredos necessários (chaves de API de modelos, tokens de canal WhatsApp/Meta, strings de conexão).

## Workflow
1. **Dimensionamento de recursos e configuração de streaming:**
   - Definir CPU e memória com base no runtime (ex: 1-2 vCPUs, 1-2GB RAM para orchestrators Python/Node.js).
   - Ajustar `--timeout` para chamadas longas de LLM e streams SSE (padrão recomendado: 300 segundos a 600 segundos).
   - Configurar `--concurrency` (evitar saturação em instâncias que sustentam conexões SSE abertas).
   - Habilitar HTTP/2 se necessário para multiplexação de conexões e SSE.

2. **Segurança de credenciais e rede:**
   - Injetar segredos via Secret Manager como variáveis de ambiente no container, sem comitar valores no repositório.
   - Configurar Service Account com princípio de menor privilégio (permissão restrita a Vertex AI, Secret Manager e Datastore/SQL).
   - Configurar Direct VPC Egress para comunicação interna com bancos de dados sem tráfego pela internet pública.

3. **Configuração de observabilidade e métricas:**
   - Estruturar logs em JSON formatados para Cloud Logging com campos padrão: `severity`, `message`, `session_id`, `trace`, `component`.
   - Gerar consultas prontas de LQL (Logging Query Language) para filtros críticos:
     - Erros de chamada a modelos e rate limits (`429 Too Many Requests`).
     - Desconexões prematuras de streaming SSE.
     - Latência acima de thresholds de SLO (> 5 segundos no primeiro token).
   - Definir consultas PromQL para contagem de turnos, taxas de erro e consumo de memória.

4. **Health checks e políticas de escalonamento:**
   - Definir probes de liveness e readiness (ex: `/health` ou `/status` verificando dependências mínimas sem onerar APIs de modelos).
   - Estabelecer `min-instances` (para evitar cold start em atendimentos críticos como WhatsApp) e `max-instances` (para contenção de custos de infraestrutura).

5. **Consolidar especificação de deploy:**
   - Preencher `templates/agent-cloud-deploy-spec.md`.
   - Validar com `infra-security-auditor` antes de aplicar em ambiente de produção.

## Saida obrigatoria
- Especificação de deploy preenchida contendo:
  - Comando de deploy ou manifest IaC (Terraform / Cloud Run YAML).
  - Mapeamento de variáveis de ambiente e referências do Secret Manager.
  - Parâmetros de concorrência, timeouts e instâncias (min/max).
  - Conjunto de consultas de diagnóstico em LQL e PromQL para monitoramento do serviço.

## Criterios de aceite
- Nenhum segredo ou token está em texto plano na configuração.
- O timeout de requisição é compatível com o tempo de geração de texto/áudio do modelo.
- O endpoint de healthcheck não consome tokens do provedor LLM a cada probe.
- Logs e consultas de observabilidade permitem rastrear turnos por `session_id` sem vazar PII.

## Arquivos de apoio
- Template: `templates/agent-cloud-deploy-spec.md`
- Rubrics: `rubrics/infra-security.md`, `rubrics/performance-budget.md`

## Exemplos de uso
- "Prepare a especificação de deploy no Cloud Run para o agente GranKasa com suporte a streaming SSE e secrets do Gemini."
- "Gere as queries LQL e métricas PromQL para monitorar erros 429 de LLM e quedas de conexão no nosso container de agente."
- "Audite se a configuração de concorrência e timeout do Cloud Run vai quebrar as respostas longas do agente."
