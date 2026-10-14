# Emanuely Matos — site inicial

Site responsivo em Flask com catálogo editável, painel administrativo e pedidos de agendamento.

## Segurança antes de publicar
1. Defina variáveis de ambiente `SECRET_KEY`, `ADMIN_USERNAME` e `ADMIN_PASSWORD` no serviço de hospedagem.
2. Use uma senha forte e exclusiva. Não coloque senhas no GitHub.
3. Configure um banco PostgreSQL persistente em `DATABASE_URL`. O SQLite local é apenas para testes.
4. O botão de WhatsApp abre uma conversa; envio automático pela API oficial não está incluído.
5. Antes de receber clientes reais, teste login, agendamento, permissões, backup e política de privacidade.

## Testar no computador
Requer Python 3.11 ou superior.

```bash
python -m venv .venv
# Windows: .venv\Scripts\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements.txt
```

Defina `ADMIN_USERNAME`, `ADMIN_PASSWORD` e `SECRET_KEY` nas variáveis de ambiente e execute:

```bash
python app.py
```

Abra http://127.0.0.1:5000

## Publicar
Suba estes arquivos para um repositório GitHub privado ou público (não há segredos no código). No serviço de hospedagem Python, configure:
- Build command: `pip install -r requirements.txt`
- Start command: `gunicorn app:app`
- Variáveis: `SECRET_KEY`, `ADMIN_USERNAME`, `ADMIN_PASSWORD`, `DATABASE_URL`

Planos gratuitos e suas regras mudam; confirme a disponibilidade de servidor e banco persistente antes de publicar.
