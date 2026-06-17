"""
app.py - Dashboard FarmTech Solutions (Fase 3 + Fase 4)

Visualizacao interativa das leituras dos sensores, organizada em duas
abas:

  - Monitoramento (Fase 3): niveis de umidade, P, K e pH, status da
    irrigacao e sugestoes de manejo baseadas em regras fixas.
  - Previsoes com IA (Fase 4): modelos de regressao (Scikit-Learn)
    treinados sobre os mesmos dados, com metricas de desempenho,
    grafico de correlacao e previsoes interativas em tempo real.

Funcionamento:
  1. Tenta conectar no Oracle FIAP.
  2. Se a conexao falhar, faz fallback automatico para o CSV gerado
     em ../dados/leituras_sensores.csv (essencial para gravacao do
     video caso a rede da FIAP esteja indisponivel).

Execucao:
    pip install -r ../requirements.txt
    streamlit run app.py
"""

import os
import sys

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

try:
    import oracledb
    ORACLE_DISPONIVEL = True
except ImportError:
    ORACLE_DISPONIVEL = False

# Permite importar o pacote ml/ (pipeline da Fase 4), pasta irma de
# dashboard/ dentro do repositorio.
sys.path.append(os.path.join(os.path.dirname(__file__), ".."))
from ml.treinar_modelos import (
    carregar_e_preparar_dados,
    treinar_modelo_umidade,
    treinar_modelos_temperatura,
)


# ========================== CONFIGURACAO ==========================

def _carregar_config_db() -> dict:
    """Le as credenciais do Oracle de st.secrets ou de variaveis de ambiente.

    Nunca deixamos usuario/senha hardcoded no codigo-fonte, pois o
    repositorio e publico.
    """
    if "oracle" in st.secrets:
        return {
            "user": st.secrets["oracle"]["user"],
            "password": st.secrets["oracle"]["password"],
            "dsn": st.secrets["oracle"].get("dsn", "oracle.fiap.com.br:1521/ORCL"),
        }
    return {
        "user": os.environ.get("ORACLE_USER", ""),
        "password": os.environ.get("ORACLE_PASSWORD", ""),
        "dsn": os.environ.get("ORACLE_DSN", "oracle.fiap.com.br:1521/ORCL"),
    }


CONFIG_DB = _carregar_config_db()

CAMINHO_CSV_FALLBACK = os.path.join(
    os.path.dirname(__file__), "..", "dados", "leituras_sensores.csv"
)

# Limites da logica de irrigacao (mesmos do ESP32 da Fase 2)
UMIDADE_MIN_IRRIGAR = 30.0
UMIDADE_MAX_DESLIGAR = 70.0
PH_IDEAL_MIN = 5.5
PH_IDEAL_MAX = 7.0

# Estimativa de lamina de irrigacao (Fase 4): ponto central da faixa segura
# (entre UMIDADE_MIN_IRRIGAR e UMIDADE_MAX_DESLIGAR) e uma profundidade de
# referencia. A literatura agronomica situa a profundidade efetiva do
# sistema radicular da cana-de-acucar entre 0,45 m e 0,6 m, concentrando
# ~90% da extracao de agua nos primeiros 0,6 m (EMBRAPA). Usamos uma camada
# de manejo mais conservadora (0,3 m) -- a faixa superficial mais ativa,
# onde o sensor capacitivo de umidade tipicamente atua -- em vez do
# perfil radicular completo, evitando sobrestimar a lamina necessaria.
UMIDADE_ALVO = (UMIDADE_MIN_IRRIGAR + UMIDADE_MAX_DESLIGAR) / 2  # 50.0%
PROFUNDIDADE_REFERENCIA_MM = 300.0

# Nomes de exibicao das colunas (apenas para as tabelas do dashboard --
# as colunas internas permanecem em snake_case sem acento).
COLUNAS_DISPLAY = {
    "id_leitura": "ID leitura",
    "data_hora": "Data/Hora",
    "umidade_solo": "Umidade do solo (%)",
    "umidade_ar": "Umidade do ar (%)",
    "temperatura": "Temperatura (°C)",
    "ph_solo": "pH do solo",
    "fosforo": "Fósforo",
    "potassio": "Potássio",
    "status_bomba": "Status da bomba",
    "sugestao": "Sugestão",
}


# ========================== CARGA DE DADOS ==========================

