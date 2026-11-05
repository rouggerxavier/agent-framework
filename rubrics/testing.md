# Testing Rubric

Use em toda alteracao de software para escolher cobertura proporcional ao risco
e avaliar os testes criados ou afetados. Nao exige auditar a suite inteira.

## Decidir antes de escrever

Inspecione os testes relacionados e responda: qual comportamento precisa ser
protegido, qual defeito plausivel o teste detectaria e por que a cobertura atual
nao basta?

| Situacao observada | Decisao |
| --- | --- |
| Testes existentes detectam a regressao relevante | Reaproveitar e executar; nao duplicar |
| Caso existente cobre o fluxo, mas falta uma condicao relevante | Ampliar o caso ou parametrizar conforme o padrao local |
| Comportamento novo/alterado sem protecao suficiente | Criar o menor teste que detecte a falha |
| Bug ja reproduzido por teste existente | Usar esse teste como regressao |
| Refatoracao preserva comportamento ja coberto | Executar cobertura existente; caracterizar apenas lacunas relevantes |
| Texto, docs ou ajuste visual sem comportamento alterado | Pode dispensar teste novo; verificar texto, renderizacao ou diff conforme a mudanca |
| Ambiente ou dependencia necessaria indisponivel | Declarar lacuna e verificacao possivel; nao afirmar cobertura validada |

Nenhum teste novo e uma decisao com motivo, nao uma dispensa automatica de
verificacao. Preserve gates e waivers exigidos pelo modo/contrato. Nao crie
testes para atingir quantidade ou percentual de cobertura; metricas ajudam a
localizar lacunas, mas nao demonstram utilidade sozinhas.

## Risco
- Baixo: copy, docs, estilo sem comportamento.
- Medio: fluxo local, componente isolado, parser simples, validacao.
- Alto: auth, billing, dados persistidos, API publica, migrations, permissao, checkout.

## Tipos
- Unit: regra pura, parser, validacao, formatacao, edge case isolado.
- Integration: contrato entre modulos, banco, API interna, estado compartilhado.
- E2E: fluxo critico de usuario ou integracao de varias camadas.
- Manual QA: estados visuais, acessibilidade, copy e device real.

Escolha o menor nivel que observa o risco completo. Muitos unitarios com
dependencias simuladas nao substituem uma integracao necessaria; um E2E pesado
nao agrega quando o defeito ja e detectado em um nivel menor.

## Backend: testar a fronteira relevante

| Comportamento/risco | Evidencia util |
| --- | --- |
| Regra pura, parser ou validacao | Entrada e resultado esperado, incluindo limite ou rejeicao relevante |
| Persistencia, query ou transacao | Estado gravado/lido e atomicidade com banco de teste compativel quando o risco depende dele |
| API, permissao ou isolamento | Resposta/contrato e efeitos, incluindo rejeicao sem escrita ou acesso indevido |
| Job, webhook ou retry | Efeito final; duplicidade, idempotencia ou falha parcial quando fazem parte do comportamento |
| Integracao externa | Contrato na fronteira e tratamento de falha; simulacao controlada sem chamadas reais desnecessarias |

Simule dependencias para controlar custo, tempo ou falhas externas. Nao simule
justamente a query, permissao, transacao ou regra cuja correcao esta em teste.
Verificar uma chamada e suficiente apenas quando essa interacao e o contrato
relevante; nao substitui verificar o efeito pedido.

## Frontend

- Teste interacao e resultado perceptivel: submit, navegacao, validacao e estados
  loading/empty/error quando afetados e relevantes.
- Prefira seletores semanticos e o comportamento do usuario a detalhes internos
  do componente, nomes de classes ou formato do estado.
- Ajuste visual pode usar inspecao/renderizacao ou regressao visual existente;
  nao crie teste de classe CSS apenas porque houve um diff.

## Provar utilidade

- Bug: busque RED pelo defeito antes do fix e GREEN depois. Erro de import,
  setup ou rede nao prova a reproducao do bug.
- Feature: derive a expectativa do requisito/contrato, independentemente do
  calculo da implementacao. Pergunte se uma resposta incorreta, efeito ausente
  ou entrada rejeitada indevidamente reprovaria o teste.
- Se a assercao aceitaria o defeito relevante, corrija ou substitua o teste no
  escopo da tarefa. Nao exija mutacao artificial do codigo em todo teste.
- Use dados deterministas e isolamento para estado, relogio e rede quando
  afetarem o resultado. Reaproveite fixtures sem esconder a condicao testada.
- Rode os comandos e registre o resultado observado. Teste escrito mas nao
  executado e cobertura proposta, nao validada.

## Checklist
- O teste cobre requisito ou bug principal.
- Cada teste novo ou ampliado detecta falha plausivel que faltava cobrir.
- Ha caso de erro ou edge case relevante.
- Mudancas em contrato tem teste de compatibilidade.
- UI cobre loading, empty e error state quando aplicavel.
- Comandos de teste sao registrados.
- Lacunas sao declaradas.

## Red flags
- Apenas happy path em fluxo critico.
- Snapshot substituindo assercao relevante.
- Teste que replica implementacao.
- Assercao tautologica, sem resultado relevante ou apenas sobre o proprio mock.
- Expectativa calculada pelo mesmo codigo que esta sendo testado.
- Duplicacao de cobertura sem novo risco ou condicao relevante.
- Teste de detalhe interno que quebra em refatoracao sem mudanca de comportamento.
- Teste instavel por tempo, rede ou dados.
