# Relatório de execução — Preditor de Qualidade de Redes

**Grupo 4 · Ciência da Computação · 25 de outubro de 2026**

## 1. Objetivo

Treinar e avaliar um classificador Random Forest que usa características de uma medição pública de ping IPv4 para prever a classe da próxima medição do mesmo fluxo sonda–âncora. As classes são `OK`, `RISCO` e `FALHA`.

## 2. Fonte e auditoria de publicidade

A execução foi realizada usando os resultados informados pelo pipeline local, que consulta a API REST pública do RIPE Atlas. A saída do programa registrou `Auditoria de publicidade: APROVADA`.

| Indicador | Resultado desta execução |
|---|---:|
| Âncoras selecionadas | 30 |
| Medições públicas listadas | 879 |
| Pares sonda–âncora públicos distintos encontrados | 140 |
| Observações reais salvas no fluxo bruto | 480.812 |
| Fluxos distintos no arquivo bruto | 80 |
| Fluxos com baseline válido | 78 |
| Observações após rotulagem | 235.386 |

**Limitação de cobertura:** o projeto de referência apresenta 150 pares (30 âncoras × 5 sondas). Esta execução encontrou 140 pares públicos e terminou com 78 fluxos válidos para o dataset/treino, após a validação do baseline. Não foram inventados IDs para completar o total. Portanto, o resultado não deve ser descrito como cobertura completa dos 150 pares.

A aprovação da auditoria significa que as linhas rastreadas pelos arquivos locais passaram pelas regras de publicidade/IP usadas pelo validador. Para reprodução, devem ser preservados os arquivos de auditoria e a origem dos CSVs gerados.

## 3. Períodos e separação temporal

Todas as datas abaixo estão em UTC.

- **Período A — baseline:** 11/10/2026 22:05:04 até 18/10/2026 22:05:04. Não entra diretamente no treino.
- **Período B — rotulagem/treino:** 18/10/2026 22:05:04 até 25/10/2026 22:05:04.
- **Teste temporal:** observações iniciadas em 24/10/2026 12:16:04 e terminadas em 25/10/2026 22:03:40.

O pipeline ordena os dados no tempo. Foram reportadas 235.386 linhas elegíveis antes da separação, 188.537 linhas de treino e 46.774 linhas de teste. A soma de treino e teste é 235.311, 75 linhas abaixo do total elegível: o código exclui intencionalmente da parte de treino observações cuja próxima medição atravessaria a fronteira temporal do teste. Isso evita usar no treino um alvo futuro que pertence ao período de teste.

Os períodos A e B foram consultados retroativamente na API. Isto é diferente de afirmar que uma nova medição criada pelo estudante ficou coletando durante 14 dias completos.

## 4. Configuração do modelo

- Algoritmo: Random Forest.
- Árvores: 200.
- `min_samples_leaf`: 5.
- `max_features`: `sqrt`.
- `random_state`: 42.
- Alvo: classe da próxima observação (`classe_proxima`).
- Entradas: 21 características da medição atual e de janelas recentes do mesmo fluxo.

## 5. Métricas no conjunto de teste

| Métrica | Resultado |
|---|---:|
| Acurácia | 94,44% |
| Acurácia balanceada | 71,34% |
| F1 macro | 0,7887 |
| Acurácia da referência de persistência | 91,11% |
| F1 macro da referência de persistência | 0,7094 |

O F1 macro do modelo superou a referência de persistência em aproximadamente 0,0793 (7,93 pontos percentuais). A acurácia, isoladamente, não é suficiente para julgar o modelo porque `OK` é a classe dominante.

### Métricas por classe

| Classe | Precisão | Recall (detecção) | F1 | Casos reais no teste |
|---|---:|---:|---:|---:|
| `OK` | 95,11% | 99,30% | 0,9716 | 41.093 |
| `RISCO` | 85,95% | 60,51% | 0,7102 | 4.609 |
| `FALHA` | 92,81% | 54,20% | 0,6843 | 1.072 |

### Matriz de confusão

Linhas são classes reais; colunas são classes previstas.

| Classe real \ Prevista | `OK` | `RISCO` | `FALHA` |
|---|---:|---:|---:|
| `OK` | 40.804 | 283 | 6 |
| `RISCO` | 1.781 | 2.789 | 39 |
| `FALHA` | 318 | 173 | 581 |

O modelo detectou corretamente 581 dos 1.072 casos reais de `FALHA`. Outros 491 casos de falha foram previstos como `OK` (318) ou `RISCO` (173). Assim, embora a precisão de `FALHA` seja alta quando o modelo emite esse alerta, o recall de 54,20% mostra que ainda há falhas que não são identificadas como `FALHA`.

## 6. Interpretação e limitações

1. Os resultados são válidos para as medições e fluxos que a API retornou nesta execução; não representam garantia de desempenho em outras redes ou períodos.
2. O número de pares (140) ficou abaixo dos 150 do projeto de referência, e só 78 fluxos tiveram baseline válido. Essa limitação deve permanecer explícita.
3. A classe `OK` é muito mais frequente. Por isso, devem ser apresentados F1 macro, acurácia balanceada e métricas por classe junto com a acurácia.
4. O recall de `FALHA` de 54,20% é uma limitação importante para um sistema de alerta; o resultado precisa ser descrito como protótipo acadêmico, não como solução pronta para operação crítica.
5. Os períodos são dados históricos públicos da API. Não se deve afirmar que houve 14 dias de coleta própria contínua.
6. O modelo não usa o dataset sintético antigo no treinamento deste pipeline; os arquivos antigos do protótipo devem ser identificados como legados, e não misturados aos resultados desta execução.

## 7. Artefatos produzidos

- `pipeline/08_treino/data/avaliacao_teste.json` — métricas, matriz de confusão, períodos e hash do modelo.
- `pipeline/08_treino/data/auditoria_publicidade.json` — resultado das verificações de publicidade.
- `pipeline/08_treino/data/modelos/modelo_random_forest.joblib` — modelo treinado.
- `pipeline/05_periodos/data/periodos.json` — janelas A e B.

Ao entregar, mantenha os relatórios JSON correspondentes à mesma execução usada para gerar o modelo. Não altere manualmente métricas para aproximá-las das métricas do repositório de referência: bases, períodos e cobertura podem ser diferentes.