@st.cache_data(ttl=60)
def carregar_do_oracle() -> pd.DataFrame:
    """Le todas as leituras do Oracle e retorna um DataFrame."""
    if not ORACLE_DISPONIVEL:
        raise RuntimeError("pacote oracledb nao instalado")

    conn = oracledb.connect(**CONFIG_DB)
    sql = """
        SELECT id_leitura, data_hora, umidade_solo, umidade_ar,
               temperatura, ph_solo, fosforo, potassio, status_bomba
        FROM leitura_sensor
        ORDER BY data_hora
    """
    df = pd.read_sql(sql, conn)
    conn.close()
    df.columns = [c.lower() for c in df.columns]
    df["data_hora"] = pd.to_datetime(df["data_hora"])
    return df


@st.cache_data(ttl=60)
def carregar_do_csv() -> pd.DataFrame:
    """Fallback: le o CSV gerado pelo gerar_dados_sensores.py."""
    df = pd.read_csv(CAMINHO_CSV_FALLBACK)
    df["data_hora"] = pd.to_datetime(df["data_hora"])
    return df


def carregar_dados() -> tuple:
    """Tenta Oracle, cai para CSV se necessario. Retorna (df, fonte)."""
    try:
        return carregar_do_oracle(), "Oracle FIAP"
    except Exception as erro:
        st.warning(
            f"Não foi possível conectar ao Oracle ({erro}). "
            f"Usando dados locais (CSV) como alternativa."
        )
        return carregar_do_csv(), "CSV local"


@st.cache_resource(show_spinner="Treinando modelos de regressão...")
def carregar_modelos_ia():
    """Treina (com cache) os dois modelos da Fase 4 usando o pipeline de
    ml/treinar_modelos.py -- mesmo codigo do script standalone, reaproveitado
    aqui para a integracao com o dashboard."""
    df_ml = carregar_e_preparar_dados()
    modelo_umidade, metricas_umidade, y_te_umid, pred_umid = treinar_modelo_umidade(df_ml)
    modelo_temp, melhor_temp, resultados_temp, extras_temp = treinar_modelos_temperatura(df_ml)
    return {
        "modelo_umidade": modelo_umidade,
        "metricas_umidade": metricas_umidade,
        "y_te_umidade": y_te_umid,
        "pred_umidade": pred_umid,
        "modelo_temp": modelo_temp,
        "melhor_temp": melhor_temp,
        "resultados_temp": resultados_temp,
        "extras_temp": extras_temp,
    }


# ========================== LOGICA DE NEGOCIO ==========================

def gerar_sugestao_irrigacao(linha: pd.Series) -> str:
    """Retorna sugestao textual baseada em umidade, temperatura e pH."""
    if linha["umidade_solo"] < UMIDADE_MIN_IRRIGAR:
        return "Ligar bomba: umidade do solo crítica"
    if linha["umidade_solo"] > UMIDADE_MAX_DESLIGAR:
        return "Desligar bomba: solo saturado"
    if linha["temperatura"] > 30 and linha["umidade_solo"] < 50:
        return "Considerar irrigação: dia quente e seco"
    if linha["ph_solo"] < PH_IDEAL_MIN:
        return "pH baixo: avaliar calagem"
    if linha["ph_solo"] > PH_IDEAL_MAX:
        return "pH alto: avaliar gesso agrícola"
    return "Condições normais: manter monitoramento"


def gerar_sugestao_preventiva(umidade_prevista: float) -> str:
    """Sugestao baseada na umidade PREVISTA pelo modelo de ML para a proxima
    leitura (30 min a frente) -- acao preventiva, e nao reativa como em
    gerar_sugestao_irrigacao."""
    if umidade_prevista < UMIDADE_MIN_IRRIGAR:
        return "🔴 Irrigar de forma preventiva: tendência de cair para nível crítico"
    if umidade_prevista > UMIDADE_MAX_DESLIGAR:
        return "🔵 Manter bomba desligada: solo deve continuar saturado"
    return "🟢 Sem ação necessária: umidade prevista dentro da faixa ideal"


