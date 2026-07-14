# SIGOP — Sistema Integrado de Gerenciamento de Operações Policiais

Delegacia Especializada de Estelionato de Cuiabá/MT

## Estrutura do projeto

```
SIGOP/
├── app.py
├── requirements.txt
├── sql/
│   └── schema.sql
├── utils/
│   ├── __init__.py
│   └── db.py
└── pages/
    ├── 1_Dashboard.py
    ├── 2_Efetivo.py
    ├── 3_Operacoes.py
    ├── 4_CQH.py
    ├── 5_Afastamentos.py
    ├── 6_Viaturas.py
    ├── 7_Ranking.py
    └── 8_Gerar_Documento.py
```

## Passo a passo para colocar no ar

### 1. Criar o projeto no Supabase
1. Acesse https://supabase.com e crie uma conta (ou faça login).
2. Clique em **New Project** e preencha nome, senha do banco e região.
3. Aguarde o projeto ser criado (leva cerca de 2 minutos).

### 2. Criar as tabelas
1. No painel do Supabase, vá em **SQL Editor** (menu lateral).
2. Clique em **New query**.
3. Cole todo o conteúdo do arquivo `sql/schema.sql` deste projeto.
4. Clique em **Run**. Isso cria todas as tabelas necessárias.

### 3. Pegar as chaves de conexão
1. No painel do Supabase, vá em **Project Settings → API**.
2. Copie o **Project URL** (algo como `https://xxxxx.supabase.co`).
3. Copie a **anon public key** (chave longa).

### 4. Subir o projeto para o GitHub
1. Crie um repositório novo (ex: `SIGOP`).
2. Envie todos os arquivos desta pasta para o repositório, mantendo a
   estrutura de pastas (`pages/`, `utils/`, `sql/`).
   - **Não suba o arquivo `.streamlit/secrets_template.toml` com dados reais.**
     Ele é só um modelo.

### 5. Publicar no Streamlit Cloud
1. Acesse https://share.streamlit.io e clique em **Create app**.
2. Selecione o repositório `SIGOP`, branch `main`, arquivo principal `app.py`.
3. Antes de clicar em Deploy, vá em **Advanced settings → Secrets** e cole:

```toml
SUPABASE_URL = "https://SEU-PROJETO.supabase.co"
SUPABASE_KEY = "sua-chave-anon-aqui"
```

4. Clique em **Deploy**.

### 6. Testar
Abra o app publicado. Na página inicial, expanda "Status da conexão com o
banco de dados" para confirmar que a conexão com o Supabase está funcionando.
Depois, cadastre um servidor na página **Efetivo** para testar.

## Módulos disponíveis

- **Dashboard** — visão geral do dia (CQH, próximas operações, afastamentos)
- **Efetivo** — cadastro de delegados, escrivães e investigadores
- **Operações** — cadastro, briefing, escala de equipe e viatura, com
  verificação automática de conflitos (servidor de férias/folga/CQH/outra
  operação não pode ser escalado)
- **CQH** — escala de plantão, também com verificação de conflitos
- **Afastamentos** — férias, folgas e licenças
- **Viaturas** — cadastro e status da frota
- **Ranking** — estatísticas e gráfico de participação em operações
- **Gerar Documento** — gera a Ordem de Operação em Word (.docx) e PDF,
  pronta para impressão ou compartilhamento

## Próximos passos sugeridos

- Autenticação de usuários (login da chefia) usando `st.login` ou Supabase Auth
- Exportação de relatórios em lote (mensal, anual)
- Notificações automáticas de conflitos futuros
- Calendário visual interativo (ex: usando `streamlit-calendar`)
