-- ============================================================
-- SIGOP - Sistema Integrado de Gerenciamento de Operações Policiais
-- Script de criação das tabelas no Supabase (PostgreSQL)
-- Copie e execute este script no SQL Editor do seu projeto Supabase
-- ============================================================

-- Tabela de servidores (efetivo)
create table if not exists servidores (
    id bigint generated always as identity primary key,
    nome text not null,
    matricula text,
    cargo text not null check (cargo in ('Delegado de Polícia', 'Escrivão de Polícia', 'Investigador de Polícia')),
    equipe text,
    telefone text,
    situacao text not null default 'Ativo' check (situacao in ('Ativo', 'Férias', 'Licença')),
    observacoes text,
    created_at timestamp with time zone default now()
);

-- Tabela de viaturas
create table if not exists viaturas (
    id bigint generated always as identity primary key,
    identificacao text not null,
    modelo text,
    status text not null default 'Disponível' check (status in ('Disponível', 'Oficina', 'Em operação')),
    created_at timestamp with time zone default now()
);

-- Tabela de operações
create table if not exists operacoes (
    id bigint generated always as identity primary key,
    nome text not null,
    data date not null,
    horario time,
    local text,
    cidade text,
    delegado_responsavel text,
    objetivo text,
    briefing text,
    status text not null default 'Planejada' check (status in ('Planejada', 'Em andamento', 'Concluída', 'Cancelada')),
    created_at timestamp with time zone default now()
);

-- Vínculo entre operações, servidores e viaturas
create table if not exists operacao_participantes (
    id bigint generated always as identity primary key,
    operacao_id bigint references operacoes(id) on delete cascade,
    servidor_id bigint references servidores(id) on delete cascade,
    equipe text,
    viatura_id bigint references viaturas(id),
    folga_concedida text default 'Sem folga' check (folga_concedida in ('Sem folga', 'Meio período', 'Dia integral')),
    created_at timestamp with time zone default now()
);

-- Escala de CQH (plantão)
create table if not exists cqh (
    id bigint generated always as identity primary key,
    data date not null,
    servidor_id bigint references servidores(id) on delete cascade,
    equipe text,
    created_at timestamp with time zone default now()
);

-- Afastamentos (férias, folga, licença)
create table if not exists afastamentos (
    id bigint generated always as identity primary key,
    servidor_id bigint references servidores(id) on delete cascade,
    tipo text not null check (tipo in ('Férias', 'Folga', 'Licença', 'Folga Operacional')),
    data_inicio date not null,
    data_fim date not null,
    observacoes text,
    created_at timestamp with time zone default now()
);

-- Índices úteis
create index if not exists idx_operacao_participantes_operacao on operacao_participantes(operacao_id);
create index if not exists idx_operacao_participantes_servidor on operacao_participantes(servidor_id);
create index if not exists idx_afastamentos_servidor on afastamentos(servidor_id);
create index if not exists idx_cqh_servidor on cqh(servidor_id);
