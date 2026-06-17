"""
treinar_modelos.py - Pipeline de Machine Learning (Fase 4)

Treina e avalia os modelos de regressao usados pelo dashboard:

  1. Previsao da PROXIMA leitura de umidade do solo (regressao multipla)
     - usa a leitura atual de umidade, status da bomba, hora do dia e
       temperatura para prever a umidade 30 minutos a frente. Isso permite
       sugerir irrigacao de forma PREVENTIVA (antes da umidade ficar
       critica), em vez de apenas reagir ao valor atual, como era feito
       na Fase 3.

  2. Previsao de temperatura a partir da hora do dia, comparando tres
     abordagens: regressao linear simples (so a hora bruta), regressao
     linear com atributos ciclicos (seno/cosseno da hora) e Random Forest
     (modelo nao linear). Mostra na pratica o impacto de feature
     engineering e de modelos nao lineares quando a relacao nao e uma
     linha reta.

Por que NAO usamos pH como alvo de regressao:
  Testamos prever ph_solo a partir das demais variaveis (umidade,
  temperatura, fosforo, potassio) e o R2 ficou NEGATIVO (-0.24) -- pior
  do que simplesmente prever a media. Isso acontece porque, no gerador
  de dados da Fase 3 (scripts/gerar_dados_sensores.py), o pH e sorteado
  de forma totalmente aleatoria e independente das demais variaveis.
  Nao existe relacao real para o modelo aprender, entao manter pH como
  alvo daria uma demonstracao fraca e poderia ser questionado no video.
  Substituimos por temperatura, que tem um padrao real (ciclo diario) e
  ainda permite a comparacao linear x nao linear pedida no enunciado.

Saida (pasta ml/modelos/):
  - modelo_umidade.pkl       (regressor da proxima leitura de umidade)
  - modelo_temperatura.pkl   (melhor modelo entre os tres comparados)
  - metricas.json            (todas as metricas, usadas pelo dashboard)

Execucao:
    pip install -r requirements.txt
    python ml/treinar_modelos.py
"""

import os
import json

import joblib
import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestRegressor
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split

CAMINHO_CSV = os.path.join(
    os.path.dirname(__file__), "..", "dados", "leituras_sensores.csv"
)
PASTA_MODELOS = os.path.join(os.path.dirname(__file__), "modelos")
SEED = 42


# ========================== PREPARACAO DOS DADOS ==========================

def carregar_e_preparar_dados() -> pd.DataFrame:
    """Le o CSV da Fase 3 e cria as colunas derivadas usadas pelos modelos."""
    df = pd.read_csv(CAMINHO_CSV)
    df["data_hora"] = pd.to_datetime(df["data_hora"])
    df = df.sort_values("data_hora").reset_index(drop=True)

    # Hora do dia em formato decimal (ex.: 14h30 -> 14.5)
    df["hora"] = df["data_hora"].dt.hour + df["data_hora"].dt.minute / 60
    # Transformacao ciclica: evita que 23h e 00h pareçam "distantes" pro modelo
    df["hora_sin"] = np.sin(2 * np.pi * df["hora"] / 24)
    df["hora_cos"] = np.cos(2 * np.pi * df["hora"] / 24)

    df["bomba_bin"] = (df["status_bomba"] == "LIGADA").astype(int)
    df["fosforo_bin"] = (df["fosforo"] == "SIM").astype(int)
    df["potassio_bin"] = (df["potassio"] == "SIM").astype(int)

    # Alvo do Modelo 1: umidade da PROXIMA leitura (30 minutos depois)
    df["umidade_solo_prox"] = df["umidade_solo"].shift(-1)

    return df


def metrica_dict(y_true, y_pred) -> dict:
    """Calcula MAE, MSE, RMSE e R2 e devolve como dicionario (p/ JSON)."""
    mse = float(mean_squared_error(y_true, y_pred))
    return {
        "mae": round(float(mean_absolute_error(y_true, y_pred)), 3),
        "mse": round(mse, 3),
        "rmse": round(mse ** 0.5, 3),
        "r2": round(float(r2_score(y_true, y_pred)), 3),
    }


# ========================== MODELO 1: UMIDADE FUTURA ==========================

def treinar_modelo_umidade(df: pd.DataFrame) -> tuple:
    """Regressao multipla: preve a umidade do solo na proxima leitura."""
    dados = df.dropna(subset=["umidade_solo_prox"])
    features = ["umidade_solo", "bomba_bin", "hora", "temperatura"]
    X = dados[features]
    y = dados["umidade_solo_prox"]

    X_tr, X_te, y_tr, y_te = train_test_split(
        X, y, test_size=0.2, random_state=SEED
    )
    modelo = LinearRegression().fit(X_tr, y_tr)
    pred = modelo.predict(X_te)

    metricas = metrica_dict(y_te, pred)
    metricas["features"] = features
    metricas["descricao"] = (
        "Regressão linear múltipla - prevê a umidade do solo na "
        "próxima leitura (30 min a frente)"
    )
    # y_te e pred tambem sao devolvidos para o grafico "real vs previsto"
    # ser reaproveitado pelo dashboard sem duplicar o treino.
    return modelo, metricas, y_te, pred


