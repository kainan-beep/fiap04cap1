-- =====================================================================
-- FarmTech Solutions - Fase 3: Banco de Dados Estruturado
-- Script: 02_consultas.sql
-- Descricao: Consultas SQL exigidas pelo barema (item "Consultas SQL").
--            Cada bloco resolve uma pergunta de negocio relevante.
-- =====================================================================

-- ----------------------------------------------------------------------
-- 1) Consulta basica: todos os dados da tabela (exigida no enunciado)
-- ----------------------------------------------------------------------
SELECT * FROM leitura_sensor;


-- ----------------------------------------------------------------------
-- 2) Quantas leituras estao armazenadas?
-- ----------------------------------------------------------------------
SELECT COUNT(*) AS total_leituras FROM leitura_sensor;


-- ----------------------------------------------------------------------
-- 3) Estatisticas descritivas da umidade do solo
-- ----------------------------------------------------------------------
SELECT
    ROUND(MIN(umidade_solo), 2) AS umidade_minima,
    ROUND(MAX(umidade_solo), 2) AS umidade_maxima,
    ROUND(AVG(umidade_solo), 2) AS umidade_media,
    ROUND(STDDEV(umidade_solo), 2) AS desvio_padrao
FROM leitura_sensor;


-- ----------------------------------------------------------------------
-- 4) Quantas vezes a bomba de irrigacao foi acionada?
-- ----------------------------------------------------------------------
SELECT
    status_bomba,
    COUNT(*) AS qtd_leituras,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM leitura_sensor), 2) AS percentual
FROM leitura_sensor
GROUP BY status_bomba
ORDER BY qtd_leituras DESC;


-- ----------------------------------------------------------------------
-- 5) Leituras criticas: umidade do solo abaixo de 30%
-- ----------------------------------------------------------------------
SELECT id_leitura, data_hora, umidade_solo, status_bomba
FROM leitura_sensor
WHERE umidade_solo < 30
ORDER BY data_hora;


-- ----------------------------------------------------------------------
-- 6) Leituras com pH fora da faixa ideal (5.5 a 7.0)
-- ----------------------------------------------------------------------
SELECT id_leitura, data_hora, ph_solo, fosforo, potassio
FROM leitura_sensor
WHERE ph_solo < 5.5 OR ph_solo > 7.0
ORDER BY ph_solo;


-- ----------------------------------------------------------------------
-- 7) Quantas leituras detectaram presenca de Fosforo E Potassio juntos?
-- ----------------------------------------------------------------------
SELECT COUNT(*) AS leituras_com_p_e_k
FROM leitura_sensor
WHERE fosforo = 'SIM' AND potassio = 'SIM';


-- ----------------------------------------------------------------------
-- 8) Media diaria da umidade do solo e da temperatura
-- ----------------------------------------------------------------------
SELECT
    SUBSTR(data_hora, 1, 10) AS data,
    ROUND(AVG(umidade_solo), 2) AS umidade_media,
    ROUND(AVG(temperatura), 2) AS temperatura_media,
    COUNT(*) AS qtd_leituras
FROM leitura_sensor
GROUP BY SUBSTR(data_hora, 1, 10)
ORDER BY data;


-- ----------------------------------------------------------------------
-- 9) Ultimas 10 leituras registradas (monitoramento recente)
-- ----------------------------------------------------------------------
SELECT *
FROM (
    SELECT * FROM leitura_sensor
    ORDER BY data_hora DESC
)
WHERE ROWNUM <= 10;
