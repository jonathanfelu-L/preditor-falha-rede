# Memorando de Decisão — Preditor de Falha/Risco em Dispositivos de Rede

| Campo | Informação |
|---|---|
| **Projeto** | Preditor de Falha e Risco em Dispositivos de Rede (com modelo de predição em árvore) |
| **Grupo** | Grupo 4 |
| **Turma** | [preencher] |
| **Responsável** | Jonathan Ferreira Luna |
| **Disciplinas** | Redes de Computadores, Estrutura de Dados II e Análise de Sistemas |
| **Professores** | Profa. Andréa Ono Sakai, Profa. Denise Braito de Souza, Prof. Luis Ricardo de Oliveira |
| **Data do memorando** | [preencher] |
| **Repositório** | [link do GitHub] |
| **Branch principal** | main |

> **Observação sobre a composição da equipe:** este projeto está sendo conduzido individualmente por Jonathan Ferreira Luna, que acumula os papéis de Product Owner, Scrum Master e equipe de desenvolvimento, cobrindo as frentes de Redes, Estrutura de Dados II e Análise de Sistemas.

> **Nota:** os itens marcados com **[CONFIRMAR]** são decisões preliminares e podem ser ajustadas ao longo das sprints, com registro no Product Backlog.

---

## 1. Contexto

O projeto integra três disciplinas trabalhando em paralelo com a metodologia **Scrum**, no período de **17/08/2026 a 12/11/2026** (apresentação de 10 a 12/11/2026, nota de 0 a 4).

- **Redes** gera um log de métricas de monitoramento de dispositivos (`log_rede.csv`).
- **Estrutura de Dados II** treina uma árvore de decisão com esse log e constrói um dashboard que classifica dispositivos em tempo real.
- **Análise de Sistemas** organiza o projeto: requisitos, regras de negócio, Product Backlog e cerimônias Scrum.

**Problema a resolver:** classificar cada dispositivo de rede em **OK**, **RISCO** ou **FALHA** a partir de métricas de rede, ao vivo, e permitir demonstrar as três classes na apresentação mesmo que a rede real esteja saudável.

---

## 2. Decisões

### D1 — Contrato de dados (schema do log)

- **Decisão:** o schema é fixo e não muda após o Kickoff:
  `timestamp, ip, latencia_ms, perda_pacotes_pct, jitter_ms, status_real`
- **Justificativa:** permite que as frentes de Redes e de Estrutura de Dados II avancem em paralelo, sem que uma espere pela outra. A frente de ED2 usa dados sintéticos desde a Sprint 1, enquanto a coleta real segue o mesmo formato.
- **Consequência:** qualquer alteração no schema exige revisão das três frentes e registro no Product Backlog.

### D2 — Critérios de classificação (regras de negócio) **[CONFIRMAR]**

| Classe | Critério inicial |
|---|---|
| **OK** | Latência baixa, jitter baixo e perda de pacotes próxima de 0% |
| **RISCO** | Latência acima de ~100 ms, ou jitter/perda em nível intermediário |
| **FALHA** | Perda de pacotes acima de ~15%, ou dispositivo sem resposta |

- **Justificativa:** o gerador sintético e a rotulagem da coluna `status_real` do log real precisam seguir a mesma regra de bom senso (por exemplo, perda alta tende a FALHA).
- **Observação:** os limiares acima são iniciais. A árvore aprende seus próprios cortes a partir dos dados, e os valores finais serão documentados no Documento de Regras de Negócio.

### D3 — Algoritmo do modelo

- **Decisão:** árvore de decisão (ID3/CART) **[CONFIRMAR: scikit-learn ou implementação manual]**.
- **Alternativas consideradas:**
  - Implementação manual (mais didática, mais trabalhosa).
  - `scikit-learn` `DecisionTreeClassifier` (mais rápida, menor risco de erro).
  - Random Forest (opcional, apenas para comparação).
- **Justificativa:** a árvore é interpretável, pois expõe as condições de corte, e atende diretamente ao conteúdo de Estrutura de Dados II (nós, folhas, percurso recursivo).
- **Validação:** divisão treino/teste de 70%/30%, com cálculo de acurácia sobre os dados de teste.

### D4 — Estratégia de dados (sintético → real)

- **Decisão:** treinar primeiro com dataset sintético (Sprints 1–2) e retreinar com o log real na Sprint 5, comparando as acurácias.
- **Justificativa:** o desenvolvimento do modelo não fica bloqueado pela coleta real, e o relatório de comparação sintético vs. real é um entregável exigido.
- **Requisito:** o log (sintético ou real) deve conter as 3 classes, com mínimo de 100 a 150 registros e boa distribuição entre elas.

### D5 — Coleta de dados (frente de Redes)

- **Decisão:** monitorar 2 ou mais IPs na rede local (ou simulados no Cisco Packet Tracer), coletando latência, jitter e perda de pacotes via ping (ICMP).
- **Cenários gerados propositalmente:** rede saudável, degradada e com falha (desligar interface, saturar tráfego, aumentar RTT).
- **Uso do Packet Tracer:** somente na fase de geração do log de treino, sem integração com o dashboard em tempo real.

### D6 — Tecnologias

