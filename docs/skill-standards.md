# Padrao de Skills

Use este padrao ao criar ou revisar skills do `agent-framework`.

## Principios
- Skill e procedimento reutilizavel, nao anotacao longa.
- `description` e o gatilho principal; coloque nela quando a skill deve ser usada.
- Mantenha `SKILL.md` curto. Conteudo longo vai para `rubrics/`, `workflows/`, `templates/` ou `docs/`.
- Prefira atualizar skill existente quando a nova ideia compartilha objetivo, entradas e saidas.
- Crie rubric para criterio de avaliacao, workflow para sequencia entre skills e template para formato de entrega.

## Estrutura obrigatoria
```yaml
---
name: nome-em-kebab-case
description: Use para ...
---
```

O nome deve bater com a pasta em `skills/<name>/`.

## Secoes recomendadas
- `## Objetivo`
- `## Quando usar`
- `## Quando nao usar`
- `## Entradas esperadas`
- `## Workflow`
- `## Saida obrigatoria`
- `## Criterios de aceite`
- `## Arquivos de apoio`
- `## Exemplos de uso`

## Qualidade do gatilho
- Comece a description com `Use para`.
- Inclua dominios, artefatos ou situacoes que devem disparar a skill.
- Evite descriptions genericas como "ajudar com desenvolvimento".
- Mantenha a description abaixo de 240 caracteres.

## Decisao de asset
| Necessidade | Asset recomendado |
| --- | --- |
| Procedimento acionavel e recorrente | Skill |
| Criterios para avaliar qualidade ou risco | Rubric |
| Sequencia entre varias skills | Workflow |
| Estrutura de saida reutilizavel | Template |
| Regra do framework ou manutencao | Doc |

## Checklist antes de commit
- Nome em kebab-case e igual ao frontmatter.
- Escopo nao duplica skill existente.
- Workflow tem passos observaveis.
- Saida obrigatoria e criterio de aceite sao claros.
- Arquivos de apoio existem e sao referenciados com parcimonia.
- `bash installers/verify-framework.sh` passa.
