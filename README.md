# market-ml-lab

> ⚠️ **README temporário.** Este projeto está em estágio inicial e este documento será expandido conforme o projeto evolui.

## O que é isso

Laboratório de estudo para aplicar Machine Learning / Deep Learning em dados de mercado (cripto, ações, commodities — o escopo é aberto, não fixo em um único tipo de ativo).

**Isto não é uma ferramenta de recomendação de investimento.** É um projeto de aprendizado sobre coleta de dados, engenharia de features, modelagem e validação estatística em séries temporais financeiras.

## Status atual

🚧 Fase 1 — coleta de dados.

- [x] Setup do repositório e ambiente
- [x] Coleta básica de candles via API (CCXT)
- [ ] Organização e limpeza de dados históricos
- [ ] Cálculo de indicadores técnicos
- [ ] Baseline de classificação (Random Forest / Regressão Logística)
- [ ] Backtest com validação walk-forward
- [ ] Avaliação de modelos de Deep Learning (se justificado pelos resultados anteriores)

## Como rodar

```powershell
# criar e ativar ambiente virtual
python -m venv venv
.\venv\Scripts\Activate.ps1

# instalar dependências
pip install -r requirements.txt
```

## Princípios do projeto

- **Sem lookahead bias**: nenhuma feature ou rótulo usa informação que não estaria disponível no momento real da decisão.
- **Validação honesta**: divisão de treino/teste respeita a ordem temporal (walk-forward), nunca split aleatório.
- **Modelo simples primeiro**: só se justifica Deep Learning depois de esgotar e comparar com baselines mais simples (ex.: Random Forest, XGBoost).
- **Resultados documentados com limitações**, não vendidos como solução pronta.

## Licença

MIT — veja [LICENSE](./LICENSE).