def calcular_lamina_irrigacao_mm(umidade_prevista: float) -> float:
    """Estima a lamina de irrigacao (mm) a partir do deficit entre a umidade
    PREVISTA pelo Modelo 1 e a umidade-alvo (UMIDADE_ALVO), convertido para
    profundidade de agua usando PROFUNDIDADE_REFERENCIA_MM.

    E uma aproximacao didatica para transformar a previsao em uma grandeza
    fisica (mm) -- nao substitui um balanco hidrico de precisao, que exigiria
    evapotranspiracao, textura do solo e curva de retencao de agua reais."""
    deficit_percentual = max(0.0, UMIDADE_ALVO - umidade_prevista)
    lamina_mm = deficit_percentual * PROFUNDIDADE_REFERENCIA_MM / 100
    return round(lamina_mm, 1)


# ========================== UI ==========================

st.set_page_config(
    page_title="FarmTech Solutions - Dashboard",
    page_icon="🌾",
    layout="wide",
)

st.title("🌾 FarmTech Solutions — Monitoramento e Previsão Agrícola")
st.caption("Dashboard interativo dos sensores IoT — Fase 3 e Fase 4 (PBL FIAP)")

df, fonte = carregar_dados()

# Barra lateral: filtros (compartilhados pelas duas abas)
st.sidebar.header("Filtros")
st.sidebar.markdown(f"**Fonte de dados:** `{fonte}`")
st.sidebar.markdown(f"**Total de leituras:** {len(df)}")

data_min = df["data_hora"].min().date()
data_max = df["data_hora"].max().date()
data_inicio, data_fim = st.sidebar.date_input(
    "Período",
    value=(data_min, data_max),
    min_value=data_min,
    max_value=data_max,
)

mascara = (df["data_hora"].dt.date >= data_inicio) & \
          (df["data_hora"].dt.date <= data_fim)
df_filt = df.loc[mascara].copy()

if df_filt.empty:
    st.warning("Nenhuma leitura no período selecionado.")
    st.stop()

tab1, tab2 = st.tabs(["📊 Monitoramento (Fase 3)", "🔮 Previsões com IA (Fase 4)"])

# ===================================================================
# ABA 1 - MONITORAMENTO (conteudo original da Fase 3, sem alteracoes)
# ===================================================================
with tab1:
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Umidade média do solo", f"{df_filt['umidade_solo'].mean():.1f}%")
    col2.metric("Temperatura média", f"{df_filt['temperatura'].mean():.1f}°C")
    col3.metric("pH médio", f"{df_filt['ph_solo'].mean():.2f}")
    col4.metric(
        "Tempo com bomba ligada",
        f"{(df_filt['status_bomba'] == 'LIGADA').mean() * 100:.1f}%",
    )

    st.divider()

    st.subheader("Umidade do solo e acionamento da bomba")
    fig_umidade = px.line(
        df_filt, x="data_hora", y="umidade_solo",
        title="Umidade do solo ao longo do tempo (%)",
        labels={"data_hora": "Data/Hora", "umidade_solo": "Umidade (%)"},
    )
    fig_umidade.add_hline(
        y=UMIDADE_MIN_IRRIGAR, line_dash="dot", line_color="red",
        annotation_text="Limite mínimo (liga bomba)",
    )
    fig_umidade.add_hline(
        y=UMIDADE_MAX_DESLIGAR, line_dash="dot", line_color="green",
        annotation_text="Limite máximo (desliga bomba)",
    )

    df_bomba = df_filt.copy()
    df_bomba["bomba_num"] = (df_bomba["status_bomba"] == "LIGADA").astype(int) * 100
    fig_umidade.add_scatter(
        x=df_bomba["data_hora"], y=df_bomba["bomba_num"],
        mode="lines", name="Bomba LIGADA (faixas)",
        line=dict(color="rgba(0, 100, 255, 0.15)", width=0),
        fill="tozeroy", fillcolor="rgba(0, 100, 255, 0.10)",
    )
    st.plotly_chart(fig_umidade, width="stretch")

    col_a, col_b = st.columns(2)

    with col_a:
        st.subheader("pH do solo")
        fig_ph = px.line(
            df_filt, x="data_hora", y="ph_solo",
            labels={"data_hora": "Data/Hora", "ph_solo": "pH"},
        )
        fig_ph.add_hrect(
            y0=PH_IDEAL_MIN, y1=PH_IDEAL_MAX,
            fillcolor="green", opacity=0.15, line_width=0,
            annotation_text="Faixa ideal", annotation_position="top left",
        )
        st.plotly_chart(fig_ph, width="stretch")

    with col_b:
        st.subheader("Temperatura e umidade do ar")
        fig_temp = px.line(
            df_filt, x="data_hora", y=["temperatura", "umidade_ar"],
            labels={"data_hora": "Data/Hora", "value": "Valor", "variable": "Sensor"},
        )
        st.plotly_chart(fig_temp, width="stretch")

    col_c, col_d = st.columns(2)

    with col_c:
        st.subheader("Presença de Fósforo (P)")
        contagem_p = df_filt["fosforo"].value_counts().reset_index()
        contagem_p.columns = ["presença", "qtd"]
        fig_p = px.pie(
            contagem_p, names="presença", values="qtd", hole=0.5,
            color="presença", color_discrete_map={"SIM": "#2ecc71", "NAO": "#e74c3c"},
        )
        st.plotly_chart(fig_p, width="stretch")

    with col_d:
        st.subheader("Presença de Potássio (K)")
        contagem_k = df_filt["potassio"].value_counts().reset_index()
        contagem_k.columns = ["presença", "qtd"]
        fig_k = px.pie(
            contagem_k, names="presença", values="qtd", hole=0.5,
            color="presença", color_discrete_map={"SIM": "#3498db", "NAO": "#e74c3c"},
        )
        st.plotly_chart(fig_k, width="stretch")

    st.divider()

    st.subheader("💡 Sugestões de manejo (últimas leituras)")
    df_recente = df_filt.tail(10).copy()
    df_recente["sugestao"] = df_recente.apply(gerar_sugestao_irrigacao, axis=1)
    st.dataframe(
        df_recente[[
            "data_hora", "umidade_solo", "temperatura", "ph_solo",
            "status_bomba", "sugestao",
        ]].rename(columns=COLUNAS_DISPLAY),
        width="stretch",
        hide_index=True,
    )

    with st.expander("Ver todas as leituras filtradas"):
        st.dataframe(df_filt.rename(columns=COLUNAS_DISPLAY), width="stretch", hide_index=True)

