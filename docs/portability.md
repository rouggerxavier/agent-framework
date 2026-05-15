# Portabilidade

Fluxo recomendado para usar o framework em mais de um computador.

## No computador principal

```bash
cd ~/agent-framework
git add .
git commit -m "Update agent framework"
git push
```

## Em outro computador

```bash
git clone git@github.com:SEU_USUARIO/agent-framework.git ~/agent-framework
cd ~/agent-framework
bash installers/verify-framework.sh
bash installers/install-all.sh
```

## Atualizacoes futuras

```bash
cd ~/agent-framework
git pull --ff-only
bash installers/verify-framework.sh
bash installers/install-all.sh
```

## Regras de seguranca

- Edite skills somente em `~/agent-framework`.
- Nao salve `.env`, tokens, senhas, chaves privadas ou dados sensiveis.
- Use repositorio Git privado.
- Rode `verify-framework.sh` antes de instalar.
