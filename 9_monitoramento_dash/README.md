# Painel de monitoramento (acadêmico)

Execute na raiz do repositório, com o ambiente virtual ativo:

```powershell
streamlit run 9_monitoramento_dash/app.py
```

O painel lê o arquivo de medições que foi baixado e a avaliação mais recente. **Ele não cria medições nem consulta a API a cada segundo.** Para atualizar o histórico, rode novamente a coleta conforme o README e gere o arquivo de fluxo; depois reabra/recarregue o painel.
