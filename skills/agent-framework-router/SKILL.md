---
name: agent-framework-router
description: Use primeiro em tarefa nova - escolhe fast, standard ou critical e a categoria (agentes de IA, software, testes, revisao, design, seguranca, infra, orquestracao) com poucos assets.
---

# Agent Framework Router

## Objetivo
Dado um pedido, selecionar explicitamente `fast`, `standard` ou `critical` e
apontar rapidamente os assets certos. Dispatcher leve, nao executor.

## Quando usar
- No inicio de uma nova tarefa.
- Para respeitar `--fast`, `--standard`, `--critical` ou `--auto`.
- Para combinar poucos assets sem transformar trabalho comum em governanca.

## Quando nao usar
- Escolha de modelo/agente: use `model-routing`.
- Skill alvo ja obvia: chame-a direto.
- Retomada explicitamente persistente: use `framework-next`.

## Workflow
1. Leia a escolha explicita: `--fast`, `--standard`, `--critical` ou `--auto`;
   sem flag, use `auto`.
2. Em `auto`, `standard` e o padrao. E o modo do desenvolvimento normal.
3. Escolha `fast` apenas com evidencia positiva de trabalho curto e contido:
   ~10 minutos, poucos arquivos, comportamento previsivel, baixo impacto, facil
   reversao, sem decisao arquitetural.
4. `critical` e sempre uma escolha explicita: so selecione com `--critical` ou
   com pedido claro do usuario. Recomende-o — nomeando o dano — quando um
   defeito causar dano grave: quebrar o
   nucleo de auth/sessoes, invasao ou escalada de privilegio, vazamento entre
   tenants, perda/corrupcao seria de dados, movimentar dinheiro, gateway de
   pagamento, criptografia/segredos, recuperacao de conta, migration destrutiva
   ou dificil de reverter, derrubar parte essencial da producao, operacao
   irreversivel de grande blast radius.
5. Nao escale por area nem por tamanho. Tocar auth, ter migration, mexer em
   permissoes, envolver dados financeiros, exigir muitos testes ou alterar
   varios arquivos **nao** torna a tarefa `critical`.
6. Respeite a flag do usuario. Nunca eleve `--fast`/`--standard` para
   `critical` por conta propria: relate o dano detectado, recomende
   `--critical` e siga no modo pedido. A unica correcao automatica e o piso:
   area sensivel derruba `fast` para `standard`.
7. Se for retomada ou `critical`, e `.agent/STATE.md` existir, encaminhe para
   `framework-next`. A mera existencia de `.agent/` nao obriga uma nova tarefa a
   usar o kernel.
8. Identifique a categoria (secao "Roteamento por categoria"), leia so o arquivo
   dela, siga a instrucao que ele traz, liste 1-4 assets e corte o resto. Toda alteracao de
   software inclui `test-strategy-builder`, em qualquer modo e fora desse limite:
   decidir sobre testes e obrigatorio; criar testes novos depende de lacuna real.
9. Indique o primeiro asset a invocar.
10. Se CI, PR, merge ou integracao fizer parte do fluxo, acrescente o perfil de
    CI e as politicas de espera/proxima unidade, e selecione
    `ci-throughput-controller`. O modo continua sendo risco/execucao; o perfil de
    CI e um eixo separado.

## Modos

| Modo | Caminho | Defaults |
|---|---|---|
| `fast` | route → inspect → implement → targeted verification → diff review | sem `.agent/`, spec, contrato, seal, ledger, reviewers separados ou worktree |
| `standard` | route → focused grounding → short plan → implement → tests → integrated review | estado opcional, spec/contrato leves, uma review integrada, sem seal |
| `critical` | lifecycle persistente completo P0/P1 | estado, spec, contratos, seal, ledger e duas reviews independentes |

Regra de desempate: duvida → `standard`; curto e contido comprovado → `fast`;
dano grave comprovado → `critical`.

Calibracao esperada, como referencia e nao como cota: `fast` ~30%, `standard`
~65-70%, `critical` ~1-5%.

O modo pertence a tarefa. Uma fase pode conter tarefas `fast`, `standard` e
`critical`; uma tarefa `critical` nao eleva as vizinhas. Para corrigir uma
classificacao ja registrada, use
`framework-next set-execution-mode` — escalada exige `--risk` nomeando o dano
grave; reducao exige apenas `--reason`.

## Roteamento por categoria

1. Ache a categoria principal pelos gatilhos da tabela.
2. Leia **somente** o arquivo dela (dois, se o pedido cruzar categorias) e siga a
   instrucao que ele traz antes de escolher assets. Nao abra os outros.
3. Escolha 1-4 assets do arquivo. Pisos obrigatorios (testes em alteracoes de
   software, agentes e frontend) nao contam no limite.
4. Pedido que cruza categorias: assets da principal + no maximo 1 de outra.
5. O modo (`fast`/`standard`/`critical`) vale para todas; a categoria nao muda o
   modo.

