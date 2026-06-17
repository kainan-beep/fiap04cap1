"""
gerar_dados_sensores.py - Geracao de dados simulados dos sensores da Fase 2.

Simula leituras coletadas pelo sistema IoT desenvolvido na Fase 2:
  - ESP32 + DHT22 (umidade e temperatura do ar)
  - Sensor capacitivo de umidade do solo
  - LDR usado como sensor de pH (calibracao linear)
  - Botoes que simulam presenca de Fosforo (P) e Potassio (K)
  - Rele que aciona a bomba de irrigacao quando umidade do solo < limite

Saida: dados/leituras_sensores.csv
Formato: cabecalho na primeira linha + valores numericos/textuais separados
por virgula. Pronto para importacao no Oracle SQL Developer via wizard
'Importar Dados' ou via o script carga_oracle.py.
"""

import csv
import os
import random
from datetime import datetime, timedelta

# ========================== CONFIGURACAO ==========================

# Quantidade de leituras a serem geradas
TOTAL_LEITURAS = 240

# Intervalo entre leituras (simulando uma coleta a cada 30 minutos)
INTERVALO_MINUTOS = 30

# Data inicial das leituras (5 dias para tras a partir do momento atual)
DATA_INICIAL = datetime.now() - timedelta(days=5)

# Limites de acionamento da bomba (replicando a logica do ESP32)
UMIDADE_SOLO_MIN = 30.0   # liga a bomba se umidade < 30%
UMIDADE_SOLO_MAX = 70.0   # desliga se umidade > 70%

# Faixa esperada de pH (LDR calibrado entre 0-14)
PH_MIN_IDEAL = 5.5
PH_MAX_IDEAL = 7.0

# Pasta de saida
PASTA_DADOS = os.path.join(os.path.dirname(__file__), "..", "dados")
ARQUIVO_SAIDA = os.path.join(PASTA_DADOS, "leituras_sensores.csv")


# ========================== SIMULACAO ==========================

def simular_leitura(data_hora: datetime, estado_bomba_anterior: str,
                    umidade_anterior: float) -> dict:
    """Gera uma leitura simulada com correlacoes realistas entre variaveis."""

    # Umidade do solo: decai naturalmente, sobe rapido quando bomba esta ligada
    hora = data_hora.hour
    if estado_bomba_anterior == "LIGADA":
        # irrigando: ganha umidade
        delta = random.uniform(3.0, 6.0)
    else:
        # secando: perde mais durante o dia (sol/transpiracao)
        if 9 <= hora <= 17:
            delta = -random.uniform(1.5, 3.5)
        else:
            delta = -random.uniform(0.3, 1.2)

    umidade_solo = umidade_anterior + delta + random.gauss(0, 1.0)
    umidade_solo = max(10.0, min(95.0, umidade_solo))
    umidade_solo = round(umidade_solo, 2)

    # Temperatura: ciclo diurno (frio de madrugada, quente a tarde)
    temp_base = 18 + 10 * abs(1 - abs(hora - 14) / 14)
    temperatura = round(temp_base + random.gauss(0, 1.5), 2)

    # Umidade do ar: inversamente relacionada a temperatura
    umidade_ar = round(max(30.0, min(95.0, 90 - temperatura + random.gauss(0, 5))), 2)

    # pH do solo: levemente variavel, geralmente proximo ao ideal
    ph = round(random.gauss(6.3, 0.6), 2)
    ph = max(4.0, min(9.0, ph))

    # P e K: presenca simulada por botoes (booleano)
    # Aproximadamente 65% das leituras com P presente, 70% com K presente
    fosforo_presente = "SIM" if random.random() < 0.65 else "NAO"
    potassio_presente = "SIM" if random.random() < 0.70 else "NAO"

    # Logica da bomba (histerese, igual ao ESP32 da Fase 2)
    if umidade_solo < UMIDADE_SOLO_MIN:
        status_bomba = "LIGADA"
    elif umidade_solo > UMIDADE_SOLO_MAX:
        status_bomba = "DESLIGADA"
    else:
        status_bomba = estado_bomba_anterior

    return {
        "data_hora": data_hora.strftime("%Y-%m-%d %H:%M:%S"),
        "umidade_solo": umidade_solo,
        "umidade_ar": umidade_ar,
        "temperatura": temperatura,
        "ph_solo": ph,
        "fosforo": fosforo_presente,
        "potassio": potassio_presente,
        "status_bomba": status_bomba,
    }


def gerar_dataset(total: int) -> list:
    """Gera a lista completa de leituras simuladas."""
    leituras = []
    estado_bomba = "DESLIGADA"
    umidade = 55.0  # umidade inicial do solo
    data_hora_atual = DATA_INICIAL

    for i in range(total):
        leitura = simular_leitura(data_hora_atual, estado_bomba, umidade)
        leitura["id_leitura"] = i + 1
        leituras.append(leitura)
        estado_bomba = leitura["status_bomba"]
        umidade = leitura["umidade_solo"]
        data_hora_atual += timedelta(minutes=INTERVALO_MINUTOS)

    return leituras


def salvar_csv(leituras: list, caminho: str) -> None:
    """Salva as leituras em arquivo CSV pronto para importacao no Oracle."""
    if not os.path.exists(PASTA_DADOS):
        os.makedirs(PASTA_DADOS)

    # Ordem das colunas igual a da tabela LEITURA_SENSOR no Oracle
    campos = [
        "id_leitura",
        "data_hora",
        "umidade_solo",
        "umidade_ar",
        "temperatura",
        "ph_solo",
        "fosforo",
        "potassio",
        "status_bomba",
    ]

    with open(caminho, "w", newline="", encoding="utf-8") as arq:
        writer = csv.DictWriter(arq, fieldnames=campos)
        writer.writeheader()
        writer.writerows(leituras)

    print(f"  [OK] {len(leituras)} leituras geradas em: {caminho}")


# ========================== EXECUCAO ==========================

def main():
    print()
    print("  " + "=" * 60)
    print("  GERADOR DE DADOS DOS SENSORES DA FASE 2")
    print("  " + "=" * 60)
    print(f"  Total de leituras:   {TOTAL_LEITURAS}")
    print(f"  Intervalo:           {INTERVALO_MINUTOS} minutos")
    print(f"  Data inicial:        {DATA_INICIAL.strftime('%d/%m/%Y %H:%M')}")
    print("  " + "-" * 60)

    random.seed(42)  # reprodutibilidade
    leituras = gerar_dataset(TOTAL_LEITURAS)
    salvar_csv(leituras, ARQUIVO_SAIDA)

    # Estatisticas rapidas para validacao visual
    media_umidade = sum(l["umidade_solo"] for l in leituras) / len(leituras)
    bombas_ligadas = sum(1 for l in leituras if l["status_bomba"] == "LIGADA")
    print(f"  Umidade media do solo: {media_umidade:.2f}%")
    print(f"  Leituras com bomba ligada: {bombas_ligadas} ({bombas_ligadas/len(leituras)*100:.1f}%)")
    print("  " + "=" * 60)


if __name__ == "__main__":
    main()
