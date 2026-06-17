-- =====================================================================
-- FarmTech Solutions - Fase 3: Banco de Dados Estruturado
-- Script: 01_criar_tabela.sql
-- Descricao: Criacao da tabela LEITURA_SENSOR que armazena os dados
--            coletados pelo sistema IoT da Fase 2 (ESP32 + sensores).
-- =====================================================================

-- Remove a tabela caso ja exista (somente em ambiente de testes)
-- Em producao, comente esta linha para evitar perda de dados.
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE leitura_sensor';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE != -942 THEN -- ORA-00942: table or view does not exist
            RAISE;
        END IF;
END;
/

-- Criacao da tabela
CREATE TABLE leitura_sensor (
    id_leitura     NUMBER         PRIMARY KEY,
    data_hora      VARCHAR2(19)   NOT NULL,    -- formato: YYYY-MM-DD HH24:MI:SS
    umidade_solo   NUMBER(5,2)    NOT NULL,    -- em %
    umidade_ar     NUMBER(5,2)    NOT NULL,    -- em %
    temperatura    NUMBER(5,2)    NOT NULL,    -- em graus Celsius
    ph_solo        NUMBER(4,2)    NOT NULL,    -- pH entre 0 e 14
    fosforo        VARCHAR2(3)    NOT NULL,    -- SIM ou NAO
    potassio       VARCHAR2(3)    NOT NULL,    -- SIM ou NAO
    status_bomba   VARCHAR2(10)   NOT NULL,    -- LIGADA ou DESLIGADA
    CONSTRAINT chk_umidade_solo CHECK (umidade_solo BETWEEN 0 AND 100),
    CONSTRAINT chk_umidade_ar   CHECK (umidade_ar BETWEEN 0 AND 100),
    CONSTRAINT chk_ph           CHECK (ph_solo BETWEEN 0 AND 14),
    CONSTRAINT chk_fosforo      CHECK (fosforo IN ('SIM', 'NAO')),
    CONSTRAINT chk_potassio     CHECK (potassio IN ('SIM', 'NAO')),
    CONSTRAINT chk_bomba        CHECK (status_bomba IN ('LIGADA', 'DESLIGADA'))
);

-- Indice para consultas por periodo (a mais usada na dashboard)
CREATE INDEX idx_leitura_data ON leitura_sensor(data_hora);

COMMIT;
