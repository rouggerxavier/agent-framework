---
name: agent-framework-installer
description: Use para instalar, atualizar, verificar e sincronizar o agent-framework local em Codex e Claude Code de forma segura e portavel.
---

# Agent Framework Installer

## Objetivo
Guiar a instalacao, atualizacao, verificacao e sincronizacao do `~/agent-framework` em qualquer computador sem sobrescrever skills externas nem expor dados sensiveis.

## Quando usar
- Ao configurar um computador novo.
- Ao atualizar skills depois de `git pull`.
- Ao verificar se o framework esta consistente.
- Ao sincronizar skills para Codex ou Claude Code.

## Quando nao usar
- Para criar novas skills de dominio.
- Para apagar, resetar ou limpar instalacoes existentes.
- Para gerenciar secrets, tokens, `.env` ou chaves privadas.

## Entradas esperadas
- Caminho do framework, normalmente `~/agent-framework`.
- Alvo de instalacao: Codex, Claude Code ou ambos.
- Estado do repo Git, se existir.

## Workflow
1. Localize `~/agent-framework` ou confirme o caminho informado.
2. Verifique a estrutura com `bash installers/verify-framework.sh`.
3. Instale no Codex com `bash installers/install-codex.sh`.
4. Instale no Claude Code com `bash installers/install-claude.sh`.
5. Para ambos, use `bash installers/install-all.sh`.
6. Para atualizar, entre no framework, rode `bash installers/update-framework.sh` e depois reinstale se a verificacao passar.
7. Para portabilidade, use Git privado: commit, push, clone em outro computador e rode `install-all.sh`.

## Saida obrigatoria
- Caminho do framework localizado.
- Resultado da verificacao.
- Alvos instalados ou instrucoes para instalar.
- Avisos sobre arquivos externos preservados.
- Proximo comando recomendado.

## Criterios de aceite
- Nunca usar `git reset`, `git clean`, force pull ou remocao ampla.
- Nao salvar secrets, tokens, `.env` ou chaves privadas.
- Nao apagar skills externas fora dos nomes do framework.
- Verificar `SKILL.md`, `name` e `description` antes de instalar.

## Arquivos de apoio
Regras e portabilidade ficam nos docs; nao duplicar aqui.
- Docs: ../../docs/maintenance.md
- Docs: ../../docs/portability.md

## Exemplos de uso
- Codex: `$agent-framework-installer Verifique e instale minhas skills neste computador.`
- Claude Code: `/agent-framework-installer Atualize o framework via git pull seguro e sincronize.`
