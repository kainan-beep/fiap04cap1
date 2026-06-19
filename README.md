# 🌾 FarmTech Solutions — Cap 01, Fase 4: Previsão Inteligente na Agricultura

PBL de Inteligência Artificial — FIAP

## Sobre o Projeto

A FarmTech Solutions é uma startup acadêmica fictícia da disciplina de IA na FIAP. O projeto evoluiu em fases:

- **Fase 2:** sistema IoT com ESP32 — sensores de umidade do solo, pH simulado por LDR, presença de Fósforo e Potássio por botões e bomba de irrigação controlada por relé.
- **Fase 3:** estruturação dos dados coletados em um banco relacional Oracle, hospedado nos servidores da FIAP, com dashboard de monitoramento em Streamlit.
- **Fase 4 (atual):** aplicação de Machine Learning (Scikit-Learn) sobre os mesmos dados para prever a próxima leitura de umidade do solo e a temperatura pela hora do dia, integrando essas previsões ao dashboard e sugerindo ações preventivas de irrigação.

Esta entrega (Fase 4) contempla:

- Pipeline de ML (`ml/treinar_modelos.py`): regressão múltipla para prever a umidade futura e comparação entre 3 abordagens de regressão (linear simples, linear cíclica, Random Forest) para prever temperatura
- Métricas de avaliação (MAE, MSE, RMSE, R²) calculadas e expostas tanto no terminal quanto no dashboard
- Nova aba **"Previsões com IA"** no dashboard Streamlit, com gráficos de real vs. previsto, comparação de modelos, heatmap de correlação e um simulador interativo que sugere lâmina de irrigação em tempo real
- Aba "Monitoramento" da Fase 3 mantida sem alterações

Itens herdados da Fase 3 (banco de dados estruturado):

- Modelagem da tabela `LEITURA_SENSOR` com restrições de integridade (`CHECK` constraints)
- Geração de dados realistas simulando o que o ESP32 da Fase 2 coletaria em campo
- Dois caminhos de importação: o **wizard** do Oracle SQL Developer e um **script Python** com `oracledb`
- Consultas SQL respondendo perguntas de negócio sobre os dados coletados

## Estrutura do Repositório

```
fiap03cap1/
├── README.md                       Este arquivo
├── requirements.txt
├── sql/
│   ├── 01_criar_tabela.sql         DDL da LEITURA_SENSOR (constraints + índice)
│   └── 02_consultas.sql            9 consultas SQL para o critério do barema (Fase 3)
├── scripts/
│   ├── gerar_dados_sensores.py     Simula a coleta da Fase 2 e gera o CSV
│   └── carga_oracle.py             Carga via Python (alternativa ao wizard)
├── ml/
│   ├── treinar_modelos.py          Pipeline de ML (Fase 4): treino + métricas
│   └── modelos/                    Gerado pelo script: .pkl dos modelos + metricas.json
├── dashboard/
│   └── app.py                      Dashboard Streamlit — abas Monitoramento (Fase 3) e Previsões com IA (Fase 4)
├── dados/
│   └── leituras_sensores.csv       Gerado pelos scripts
└── docs/
    └── imagens/                    Prints de tela para a documentação
```

## Modelo de Dados

A tabela `LEITURA_SENSOR` armazena uma leitura por linha, replicando o formato que o ESP32 da Fase 2 escreveria no Monitor Serial.

| Coluna         | Tipo          | Descrição                                  |
|----------------|---------------|--------------------------------------------|
| `id_leitura`   | NUMBER (PK)   | Identificador sequencial                   |
| `data_hora`    | VARCHAR2(19)  | Timestamp `YYYY-MM-DD HH24:MI:SS`          |
| `umidade_solo` | NUMBER(5,2)   | Umidade do solo em % (sensor capacitivo)   |
| `umidade_ar`   | NUMBER(5,2)   | Umidade do ar em % (DHT22)                 |
| `temperatura`  | NUMBER(5,2)   | Temperatura em °C (DHT22)                  |
| `ph_solo`      | NUMBER(4,2)   | pH entre 0 e 14 (LDR calibrado)            |
| `fosforo`      | VARCHAR2(3)   | `SIM` ou `NAO` (botão de presença)         |
| `potassio`     | VARCHAR2(3)   | `SIM` ou `NAO` (botão de presença)         |
| `status_bomba` | VARCHAR2(10)  | `LIGADA` ou `DESLIGADA` (relé)             |

As `CHECK constraints` garantem que apenas valores válidos sejam aceitos, evitando ruído na base. Um índice em `data_hora` acelera as consultas temporais usadas pela dashboard.