# ===================================================================
# ABA 2 - PREVISOES COM IA (Fase 4)
# ===================================================================
with tab2:
    st.caption(
        "Modelos de regressão (Scikit-Learn) treinados sobre as leituras "
        "carregadas. Pipeline completo em ml/treinar_modelos.py."
    )

    ia = carregar_modelos_ia()

    # ---------- Modelo 1: umidade futura ----------
    st.subheader("Modelo 1 — previsão da próxima leitura de umidade do solo")
    st.caption(
        "Regressão linear múltipla. Em vez de reagir somente à leitura atual "
        "(Fase 3), prevê a umidade 30 minutos à frente, permitindo calcular "
        "uma lâmina de irrigação preventiva (mm) — ver simulador no final desta aba."
    )
    m1 = ia["metricas_umidade"]
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("MAE", f"{m1['mae']:.2f} p.p.")
    c2.metric("MSE", f"{m1['mse']:.2f}")
    c3.metric("RMSE", f"{m1['rmse']:.2f} p.p.")
    c4.metric("R²", f"{m1['r2']:.3f}")

    fig_real_prev = px.scatter(
        x=ia["y_te_umidade"], y=ia["pred_umidade"],
        labels={"x": "Umidade real (%)", "y": "Umidade prevista (%)"},
        title="Real vs. previsto — conjunto de teste",
    )
    minimo = float(min(ia["y_te_umidade"].min(), ia["pred_umidade"].min()))
    maximo = float(max(ia["y_te_umidade"].max(), ia["pred_umidade"].max()))
    fig_real_prev.add_trace(go.Scatter(
        x=[minimo, maximo], y=[minimo, maximo],
        mode="lines", line=dict(dash="dot", color="gray"),
        name="Previsão perfeita",
    ))
    st.plotly_chart(fig_real_prev, width="stretch")

    st.divider()

    # ---------- Modelo 2: temperatura pela hora ----------
    st.subheader("Modelo 2 — previsão de temperatura pela hora do dia")
    st.caption(
        "Comparação entre regressão linear simples, regressão linear com "
        "atributos cíclicos (seno/cosseno da hora) e Random Forest (não linear)."
    )
    linhas_comp = []
    for nome, m in ia["resultados_temp"].items():
        linhas_comp.append({
            "Modelo": nome,
            "R²": m["r2"],
            "MAE": m["mae"],
            "RMSE": m["rmse"],
            "Descrição": m["descricao"],
        })
    tabela_comp = pd.DataFrame(linhas_comp).set_index("Modelo")
    st.dataframe(
        tabela_comp.style.highlight_max(subset=["R²"], color="#2ecc7133"),
        width="stretch",
    )
    st.caption(f"Modelo escolhido para o dashboard: **{ia['melhor_temp']}**")

    extras = ia["extras_temp"]
    fig_temp_fit = px.scatter(
        x=extras["hora_teste"], y=extras["y_teste"],
        labels={"x": "Hora do dia", "y": "Temperatura (°C)"},
        title="Temperatura real (pontos) vs. prevista (linha) por hora do dia",
    )
    ordem = np.argsort(extras["hora_teste"].values)
    fig_temp_fit.add_trace(go.Scatter(
        x=extras["hora_teste"].values[ordem],
        y=np.array(extras["previsao_melhor"])[ordem],
        mode="lines", name="Previsto", line=dict(color="orange"),
    ))
    st.plotly_chart(fig_temp_fit, width="stretch")

    st.divider()

    # ---------- Correlacao entre variaveis ----------
    st.subheader("Correlação entre as variáveis dos sensores")
    corr = df_filt[["umidade_solo", "umidade_ar", "temperatura", "ph_solo"]].corr()
    fig_corr = px.imshow(
        corr, text_auto=".2f", color_continuous_scale="RdBu_r", zmin=-1, zmax=1,
        labels=dict(color="Correlação"),
    )
    st.plotly_chart(fig_corr, width="stretch")
    st.caption(
        "O pH do solo não mostra correlação relevante com as demais variáveis "
        "nesta base de dados — por isso ele não foi usado como alvo de regressão "
        "(o R² ficou negativo nos testes)."
    )

    st.divider()

    # ---------- Simulador interativo ----------
    st.subheader("🔮 Simular um cenário e prever em tempo real")
    sc1, sc2, sc3, sc4 = st.columns(4)
    sim_umidade = sc1.slider("Umidade do solo atual (%)", 10.0, 95.0, 50.0)
    sim_temp = sc2.slider("Temperatura atual (°C)", 15.0, 35.0, 25.0)
    sim_hora = sc3.slider("Hora do dia", 0.0, 23.5, 12.0, step=0.5)
    sim_bomba = sc4.selectbox("Bomba agora", ["DESLIGADA", "LIGADA"])

    entrada_umidade = pd.DataFrame([{
        "umidade_solo": sim_umidade,
        "bomba_bin": 1 if sim_bomba == "LIGADA" else 0,
        "hora": sim_hora,
        "temperatura": sim_temp,
    }])
    umidade_prevista = float(ia["modelo_umidade"].predict(entrada_umidade)[0])

    sin_h = np.sin(2 * np.pi * sim_hora / 24)
    cos_h = np.cos(2 * np.pi * sim_hora / 24)
    if ia["melhor_temp"] == "linear_ciclico":
        entrada_temp = pd.DataFrame([{"hora_sin": sin_h, "hora_cos": cos_h}])
    else:
        entrada_temp = pd.DataFrame([{"hora": sim_hora}])
    temperatura_prevista = float(ia["modelo_temp"].predict(entrada_temp)[0])
    lamina_mm = calcular_lamina_irrigacao_mm(umidade_prevista)

    r1, r2, r3 = st.columns(3)
    r1.metric("Umidade prevista (próxima leitura)", f"{umidade_prevista:.1f}%")
    r2.metric("Temperatura prevista (pela hora)", f"{temperatura_prevista:.1f}°C")
    r3.metric("Lâmina de irrigação sugerida", f"{lamina_mm:.1f} mm")

    st.info(gerar_sugestao_preventiva(umidade_prevista))
    st.caption(
        "Lâmina estimada a partir do déficit entre a umidade prevista e a "
        "umidade-alvo (50%, ponto central da faixa segura), considerando uma "
        "camada de manejo de referência de 0,3 m. É uma aproximação didática, "
        "não um balanço hídrico de precisão."
    )

st.caption(
    "FarmTech Solutions • PBL FIAP - Fase 3 e Fase 4 • "
    "Kainan B. Aguiar (RM570594) & Guilherme C. Avila (RM571294)"
)
