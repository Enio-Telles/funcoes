# 🔒 Políticas de Segurança Git - sefin_audit_5

## Configuração de Segurança Implementada

Este documento descreve as políticas de segurança configuradas para o repositório Git local.

### ✅ Configurações Ativas

#### 1. **Informações de Usuário**
- Nome: enio_telles
- Email: eniotelles@gmail.com

#### 2. **Proteções de Linha (CRLF)**
- `core.safecrlf=true` - Previne normalização automática de line endings que podem corromper arquivos

#### 3. **Push Seguro**
- `push.default=simple` - Push apenas para branch com mesmo nome no remoto

### 🛡️ Arquivos Ignorados (Segurança)

O arquivo `.gitignore` foi configurado para proteger:

- **Variáveis de Ambiente**: `.env`, `.env.local`, `.env.*.local`
- **Credenciais**: Chaves privadas (`.key`, `.pem`, `.pfx`), tokens de API
- **Certificados**: `.crt`, `.cer`, `.der`
- **Bases de Dados**: Arquivos `.db`, `.sqlite`, dumps SQL
- **Logs**: Arquivos de log que podem conter informações sensíveis

### 🪝 Git Hooks (Pre-commit)

Um pre-commit hook foi instalado para validar:
- ❌ Detectar padrões de secrets (password, api_key, token, private_key)
- ❌ Alertar sobre atribuições diretas de credenciais
- ⚠️ Avisos sobre arquivos grandes (>1MB)

**Localização**: `.git/hooks/pre-commit`

### 📋 Próximos Passos Recomendados

1. **Usuário Git Configurado** ✅
   ```bash
   # Já configurado:
   git config user.name "enio_telles"
   git config user.email "eniotelles@gmail.com"
   ```

2. **Configurar Chave SSH (Recomendado)**
   ```bash
   ssh-keygen -t ed25519 -C "eniotelles@gmail.com"
   ```

3. **Habilitar Assinatura de Commits (com GPG)**
   ```bash
   git config commit.gpgsign true
   git config user.signingkey [ID_DA_SUA_CHAVE_GPG]
   ```

4. **Revisar .gitignore Regularmente**
   ```bash
   git check-ignore -v arquivo_a_verificar
   ```

5. **Configurar Credenciais de Forma Segura**
   ```bash
   git config credential.helper cache  # Armazena por 15 min
   # ou
   git config credential.helper store  # Armazena permanentemente (usar com cuidado)
   ```

### 🚨 Boas Práticas

- ✅ Nunca commit `.env` ou arquivos com credenciais
- ✅ Use SSH ao invés de HTTPS para repositórios remotos
- ✅ Revise seus commits antes de fazer push: `git diff --staged`
- ✅ Use meaningful commit messages
- ✅ Mantenha histórico limpo: avoid force push em branches compartilhados
- ✅ Revise regularmente: `git log --oneline -10`

### 📚 Referências

- [Git Config Security](https://git-scm.com/book/en/v2/Git-Internals-Environment-Variables)
- [GitHub Security Best Practices](https://docs.github.com/en/code-security)
- [OWASP Git Security](https://cheatsheetseries.owasp.org/cheatsheets/Git_Cheat_Sheet.html)

---
**Gerado em**: 2026-03-13  
**Repositório**: C:\sefin_audit_5
