# Documento de Coleta — log_rede.csv

**Grupo:** 4
**Responsável:** Jonathan Ferreira Luna

## Como os dados foram coletados

Os dados foram coletados com a biblioteca Python **icmplib**, que envia pacotes de ping (ICMP echo request) e mede o tempo de resposta de cada um. A coleta rodou diretamente no Google Colab.

Cada registro do log corresponde a uma **janela de medição**: um grupo de 8 tentativas de ping seguidas contra o mesmo destino, com intervalo de 0,15 segundos entre elas. A partir dessa janela, foram calculadas três métricas:

- **Latência (`latencia_ms`)**: média do tempo de resposta (RTT) das tentativas que obtiveram resposta.
- **Perda de pacotes (`perda_pacotes_pct`)**: percentual de tentativas, dentro da janela, que não obtiveram resposta.
- **Jitter (`jitter_ms`)**: média da variação do tempo de resposta entre uma tentativa e a seguinte.

## Quais cenários foram simulados

Para garantir exemplos das três classes de status (OK, RISCO e FALHA) sem depender de uma rede local física, foram escolhidos 4 destinos (IPs) com perfis de qualidade diferentes:

| IP | Descrição | Classe esperada |
|---|---|---|
| `8.8.8.8` | DNS público do Google — rápido e estável | OK |
| `1.1.1.1` | DNS público da Cloudflare — rápido e estável | OK |
| `180.76.76.76` | DNS público da Baidu (China) — fisicamente distante, maior latência | RISCO |
| `192.0.2.1` | Endereço reservado para documentação/testes (RFC 5737) — nunca responde | FALHA |

A classificação de cada janela (`status_real`) foi feita automaticamente por um script, aplicando as seguintes regras:

- **FALHA**: perda de pacotes igual ou acima de 15%, ou latência indisponível (sem nenhuma resposta).
- **RISCO**: latência acima de 150 ms, ou perda de pacotes entre 2% e 15%.
- **OK**: latência até 150 ms e perda de pacotes abaixo de 2%.

## Resultado

Foram coletadas **110 janelas de medição**, distribuídas entre os 4 destinos, com a seguinte composição de classes:

| Classe | Quantidade |
|---|---|
| OK | 51 |
| RISCO | 38 |
| FALHA | 21 |

O arquivo final segue o contrato de dados definido no Kickoff: `timestamp, ip, latencia_ms, perda_pacotes_pct, jitter_ms, status_real`.