# ===================== MODELO 2: TEMPERATURA (COMPARACAO) =====================

def treinar_modelos_temperatura(df: pd.DataFrame) -> tuple:
    """Compara 3 abordagens de regressao para prever temperatura pela hora."""
    X_tr, X_te, y_tr, y_te = train_test_split(
        df[["hora", "hora_sin", "hora_cos"]], df["temperatura"],
        test_size=0.2, random_state=SEED,
    )

    resultados = {}

    # 2a) Linear simples - so a hora bruta (mostra a limitacao)
    m_linear = LinearRegression().fit(X_tr[["hora"]], y_tr)
    resultados["linear_simples"] = metrica_dict(y_te, m_linear.predict(X_te[["hora"]]))
    resultados["linear_simples"]["descricao"] = (
        "Regressão linear simples - só a hora bruta como atributo"
    )

    # 2b) Linear com atributos ciclicos (seno/cosseno da hora)
    m_ciclico = LinearRegression().fit(X_tr[["hora_sin", "hora_cos"]], y_tr)
    resultados["linear_ciclico"] = metrica_dict(
        y_te, m_ciclico.predict(X_te[["hora_sin", "hora_cos"]])
    )
    resultados["linear_ciclico"]["descricao"] = (
        "Regressão linear - hora transformada em seno/cosseno "
        "(capta o ciclo diário)"
    )

    # 2c) Random Forest (nao linear) - so a hora bruta
    m_rf = RandomForestRegressor(n_estimators=200, random_state=SEED)
    m_rf.fit(X_tr[["hora"]], y_tr)
    resultados["random_forest"] = metrica_dict(y_te, m_rf.predict(X_te[["hora"]]))
    resultados["random_forest"]["descricao"] = (
        "Random Forest (não linear) - só a hora bruta como atributo"
    )

    melhor_nome = max(resultados, key=lambda k: resultados[k]["r2"])
    modelos = {
        "linear_simples": m_linear,
        "linear_ciclico": m_ciclico,
        "random_forest": m_rf,
    }
    previsoes = {
        "linear_simples": m_linear.predict(X_te[["hora"]]),
        "linear_ciclico": m_ciclico.predict(X_te[["hora_sin", "hora_cos"]]),
        "random_forest": m_rf.predict(X_te[["hora"]]),
    }
    # X_te["hora"], y_te e as previsoes do melhor modelo sao devolvidos
    # para o grafico "temperatura real vs prevista" no dashboard.
    extras = {"hora_teste": X_te["hora"], "y_teste": y_te, "previsao_melhor": previsoes[melhor_nome]}
    return modelos[melhor_nome], melhor_nome, resultados, extras


# ========================== EXECUCAO ==========================

def main():
    print("=" * 64)
    print("FASE 4 - TREINAMENTO DOS MODELOS DE REGRESSAO")
    print("=" * 64)

    os.makedirs(PASTA_MODELOS, exist_ok=True)
    df = carregar_e_preparar_dados()
    print(f"\nDados carregados: {len(df)} leituras")

    print("\n--- Modelo 1: previsao da proxima leitura de umidade do solo ---")
    modelo_umidade, metricas_umidade, _, _ = treinar_modelo_umidade(df)
    for chave in ("mae", "mse", "rmse", "r2"):
        print(f"  {chave.upper()}: {metricas_umidade[chave]}")

    print("\n--- Modelo 2: previsao de temperatura a partir da hora ---")
    modelo_temp, melhor_temp, resultados_temp, _ = treinar_modelos_temperatura(df)
    for nome, m in resultados_temp.items():
        marca = "  <-- escolhido para o dashboard" if nome == melhor_temp else ""
        print(f"  {nome}: R2={m['r2']:.3f}  MAE={m['mae']:.3f}  RMSE={m['rmse']:.3f}{marca}")

    joblib.dump(modelo_umidade, os.path.join(PASTA_MODELOS, "modelo_umidade.pkl"))
    joblib.dump(modelo_temp, os.path.join(PASTA_MODELOS, "modelo_temperatura.pkl"))

    metricas_finais = {
        "modelo_umidade": metricas_umidade,
        "modelo_temperatura": {
            "escolhido": melhor_temp,
            "comparacao": resultados_temp,
        },
    }
    caminho_json = os.path.join(PASTA_MODELOS, "metricas.json")
    with open(caminho_json, "w", encoding="utf-8") as f:
        json.dump(metricas_finais, f, ensure_ascii=False, indent=2)

    print(f"\nModelos salvos em: {PASTA_MODELOS}")
    print(f"Metricas salvas em: {caminho_json}")
    print("=" * 64)


if __name__ == "__main__":
    main()
