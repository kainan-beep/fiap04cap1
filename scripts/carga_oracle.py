"""
carga_oracle.py - Caminho alternativo ao wizard 'Importar Dados'.

Este script faz a carga das leituras dos sensores (CSV gerado em
dados/leituras_sensores.csv) diretamente no Oracle FIAP, executando:

  1. Criacao da tabela LEITURA_SENSOR (caso nao exista).
  2. Limpeza da tabela (TRUNCATE) para evitar duplicacao.
  3. Inserts em lote via executemany (mais rapido que insert linha a linha).
  4. Verificacao final com SELECT COUNT(*) e amostra.

CREDENCIAIS: defina as variaveis de ambiente ORACLE_USER, ORACLE_PASSWORD
e (opcionalmente) ORACLE_DSN com seu RM e data de nascimento (DDMMYY)
antes de executar. Nao edite credenciais direto no codigo -- o
repositorio e publico.

Exemplo:
    export ORACLE_USER=RM570594
    export ORACLE_PASSWORD=210798
    python carga_oracle.py

Dependencia: pip install oracledb
"""

import csv
import os
import sys
import oracledb


# ========================== CONFIGURACAO ==========================

CONFIG_DB = {
    "user": os.environ.get("ORACLE_USER", ""),
    "password": os.environ.get("ORACLE_PASSWORD", ""),
    "dsn": os.environ.get("ORACLE_DSN", "oracle.fiap.com.br:1521/ORCL"),
}

if not CONFIG_DB["user"] or not CONFIG_DB["password"]:
    print("[ERRO] Defina as variaveis de ambiente ORACLE_USER e ORACLE_PASSWORD.")
    sys.exit(1)

# Caminho do CSV gerado pelo gerar_dados_sensores.py
CAMINHO_CSV = os.path.join(
    os.path.dirname(__file__), "..", "dados", "leituras_sensores.csv"
)


# ========================== CONEXAO ==========================

def conectar() -> oracledb.Connection:
    """Abre conexao com o banco Oracle FIAP."""
    try:
        conn = oracledb.connect(**CONFIG_DB)
        print("  [OK] Conectado ao Oracle FIAP.")
        return conn
    except oracledb.Error as erro:
        print(f"  [ERRO] Falha ao conectar: {erro}")
        sys.exit(1)


# ========================== DDL ==========================

DDL_CRIAR_TABELA = """
BEGIN
    EXECUTE IMMEDIATE '
        CREATE TABLE leitura_sensor (
            id_leitura     NUMBER         PRIMARY KEY,
            data_hora      VARCHAR2(19)   NOT NULL,
            umidade_solo   NUMBER(5,2)    NOT NULL,
            umidade_ar     NUMBER(5,2)    NOT NULL,
            temperatura    NUMBER(5,2)    NOT NULL,
            ph_solo        NUMBER(4,2)    NOT NULL,
            fosforo        VARCHAR2(3)    NOT NULL,
            potassio       VARCHAR2(3)    NOT NULL,
            status_bomba   VARCHAR2(10)   NOT NULL,
            CONSTRAINT chk_fosforo      CHECK (fosforo IN (''SIM'', ''NAO'')),
            CONSTRAINT chk_potassio     CHECK (potassio IN (''SIM'', ''NAO'')),
            CONSTRAINT chk_bomba        CHECK (status_bomba IN (''LIGADA'', ''DESLIGADA''))
        )
    ';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -955 THEN  -- ORA-00955: tabela ja existe
            NULL;
        ELSE
            RAISE;
        END IF;
END;
"""


def criar_tabela(conn: oracledb.Connection) -> None:
    """Cria a tabela LEITURA_SENSOR caso ainda nao exista."""
    cursor = conn.cursor()
    try:
        cursor.execute(DDL_CRIAR_TABELA)
        conn.commit()
        print("  [OK] Tabela LEITURA_SENSOR verificada/criada.")
    finally:
        cursor.close()


def limpar_tabela(conn: oracledb.Connection) -> None:
    """Apaga todas as linhas da tabela antes de carregar novos dados."""
    cursor = conn.cursor()
    try:
        cursor.execute("TRUNCATE TABLE leitura_sensor")
        print("  [OK] Tabela limpa (TRUNCATE).")
    finally:
        cursor.close()


# ========================== CARGA ==========================

def ler_csv(caminho: str) -> list:
    """Le o CSV gerado e retorna uma lista de tuplas pronta para insert."""
    if not os.path.exists(caminho):
        print(f"  [ERRO] Arquivo nao encontrado: {caminho}")
        print("         Rode antes: python gerar_dados_sensores.py")
        sys.exit(1)

    registros = []
    with open(caminho, "r", encoding="utf-8") as arq:
        reader = csv.DictReader(arq)
        for linha in reader:
            registros.append((
                int(linha["id_leitura"]),
                linha["data_hora"],
                float(linha["umidade_solo"]),
                float(linha["umidade_ar"]),
                float(linha["temperatura"]),
                float(linha["ph_solo"]),
                linha["fosforo"],
                linha["potassio"],
                linha["status_bomba"],
            ))
    print(f"  [OK] {len(registros)} registros lidos de {os.path.basename(caminho)}.")
    return registros


def inserir_lote(conn: oracledb.Connection, registros: list) -> None:
    """Insere todos os registros em uma unica operacao em lote."""
    cursor = conn.cursor()
    sql = """
        INSERT INTO leitura_sensor (
            id_leitura, data_hora, umidade_solo, umidade_ar,
            temperatura, ph_solo, fosforo, potassio, status_bomba
        ) VALUES (:1, :2, :3, :4, :5, :6, :7, :8, :9)
    """
    try:
        cursor.executemany(sql, registros)
        conn.commit()
        print(f"  [OK] {cursor.rowcount} registros inseridos.")
    except oracledb.Error as erro:
        conn.rollback()
        print(f"  [ERRO] Falha na carga: {erro}")
        sys.exit(1)
    finally:
        cursor.close()


# ========================== VERIFICACAO ==========================

def verificar_carga(conn: oracledb.Connection) -> None:
    """Roda SELECTs de validacao apos a carga."""
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM leitura_sensor")
        total = cursor.fetchone()[0]
        print(f"\n  Total de leituras no banco: {total}")

        cursor.execute("""
            SELECT id_leitura, data_hora, umidade_solo, status_bomba
            FROM leitura_sensor
            WHERE ROWNUM <= 5
            ORDER BY id_leitura
        """)
        print("\n  Amostra das 5 primeiras leituras:")
        print(f"  {'ID':<5}{'Data/Hora':<22}{'Umid. Solo':<13}{'Bomba':<12}")
        print("  " + "-" * 50)
        for linha in cursor:
            print(f"  {linha[0]:<5}{linha[1]:<22}{linha[2]:<13.2f}{linha[3]:<12}")
    finally:
        cursor.close()


# ========================== EXECUCAO ==========================

def main():
    print()
    print("  " + "=" * 60)
    print("  CARGA DAS LEITURAS DOS SENSORES NO ORACLE FIAP")
    print("  " + "=" * 60)

    conn = conectar()
    try:
        criar_tabela(conn)
        limpar_tabela(conn)
        registros = ler_csv(CAMINHO_CSV)
        inserir_lote(conn, registros)
        verificar_carga(conn)
    finally:
        conn.close()

    print("\n  " + "=" * 60)
    print("  Carga concluida com sucesso.")
    print("  " + "=" * 60)


if __name__ == "__main__":
    main()
