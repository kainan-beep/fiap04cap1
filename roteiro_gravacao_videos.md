# Roteiro de Gravação — Vídeos da Fase 4

Os dois vídeos têm limite de **5 minutos**. Ensaie pelo menos uma vez cronometrando — é fácil passar do tempo na parte de demonstração do dashboard.

Dica de gravação: rode `python ml/treinar_modelos.py` e `streamlit run dashboard/app.py` **antes** de começar a gravar, pra não perder tempo de vídeo esperando o terminal/navegador abrir. Você pode deixar as duas janelas já abertas e só alternar entre elas.

---

## Vídeo 1 — Parte 1: Integração ML + Streamlit (até 5 min)

**Foco:** provar que o modelo treinado está de fato conectado à interface — não são números fixos digitados no código.

### 0:00–0:25 — Abertura
Diga seu nome, RM, e o que vai mostrar.

> "Nessa parte vou mostrar como integramos o modelo de regressão treinado em Scikit-Learn dentro do dashboard em Streamlit da FarmTech Solutions."

### 0:25–1:15 — Arquitetura e bibliotecas
Mostre rapidamente a estrutura de pastas (`dashboard/`, `ml/`, `dados/`). Abra o `dashboard/app.py` e aponte a linha:

```python
from ml.treinar_modelos import (
    carregar_e_preparar_dados,
    treinar_modelo_umidade,
    treinar_modelos_temperatura,
)
```

> "O dashboard importa direto as funções do pipeline de treino. Ou seja, ele não está lendo um número fixo — ele está treinando e usando o modelo de verdade, dentro da própria sessão do Streamlit."

Cite as bibliotecas: Scikit-Learn (regressão e métricas), pandas/numpy (tratamento de dados), Streamlit + Plotly (interface e gráficos).

### 1:15–3:15 — Demonstração do dashboard
Abra o navegador. Passe rápido pela aba "Monitoramento" (uma frase: "essa aba é da Fase 3, sem alterações"). Foque o tempo na aba **"Previsões com IA"**:
- Mostre as 4 métricas do Modelo 1 (MAE, MSE, RMSE, R²)
- Mostre o gráfico "Real vs. previsto"
- Mostre a tabela comparando os 3 modelos de temperatura
- Mostre o heatmap de correlação

> "Aqui temos as métricas de desempenho, o gráfico de correlação entre as variáveis dos sensores, e a comparação entre diferentes abordagens de regressão para a temperatura."

### 3:15–4:30 — Simulador em tempo real
Mexa nos sliders ao vivo: baixe a umidade e mostre a lâmina de irrigação subindo e a sugestão mudando de cor.

> "Esse simulador gera previsões em tempo real: ao mudar a umidade atual, o modelo recalcula a previsão pra próxima leitura e sugere uma ação — incluindo uma estimativa de lâmina de irrigação em milímetros."

### 4:30–5:00 — Encerramento
Resuma em 1–2 frases o que foi mostrado e encerre.

---

## Vídeo 2 — Parte 2: Pipeline de Machine Learning (até 5 min)

**Foco:** tratamento de dados, treinamento, validação, métricas e interpretação dos resultados.

### 0:00–0:20 — Abertura
Nome, RM, e o que vai mostrar nessa parte.

### 0:20–1:00 — O dataset
Mostre o CSV ou um print do dataframe: 240 leituras, as colunas (umidade do solo, umidade do ar, temperatura, pH, fósforo, potássio, status da bomba), e de onde vêm (sensores simulados da Fase 2/3, IoT).

### 1:00–2:15 — Rodar o pipeline ao vivo
Rode `python ml/treinar_modelos.py` no terminal. Enquanto carrega, explique o tratamento de dados:

> "Antes de treinar, extraímos a hora do dia de cada leitura, criamos uma versão dela em seno e cosseno pra capturar o ciclo diário, e criamos a variável-alvo do primeiro modelo: a umidade da leitura seguinte, 30 minutos à frente."

Deixe o output do terminal aparecer na tela e comente os números (MAE, MSE, RMSE, R² de cada modelo).

### 2:15–3:30 — Por que essas escolhas (a parte mais importante pro critério técnico)
Explique por que regressão múltipla pra prever a umidade futura, e por que comparar 3 abordagens pra temperatura. Esse trecho é o que mostra domínio técnico e pensamento analítico — não só "rodei e funcionou".

> "Inicialmente, testamos usar o pH como uma das variáveis previstas, já que era um dos exemplos citados no enunciado. Mas o R² ficou negativo — pior do que simplesmente prever a média. Investigando o gerador de dados, vimos que o pH ali é sorteado de forma aleatória, sem relação real com as outras variáveis, então não havia padrão pra aprender. Substituímos por temperatura, que tem uma relação real e cíclica com a hora do dia, e isso também nos permitiu comparar regressão linear simples, regressão linear com atributos cíclicos e Random Forest — mostrando o ganho de usar engenharia de atributos e modelos não lineares."

### 3:30–4:30 — Validação visual no dashboard
Volte para o Streamlit e mostre que as métricas na aba "Previsões com IA" são as mesmas do terminal — isso comprova que o pipeline e o dashboard usam o mesmo modelo. Mostre os gráficos de validação (real vs. previsto).

### 4:30–5:00 — Conclusão
Resuma a interpretação prática: o que essas previsões permitem decidir.

> "Na prática, isso significa que conseguimos antecipar uma necessidade de irrigação antes da umidade ficar crítica, em vez de só reagir depois que o problema já aconteceu."

---

## Checklist rápido antes de exportar/entregar

- [ ] Vídeo 1 está dentro de 5 minutos
- [ ] Vídeo 2 está dentro de 5 minutos
- [ ] Os dois mostram o dashboard **funcionando** (não só slides ou código estático)
- [ ] O Vídeo 2 mostra o terminal rodando o treino, não só o resultado já pronto
- [ ] Os nomes e RMs dos integrantes aparecem em algum momento (fala ou tela)