## Como Executar

### Pré-requisitos

```bash
pip install -r requirements.txt
```

Conteúdo do `requirements.txt`: `oracledb`, `streamlit`, `pandas`, `plotly`, `numpy`, `scikit-learn`, `joblib`.

### Passo 1 — Gerar os dados dos sensores

```bash
cd scripts
python gerar_dados_sensores.py
```

Saída esperada: 240 leituras em `dados/leituras_sensores.csv` cobrindo 5 dias com leituras a cada 30 minutos. A lógica de simulação preserva correlações realistas: a umidade do solo decai durante o dia, a bomba aciona quando cai abaixo de 30% e desliga acima de 70% (histerese), a temperatura tem ciclo diurno e a umidade do ar é inversamente proporcional à temperatura.

### Passo 2A — Carga via wizard do Oracle SQL Developer

Este é o caminho documentado no PDF da Fase 3:

1. Abrir o Oracle SQL Developer e estabelecer a conexão com `oracle.fiap.com.br:1521/ORCL` usando o RM como usuário (`RM570594`) e a data de nascimento `DDMMYY` como senha.
2. Expandir a conexão e localizar **Tabelas (Filtrado)**.
3. Botão direito → **Importar Dados**.
4. Selecionar o arquivo `dados/leituras_sensores.csv`.
5. No campo **Nome da Tabela**, informar `LEITURA_SENSOR` (sem espaços, máximo 30 caracteres, começando com letra).
6. Avançar mantendo todas as colunas, ajustando tipos se necessário (`NUMBER` para os numéricos, `VARCHAR2` para os textuais).
7. Clicar em **Finalizar** e aguardar a mensagem de sucesso.
8. Validar com `SELECT * FROM LEITURA_SENSOR;` (Ctrl+Enter executa).

> Os prints de cada etapa estão na pasta `docs/imagens/`.

### Passo 2B — Carga via Python (alternativa)

```bash
cd scripts
python carga_oracle.py
```

O script `carga_oracle.py` executa o ciclo completo: conexão, criação da tabela (caso não exista), limpeza com `TRUNCATE`, carga em lote via `executemany` (muito mais rápido que `INSERT` linha a linha) e validação com `SELECT COUNT(*)` e amostra dos 5 primeiros registros.

> **Atenção:** as credenciais não ficam mais no código (o repositório é público). Defina as variáveis de ambiente antes de executar:
> ```bash
> export ORACLE_USER=RM570594
> export ORACLE_PASSWORD=DDMMYY
> python carga_oracle.py
> ```

### Passo 3 — Consultas SQL

Abrir `sql/02_consultas.sql` no Oracle SQL Developer e executar bloco por bloco com Ctrl+Enter. As 9 consultas cobrem:

1. `SELECT *` (exigido pelo enunciado)
2. Contagem total de leituras
3. Estatísticas descritivas da umidade do solo (`MIN`, `MAX`, `AVG`, `STDDEV`)
4. Distribuição do acionamento da bomba com percentual
5. Leituras críticas (umidade < 30%)
6. Leituras com pH fora da faixa ideal (5,5–7,0)
7. Leituras com presença simultânea de P e K
8. Médias diárias com `GROUP BY` em `SUBSTR(data_hora, 1, 10)`
9. Últimas 10 leituras com `ROWNUM`

### Passo 4 — Treinar os modelos de Machine Learning (Fase 4)

```bash
python ml/treinar_modelos.py
```