| Item | Escolha | Alternativa |
|---|---|---|
| Linguagem | Python | Outra linguagem de preferência |
| Manipulação de dados | Pandas / CSV | — |
| Modelo | scikit-learn **[CONFIRMAR]** | Implementação manual |
| Dashboard | Streamlit **[CONFIRMAR]** | Flask + HTML |
| Gestão Scrum | GitHub Projects **[CONFIRMAR]** | Trello, Jira, planilha |
| Versionamento | Git / GitHub | — |

### D7 — Dashboard em tempo real

- **Decisão:** o dashboard executa ping periódico (a cada X segundos) em 1–2 IPs reais, passa cada medição pela árvore treinada e exibe o status por dispositivo.
- **Estrutura auxiliar:** tabela hash (IP → histórico) e/ou fila com as últimas N medições.
- **Modo "Simular Evento":** botão que injeta artificialmente pico de latência, jitter ou perda, permitindo demonstrar RISCO e FALHA independentemente do estado real da rede.
- **Requisito de transparência:** indicação visual clara de qual medição é **real** (ping ao vivo) e qual é **simulada** (evento injetado).
- **Justificativa:** a apresentação exige validação ao vivo, com transição visual OK → RISCO → FALHA.

### D8 — Organização Scrum

- **Product Owner:** Jonathan Ferreira Luna — mantém e prioriza o Product Backlog.
- **Scrum Master:** Jonathan Ferreira Luna — conduz as cerimônias e registra impedimentos.
- **Equipe de desenvolvimento:** Jonathan Ferreira Luna — execução das três frentes (Redes, ED2 e Análise).
- **Cerimônias:** Sprint Planning, Daily Scrum (registro assíncrono), Sprint Review e Sprint Retrospective, com evidências registradas no repositório.
- **Quadro:** colunas To Do / Doing / Done, atualizado ao longo do projeto.
- **Escopo de Análise de Sistemas:** apenas a estruturação do Scrum (requisitos, regras de negócio, backlog e cerimônias), sem codificar a árvore nem configurar a rede.
- **Adaptação ao trabalho individual:** como não há outros integrantes, as dailies são registradas em formato de diário de bordo curto e a Sprint Review consiste na demonstração do incremento funcional ao final de cada sprint.

---

## 3. Cronograma

| Etapa | Período | Frente ED2 | Frente Redes |
|---|---|---|---|
| Kickoff | 17–21/08 | Contrato de dados, Product Backlog inicial | Contrato de dados, planejamento da coleta |
| Sprint 1 | 24/08–04/09 | Gerador sintético + estrutura da árvore | Início da coleta, configuração da rede |
| Sprint 2 | 07–18/09 | Treino/teste com dados sintéticos, acurácia | Continuação da coleta, cenários de falha |
| Sprint 3 | 21/09–02/10 | Dashboard: ping real + histórico | Cenários variados (OK/RISCO/FALHA) |
| Sprint 4 | 05–16/10 | Dashboard: modo de simulação de eventos | Entrega do `log_rede.csv` consolidado |
| Sprint 5 | 19–30/10 | Retreino com log real, comparação sintético vs. real | Apoio na validação e documentação |
| Sprint 6 | 02–09/11 | Testes finais, relatório, ensaio | Testes finais, relatório, ensaio |
| Apresentação | 10–12/11 | — | — |

---

## 4. Alternativas descartadas

- **Esperar o log real antes de começar o modelo:** descartado, pois bloquearia todo o desenvolvimento do modelo até a Sprint 4.
- **Integrar o Packet Tracer ao dashboard em tempo real:** descartado, pois foge do escopo definido e aumenta a complexidade. Ele é usado apenas na geração do log de treino.
- **Depender apenas do ping real na apresentação:** descartado, porque não há garantia de que as classes RISCO e FALHA apareçam no momento da banca. Daí a necessidade do modo de simulação.

---

## 5. Riscos e mitigações

| Risco | Impacto | Mitigação |
|---|---|---|
| Log real com poucas amostras de RISCO/FALHA | Modelo ruim ou classes ausentes | Gerar cenários propositais; complementar com dados sintéticos |
| Rede do laboratório saudável na apresentação | Não demonstra RISCO/FALHA | Modo "Simular Evento" |
| Atraso na coleta da frente de Redes | Retreino atrasado na Sprint 5 | Manter o dataset sintético como plano B; iniciar a coleta já na Sprint 1 |
| Mudança de schema no meio do projeto | Quebra a compatibilidade entre as frentes | Contrato de dados travado no Kickoff |
| Vazamento de senhas ou tokens no repositório | Problema de segurança | Revisar o repositório antes de cada entrega; usar `.gitignore` |
| Baixa aderência ao Scrum | Perda de nota (a metodologia pesa tanto quanto o código) | Registrar cerimônias e atualizar o quadro a cada sprint |
| Acúmulo de papéis por ser trabalho individual | Sobrecarga e risco de atraso | Priorização rigorosa do backlog; escopo mínimo viável definido por sprint |

---

## 6. Entregáveis previstos

- `log_rede.csv` estruturado, documentado e balanceado (OK/RISCO/FALHA)
- Gerador de dataset sintético (script + regras documentadas)
- Código-fonte (modelo + dashboard)
- Representação visual ou textual da árvore gerada
- Relatório: construção da árvore, atributos usados nos cortes e acurácia obtida
- Relatório de comparação: acurácia com dataset sintético vs. com log real (Sprint 5)
- Documento de requisitos, documento de regras de negócio e diagrama de casos de uso
- Product Backlog, Sprint Backlogs, registro das cerimônias e quadro Kanban atualizado
