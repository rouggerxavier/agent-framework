---
name: frontend-refactor-contract-guardian
description: "Use para refatorar paginas frontend a partir de handoff, AI Stitch ou Claude Design preservando rotas, integracoes backend, acoes existentes, branch dedicada e documentacao de lacunas."
---

# Frontend Refactor Contract Guardian

## Objetivo
Guiar refatoracoes visuais de paginas frontend sem quebrar contratos existentes com backend, rotas, estados, permissoes, analytics, formularios ou acoes do usuario. A skill tambem obriga registrar lacunas quando o novo design cria botoes, campos, estados ou fluxos sem suporte backend atual.

## Quando usar
- Ao aplicar handoff, zip, HTML, screenshot, AI Stitch, Claude Design, Figma exportado ou prompt de redesign em uma pagina existente.
- Quando o usuario quer refatorar uma rota especifica, como home, landing page, dashboard, detalhe, checkout, login ou area administrativa.
- Quando o novo layout pode remover funcionalidades atuais ou adicionar controles sem implementacao real.
- Antes de passar uma refatoracao visual para Claude Code, Codex ou outro agente executor.

## Quando nao usar
- Para criar uma pagina totalmente nova sem dependencia de backend existente.
- Para auditar apenas estetica ou UX sem alterar codigo; use `ui-ux-pro-max-audit`.
- Para revisar somente API ou contrato backend; use `api-contract-auditor`.
- Para refatoracao backend sem mudanca visual.

## Entradas esperadas
- Rota exata a refatorar, ou lista curta de rotas candidatas.
- Handoff/design de origem: zip, arquivo, URL, screenshot, AI Stitch, Claude Design ou prompt textual.
- Instrucoes restritivas do usuario: partes que devem ser copiadas, ignoradas, preservadas ou nao tocadas.
- Nivel desejado de refatoracao: do zero, parcial, preservar componentes atuais, ou apenas incorporar elementos especificos.
- Repo, branch atual e convencoes de build/teste.

## Perguntas obrigatorias antes de implementar
Pergunte de forma curta quando a resposta nao estiver clara no pedido ou no repo:

- Qual rota exata sera refatorada?
- A pagina deve ser refeita do zero, parcialmente adaptada ou manter estrutura/componentes atuais?
- Quais partes do handoff/design devem ser usadas e quais devem ser ignoradas?
- Quais partes da pagina atual nao podem ser alteradas?
- O novo design adiciona botoes, filtros, formularios, abas, menus, CTAs ou fluxos que precisam funcionar agora?
- Qual documentacao do projeto deve registrar lacunas e decisoes, quando houver padrao local?

## Gate de worktree e branch
Antes de editar arquivos:

1. Rode `git status --short --branch`.
2. Identifique arquivos modificados, untracked e branch atual.
3. Nunca descarte ou sobrescreva mudancas existentes sem aprovacao explicita.
4. Se houver mudancas locais fora do escopo, preserve-as e evite tocar nesses arquivos.
5. Crie uma branch dedicada antes da refatoracao, salvo se o usuario proibir:
   - nome sugerido: `refactor/<rota>-frontend-handoff`;
   - se o repo tiver padrao melhor, siga o padrao local.
6. Se nao for possivel criar branch por estado do repo, permissao ou conflito, relate o bloqueio antes de implementar.

## Workflow
1. Leia instrucoes locais do repo, especialmente `AGENTS.md`, `CLAUDE.md`, README e docs de frontend quando existirem.
2. Confirme a rota alvo:
   - encontre o arquivo da rota, layout, componentes filhos e entrypoints;
   - identifique se e home, landing page, dashboard ou outra rota especifica.
3. Mapeie a pagina atual:
   - componentes usados;
   - chamadas HTTP, server actions, loaders, hooks, stores e providers;
   - formularios, validacoes, estados de loading/erro/vazio;
   - permissoes, auth, tenant/org/project context;
   - navegacao, query params, path params e side effects.
4. Mapeie o backend diretamente conectado:
   - endpoints, payloads, schemas, DTOs, status codes e erros;
   - modelos ou services consumidos;
   - mocks, fixtures ou dados locais que nao representam producao;
   - variaveis de ambiente ou configs envolvidas.