Lê `dados/leituras_sensores.csv`, treina os dois modelos descritos na seção [Modelos de Machine Learning (Fase 4)](#modelos-de-machine-learning-fase-4), imprime as métricas no terminal e salva `modelo_umidade.pkl`, `modelo_temperatura.pkl` e `metricas.json` em `ml/modelos/`.

### Passo 5 — Dashboard

```bash
streamlit run dashboard/app.py
```

A dashboard abre em `http://localhost:8501` com duas abas.

**Aba "Monitoramento" (Fase 3, sem alterações):**

- **KPIs no topo:** umidade média do solo, temperatura média, pH médio e percentual de tempo com bomba ligada
- **Filtro de período** na barra lateral (compartilhado pelas duas abas)
- **Gráfico de umidade do solo no tempo** com linhas de referência (limites de acionamento da bomba) e faixa azul mostrando quando a bomba esteve ligada
- **pH do solo** com destaque visual para a faixa ideal (5,5–7,0)
- **Temperatura e umidade do ar** lado a lado
- **Donuts** com presença de Fósforo e Potássio
- **Tabela de sugestões de manejo** baseada na regra: umidade crítica → ligar bomba, dia quente e seco → considerar irrigação, pH fora da faixa → calagem ou gesso agrícola
- **Fallback para CSV local** caso o Oracle FIAP esteja indisponível (útil durante a gravação do vídeo)

**Aba "Previsões com IA" (Fase 4):**

- Treina os modelos (com cache) usando o mesmo pipeline de `ml/treinar_modelos.py` — não são números fixos, é o modelo real treinado dentro da sessão do Streamlit
- Métricas do Modelo 1 (MAE, MSE, RMSE, R²) e gráfico "Real vs. previsto" para a umidade futura
- Tabela comparando os 3 modelos de temperatura, com a melhor abordagem destacada
- Gráfico de temperatura real vs. prevista por hora do dia
- Heatmap de correlação entre as variáveis numéricas dos sensores
- **Simulador interativo:** sliders de umidade, temperatura, hora do dia e estado da bomba geram, em tempo real, a previsão de umidade futura, a temperatura prevista e uma lâmina de irrigação preventiva sugerida (mm)

## Modelos de Machine Learning (Fase 4)

| Modelo | Alvo | Abordagem | Métricas (conjunto de teste) |
|---|---|---|---|
| 1 — Umidade futura | Umidade do solo na próxima leitura (30 min à frente) | Regressão linear múltipla (`umidade_solo`, `bomba_bin`, `hora`, `temperatura`) | MAE ≈ 0,77 · MSE ≈ 0,86 · RMSE ≈ 0,93 · **R² ≈ 0,994** |
| 2 — Temperatura pela hora | Temperatura | 3 abordagens comparadas: linear simples, linear com hora cíclica (seno/cosseno), Random Forest | linear_simples R² ≈ 0,13 · **linear_ciclico R² ≈ 0,73 (escolhido)** · random_forest R² ≈ 0,55 |

**Por que pH não foi usado como alvo de regressão:** testamos prever `ph_solo` a partir das demais variáveis e o R² ficou negativo (pior que prever a média). No gerador de dados da Fase 3, o pH é sorteado de forma aleatória e independente das demais variáveis — não há padrão real para o modelo aprender. Substituímos por temperatura, que tem um ciclo diário real e permite comparar regressão linear x não linear, como pedido no enunciado.

Detalhes da implementação em [`ml/treinar_modelos.py`](ml/treinar_modelos.py).

#### Credenciais do Oracle (dashboard)

O dashboard lê as credenciais de `.streamlit/secrets.toml` (arquivo local, fora do controle de versão — veja `.streamlit/secrets.toml.example` para o formato). **Para avaliação, nenhuma configuração é necessária:** se o arquivo de secrets não existir, o dashboard cai automaticamente para o CSV local em `dados/leituras_sensores.csv` e funciona normalmente, exibindo apenas um aviso de que está usando dados locais.

Caso queira testar a conexão real com o Oracle FIAP, crie `.streamlit/secrets.toml` com suas próprias credenciais:
```toml
[oracle]
user = "RM000000"
password = "DDMMYY"
dsn = "oracle.fiap.com.br:1521/ORCL"
```

## Vídeos

- Fase 3: https://youtu.be/1BKev5pfFhQ
- Fase 4 — Parte 1 (Integração ML + Streamlit): https://youtu.be/xrVj5sZbpmU
- Fase 4 — Parte 2 (Pipeline de Machine Learning): https://youtu.be/iLRs0dH_GrA

## Integrantes

- Kainan Bilibio Aguiar — RM570594
- Guilherme C. Ávila — RM571294

## Continuidade com a Fase 2

O modelo de dados da Fase 3 foi desenhado para representar exatamente o que o sistema IoT desenvolvido na Fase 2 produziria em produção. Cada coluna mapeia para um componente físico do circuito ESP32:

| Coluna           | Componente da Fase 2                  |
|------------------|---------------------------------------|
| `umidade_solo`   | Sensor capacitivo de umidade do solo  |
| `umidade_ar`     | DHT22 — pino de umidade               |
| `temperatura`    | DHT22 — pino de temperatura           |
| `ph_solo`        | LDR (analogRead 0-4095 → escala 0-14) |
| `fosforo`        | Botão tátil simulando presença        |
| `potassio`       | Botão tátil simulando presença        |
| `status_bomba`   | Relé controlando a bomba              |

## Referências

- Oracle Database 19c — Documentação técnica
- python-oracledb (Oracle, 2025)
- Streamlit Documentation
- Scikit-Learn Documentation
- EMBRAPA — Agricultura Digital