| Categoria | Gatilhos | Arquivo | Piso obrigatorio |
|---|---|---|---|
| Agentes de IA | codigo que chama LLM, system prompt, tools de agente, chatbot/WhatsApp/assistente, comportamento ou eval de conversa, troca de modelo | `categories/01-agentes.md` | `rubrics/agent-design.md` |
| Desenvolvimento de software | feature, endpoint, bug, refatoracao, backend, plano de implementacao, repo novo, ideia aberta | `categories/02-software.md` | — |
| Testes e verificacao | estrategia de testes, cobertura, "esta pronto?", QA do app rodando | `categories/03-testes.md` | — |
| Revisao | revisar diff/PR, decidir profundidade de review | `categories/04-revisao.md` | — |
| Design e frontend | componente, pagina, layout, estilo, animacao, gesto, acessibilidade, UI web ou mobile | `categories/05-frontend.md` | `apple-design`, `impeccable:impeccable`, `design-taste-frontend` |
| Motion e video | video, MP4, HyperFrames, Remotion, animacao renderizada | `categories/06-video.md` | — |
| Seguranca | vulnerabilidade, auth, segredo, dados pessoais, pen test | `categories/07-seguranca.md` | — |
| Infraestrutura e operacao | deploy, release, CI, migration, env/config, dependencia, logs, performance | `categories/08-infra.md` | — |
| Orquestracao, estado e contexto | varios agentes, Maestri, worktrees, retomar trabalho, estado persistente, contexto cheio, handoff, escolher modelo para a tarefa | `categories/09-orquestracao.md` | — |
| Git, PR e documentacao | commit, abrir PR, descricao de PR, decidir ou sincronizar documentacao | `categories/10-git-docs.md` | — |
| Marketing e anuncios | Google Ads, campanha, trafego pago, CRM e audiencias | `categories/11-marketing.md` | — |
| Manutencao do framework | instalar ou atualizar o framework, criar/auditar/procurar skill | `categories/12-framework.md` | — |

Caminhos relativos a esta skill. Os arquivos sao a fonte unica: o cabecalho de
cada um (`keywords`, `required`) e o que `scripts/agent-framework-route` usa para
devolver `category`, `category_file` e os pisos. Skill nova entra na tabela do
arquivo da categoria, nao aqui.

## Saida obrigatoria
```yaml
selected_mode: fast | standard | critical
reason:
category:             # nome da categoria, ou vazio se nenhuma casar
category_file:        # arquivo lido em categories/
risk_factors: []      # apenas caminhos de dano grave nomeados
sensitive_areas: []   # impede fast (piso standard); nunca escala sozinho para critical
fast_factors: []
complexity_factors: []
assets_selected: []
assets_skipped: []
```

Quando CI/PR/integracao entra no fluxo, o router tambem reporta o eixo de CI —
campos opcionais e aditivos, que nao alteram o significado de fast/standard/critical:

```yaml
ci_profile: minimal | targeted | full
ci_blocking_point: before_merge | now | none
ci_wait_policy: background | blocking_before_merge | blocking_now
next_work_policy: continue_independent | stack_local | wait
local_gates: []
remote_gates: []
deferred_gates: []      # cada gate adiado declara onde roda de fato
runner_policy:          # contencao de runner self-hosted compartilhado
```

`standard` nao implica pipeline completo nem espera sincrona. CI bloqueia merge,
nao necessariamente a proxima unidade de trabalho. Perfil `full` levanta
`publication_hold`, nao espera automatica. Detalhe em
`kernel/ci-throughput-policy.md`; sequencia operacional em
`workflows/ci-throughput.md`.

Contexto operacional entra como dado, nao como texto do pedido:

```bash
./scripts/agent-framework-route --auto \
  --runner-kind self_hosted_shared --remote-ci-running \
  --next-unit dependent --unit-ref pr-42 \
  "Implemente a tela de fornecedores."
```

Tambem aceita `--ci-context-json '{...}'`. Campo ausente usa o default
documentado; dependencia nao declarada nunca vira dependencia confirmada.

Toda selecao `fast` ou `critical` inclui uma justificativa concreta: `fast`
mostra por que o trabalho e curto e contido; `critical` nomeia o dano grave. A
saida pode ainda indicar intencao e primeiro asset.

## Criterios de aceite
- `standard` e o default quando nada argumenta em contrario.
- `fast` exige evidencia positiva de escopo curto e contido, sem area sensivel.
- `critical` nunca e inferido: exige selecao explicita. Um caminho de dano
  grave detectado vira recomendacao, com o dano nomeado.
- Area sensivel (auth, migration, financeiro, tenant) impede `fast` (piso
  `standard`) mas nunca escala sozinha para `critical`.
- No maximo 4 assets, sem contar os pisos: `rubrics/agent-design.md` em agentes e
  `apple-design` + `impeccable:impeccable` + `design-taste-frontend` em frontend, alem de
  `test-strategy-builder` em toda alteracao de software; sem listar tudo.
- Alteracoes de software retornam `test-strategy-builder` em `assets_selected`
  em qualquer modo, inclusive quando a decisao for nenhum teste novo.
- Qualquer tarefa de agente retorna `rubrics/agent-design.md` em `assets_selected`.
- Qualquer tarefa de frontend retorna `apple-design`, `impeccable:impeccable` e `design-taste-frontend` em `assets_selected`.
- Nao duplicar checklist de rubric/workflow aqui; so referenciar.
- Ler um arquivo de categoria por pedido (dois se cruzar); nunca todos.
- Backend simples nao e automaticamente `critical`.
- Roteamento nao cria `.agent/` nem instancia templates.
- Perfil de CI nunca e derivado do modo sozinho: `standard` pode ser `minimal`,
  `targeted` ou `full` conforme o impacto real da mudanca.
- Nao orientar espera sincrona por CI sem motivo nomeado.

## Exemplos de uso
- Codex: `$agent-framework-router Qual skill para auditar este PR de API?`
- Codex: `$agent-framework-router --fast Corrija o typo no título da página.`
- Codex: `$agent-framework-router --standard Implemente o endpoint e os testes.`
- Codex: `$agent-framework-router --critical Troque o gateway de pagamento.`
- Claude Code: `/agent-framework-router Por onde começo neste repo desconhecido?`
