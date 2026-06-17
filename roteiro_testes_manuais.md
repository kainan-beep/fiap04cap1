# Roteiro de Testes Manuais — FarmTech Solutions (Fase 4)

Use este roteiro **antes** de gravar os vídeos. Cada bloco indica qual critério do barema ele valida, então se tudo aqui passar, as Partes 1 e 2 estão cobertas tecnicamente — o que falta depois é só a gravação em si.

## 0. Preparação do ambiente

- [ ] Extraiu o zip e copiou o conteúdo para dentro da pasta do repositório local, **sem sobrescrever a pasta `.git`**
- [ ] Rodou `pip install -r requirements.txt` sem erro (deve instalar oracledb, streamlit, pandas, plotly, numpy, scikit-learn e joblib)

## 1. Pipeline de ML isolado — valida "correta aplicação dos modelos" (3 pts) e parte da "integração" (3 pts)

Comando: `python ml/treinar_modelos.py`

- [ ] Roda sem erro e imprime `Dados carregados: 240 leituras`
- [ ] Modelo 1 (umidade): MAE ≈ 0.77 — MSE ≈ 0.86 — RMSE ≈ 0.93 — **R² ≈ 0.994**
- [ ] Modelo 2 (temperatura): aparecem 3 linhas — `linear_simples` (R² ≈ 0.13), `linear_ciclico` (R² ≈ 0.73), `random_forest` (R² ≈ 0.55) — com `linear_ciclico` marcado como escolhido
- [ ] Foi criada a pasta `ml/modelos/` com `modelo_umidade.pkl`, `modelo_temperatura.pkl` e `metricas.json`

**Sinal de alerta:** se esses números vierem muito diferentes (ex.: R² muito menor, ou erro de importação), pare e investigue antes de gravar — não adianta gravar o vídeo com um resultado que depois pede ajuste.

## 2. Aba "Monitoramento" (Fase 3) — não é nota da Fase 4, mas precisa continuar funcionando

Comando: `streamlit run dashboard/app.py`

- [ ] Abre no navegador sem erro
- [ ] Barra lateral mostra a fonte de dados (`CSV local`, ou `Oracle FIAP` se você estiver na rede da faculdade — qualquer um dos dois é normal)
- [ ] Os 4 KPIs aparecem no topo
- [ ] Gráfico de umidade com as duas linhas de limite (vermelha e verde) aparece
- [ ] Gráfico de pH com a faixa ideal sombreada aparece
- [ ] Gráfico de temperatura/umidade do ar aparece
- [ ] Os dois donuts (Fósforo e Potássio) aparecem
- [ ] Tabela de sugestões (últimas 10 leituras) aparece
- [ ] Expander "Ver todas as leituras filtradas" abre corretamente
- [ ] Mudar o filtro de período na barra lateral atualiza os gráficos das duas abas

## 3. Aba "Previsões com IA" (Fase 4) — valida "integração" (3 pts) e "clareza dos resultados no dashboard" (2 pts)

- [ ] Ao entrar na aba, aparece rapidamente "Treinando modelos de regressão..." e depois o conteúdo carrega
- [ ] As 4 métricas do Modelo 1 (MAE, MSE, RMSE, R²) aparecem **com os mesmos valores do terminal** — isso é a prova visual de que o dashboard está realmente integrado ao pipeline, e não usando números fixos
- [ ] Gráfico "Real vs. previsto" aparece, com os pontos próximos da linha diagonal pontilhada
- [ ] Tabela comparando os 3 modelos de temperatura aparece, com a linha de maior R² destacada
- [ ] Gráfico "Temperatura real vs. prevista por hora" aparece, com a linha seguindo o formato de pico ao longo do dia
- [ ] Heatmap de correlação aparece com as 4 variáveis numéricas, e a legenda abaixo comenta o pH

## 4. Simulador interativo — valida "previsões em tempo real" (Parte 1) e "sugerir ações de manejo" (Parte 2)

- [ ] Umidade do slider em ~15% → "Lâmina de irrigação sugerida" sobe bastante (~100 mm ou mais) e a mensagem fica **vermelha**: "Irrigar de forma preventiva"
- [ ] Umidade do slider em ~80% → lâmina cai para 0,0 mm e a mensagem fica **azul**: "Manter bomba desligada"
- [ ] Umidade do slider em ~50% → mensagem fica **verde**: "Sem ação necessária"
- [ ] Hora do slider em 0h ou 23h → temperatura prevista cai (madrugada)
- [ ] Hora do slider em 14h → temperatura prevista no valor mais alto
- [ ] Alternar "Bomba agora" para LIGADA com a mesma umidade → a umidade prevista sobe em relação à mesma configuração com a bomba desligada

## 5. Conferência final cruzada com o barema

| Critério (pontos) | Onde verificar | Status esperado |
|---|---|---|
| Integração modelo + dashboard (3 pts) | `app.py` importa direto de `ml/treinar_modelos.py`; números do Teste 3 batem com os do Teste 1 | ✅ se Testes 1 e 3 passaram |
| Correta aplicação da regressão + sugestão de manejo (3 pts) | Teste 1 (modelos rodam e métricas saem corretas) + Teste 4 (sugestão e lâmina mudam coerentemente) | ✅ se Testes 1 e 4 passaram |
| Clareza/eficiência dos resultados no dashboard (2 pts) | Teste 3 (todas as métricas, tabelas e gráficos aparecem e são legíveis) | ✅ se Teste 3 passou |
| Clareza e domínio técnico no vídeo (2 pts) | Não testável por código — depende da gravação | Ver `roteiro_gravacao_videos.md` |

Se todas as caixas acima estiverem marcadas, o projeto cobre tecnicamente tudo que foi pedido nas Partes 1 e 2. O único ponto que depende só de vocês na hora é a apresentação em si.