5. Compare design novo versus pagina atual:
   - funcionalidades que seriam removidas ou escondidas;
   - funcionalidades novas sem backend atual;
   - campos ou filtros sem origem de dados;
   - botoes ou CTAs sem acao implementavel;
   - mudancas de rota, permissao ou contrato.
6. Defina estrategia de refatoracao:
   - adaptar design ao contrato atual quando a funcionalidade precisa continuar funcionando;
   - manter componentes atuais quando eles carregam comportamento critico;
   - criar stubs visuais apenas quando aprovados e documentados;
   - nao inventar backend, endpoints ou dados.
7. Implemente de forma incremental, preservando conexoes existentes.
8. Rode verificacoes proporcionais: typecheck, lint, unit, build, teste de rota ou QA manual em dev server quando aplicavel.
9. Atualize documentacao do projeto com lacunas, perdas ou pendencias geradas pela refatoracao.
10. Entregue resumo com branch, arquivos alterados, funcionalidades preservadas, lacunas documentadas e verificacoes executadas.

## Documentacao obrigatoria de lacunas
Quando detectar diferenca entre design e backend atual, registre no local mais apropriado do repo:

- funcionalidade presente antes e perdida/removida pelo design;
- funcionalidade nova no design sem backend, dados ou acao;
- endpoint, schema ou integracao que falta;
- decisao tomada: preservar, remover, esconder, deixar stub ou bloquear;
- risco para usuario/produto se ficar pendente;
- criterio para considerar a lacuna resolvida.

Se o repo nao tiver documento proprio para isso, crie ou atualize um doc curto perto da area afetada, como `docs/frontend/refactor-gaps.md`, respeitando padroes locais. Nao crie documentacao duplicada quando uma doc existente cobre o tema.

## Regras duras
- Nao refatore uma rota incerta; confirme a rota primeiro.
- Nao trate handoff visual como fonte de verdade funcional.
- Nao remova chamada backend, validacao, permissao ou estado sem explicar e documentar.
- Nao adicione botao, formulario, menu ou fluxo que parece funcional se nao houver acao real ou stub aprovado.
- Nao hardcodar dados para substituir backend existente.
- Nao criar endpoints, migrations ou contratos backend sem pedido explicito.
- Nao ignorar instrucoes restritivas do usuario sobre partes que devem ou nao ser alteradas.

## Saida obrigatoria
- Rota refatorada e branch criada.
- Estrategia escolhida: do zero, parcial, preservar componentes ou incorporar apenas partes do handoff.
- Backend conectado: endpoints/actions/hooks/providers identificados.
- Funcionalidades preservadas.
- Funcionalidades removidas ou em risco, com justificativa.
- Funcionalidades novas sem backend, com doc atualizada.
- Arquivos alterados.
- Verificacoes executadas e resultado.
- Pendencias que precisam de decisao humana.

## Criterios de aceite
- A rota alvo esta explicita antes das edicoes.
- Worktree foi analisada e branch dedicada criada ou bloqueio relatado.
- Contratos backend existentes continuam conectados ou a perda esta documentada.
- Novos controles visuais sem funcionalidade real nao ficam silenciosos.
- Instrucoes do usuario sobre o que copiar, preservar ou ignorar foram respeitadas.
- Documentacao do projeto registra buracos funcionais relevantes.
- Resultado passou por verificacao proporcional ao risco.

## Skills relacionadas
- `project-context-loader`: carregar stack, comandos e padroes do repo.
- `ui-ux-pro-max-audit`: revisar qualidade visual e responsividade.
- `api-contract-auditor`: auditar contratos de endpoints afetados.
- `docs-sync-auditor`: garantir documentacao coerente com mudancas.
- `test-strategy-builder`: escolher testes proporcionais.
- `git-decision-router`: decidir commit, PR ou manter unstaged.

## Exemplos de uso
- Codex: `$frontend-refactor-contract-guardian Refatore a rota /dashboard usando este zip do AI Stitch, mas preserve a tabela atual e as acoes de exportacao.`
- Claude Code: `/frontend-refactor-contract-guardian Use o handoff do Claude Design apenas no hero da home; nao mexa no formulario nem na integracao com leads.`
