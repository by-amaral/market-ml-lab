"""Primeiro modelo: regressão logística com avaliação temporal walk-forward."""

import argparse
import re
from pathlib import Path

import pandas as pd
from sklearn.dummy import DummyClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, log_loss
from sklearn.model_selection import TimeSeriesSplit
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from preparacao import adicionar_alvo, adicionar_features
from validacao import verificar_dados


FEATURES = ["retorno_1h", "distancia_media20"]
ALVO = "alvo_alta"
PASTA_RESULTADOS = Path(__file__).resolve().parent / "resultados"


def preparar_base(tabela, data_inicio, data_fim):
    """Valida uma série e remove apenas linhas sem features ou alvo disponíveis."""
    obrigatorias = [
        "corretora", "par", "intervalo", "timestamp",
        "abertura", "maxima", "minima", "fechamento", "volume",
    ]
    faltantes = set(obrigatorias) - set(tabela.columns)
    if faltantes:
        raise ValueError(f"Colunas ausentes: {', '.join(sorted(faltantes))}")

    relatorio = verificar_dados(tabela, data_inicio, data_fim)
    if any(relatorio.values()):
        raise ValueError(f"Histórico inválido para treinamento: {relatorio}")

    dados = tabela.copy()
    dados["timestamp"] = pd.to_datetime(dados["timestamp"], utc=True)
    numeros = ["abertura", "maxima", "minima", "fechamento", "volume"]
    dados[numeros] = dados[numeros].apply(pd.to_numeric)
    dados = adicionar_alvo(adicionar_features(dados))

    # O timestamp identifica a abertura. A previsão usa o candle já fechado;
    # a resposta só fica disponível ao fechamento do candle seguinte.
    dados["momento_previsao"] = dados["timestamp"] + pd.Timedelta(hours=1)
    dados["alvo_disponivel_em"] = dados["timestamp"] + pd.Timedelta(hours=2)
    dados = dados.dropna(subset=FEATURES + [ALVO]).reset_index(drop=True)
    dados[ALVO] = dados[ALVO].astype(int)

    if len(dados) < 100:
        raise ValueError("Use pelo menos 100 exemplos completos para este piloto.")
    return dados


def calcular_metricas(alvos, previsoes, probabilidades):
    """Acurácia é taxa de acerto; log loss avalia as probabilidades (menor é melhor)."""
    return {
        "acuracia": accuracy_score(alvos, previsoes),
        "acuracia_balanceada": (
            balanced_accuracy_score(alvos, previsoes)
            if alvos.nunique() == 2 else float("nan")
        ),
        "log_loss": log_loss(alvos, probabilidades, labels=[0, 1]),
    }


def treinar_avaliar(tabela, data_inicio, data_fim):
    """Reajusta o modelo em três janelas crescentes, sem embaralhar os exemplos."""
    dados = preparar_base(tabela, data_inicio, data_fim)
    divisao = TimeSeriesSplit(n_splits=3, gap=1)
    etapas = []
    previsoes = []

    for etapa, (indices_treino, indices_teste) in enumerate(divisao.split(dados), 1):
        treino = dados.iloc[indices_treino]
        teste = dados.iloc[indices_teste]
        if treino[ALVO].nunique() != 2:
            raise ValueError(f"Etapa {etapa}: treino precisa conter alta e queda/empate.")
        if treino["alvo_disponivel_em"].max() >= teste["momento_previsao"].min():
            raise ValueError("Há um alvo do treino ainda desconhecido no corte temporal.")

        # O scaler aprende média e escala somente no treino de cada etapa.
        modelo = make_pipeline(
            StandardScaler(),
            LogisticRegression(max_iter=1000, random_state=42),
        )
        modelo.fit(treino[FEATURES], treino[ALVO])

        # Prevê a classe mais frequente; probabilidades refletem só o treino.
        referencia = DummyClassifier(strategy="prior")
        referencia.fit(treino[FEATURES], treino[ALVO])

        saida = teste[[
            "corretora", "par", "intervalo", "timestamp", "momento_previsao",
            "alvo_disponivel_em", ALVO,
        ]].copy()
        saida.insert(0, "etapa", etapa)
        saida["previsao_modelo"] = modelo.predict(teste[FEATURES])
        saida["probabilidade_alta"] = modelo.predict_proba(teste[FEATURES])[:, 1]
        saida["previsao_referencia"] = referencia.predict(teste[FEATURES])
        saida["probabilidade_referencia"] = referencia.predict_proba(teste[FEATURES])[:, 1]
        previsoes.append(saida)

        registro = {
            "etapa": etapa,
            "exemplos_treino": len(treino),
            "exemplos_teste": len(teste),
            "primeira_previsao_treino": treino["momento_previsao"].min(),
            "ultimo_alvo_treino_disponivel_em": treino["alvo_disponivel_em"].max(),
            "primeira_previsao_teste": teste["momento_previsao"].min(),
            "ultima_previsao_teste": teste["momento_previsao"].max(),
        }
        for nome, predicao, probabilidade in (
            ("modelo", "previsao_modelo", "probabilidade_alta"),
            ("referencia", "previsao_referencia", "probabilidade_referencia"),
        ):
            metricas = calcular_metricas(saida[ALVO], saida[predicao], saida[probabilidade])
            registro.update({f"{chave}_{nome}": valor for chave, valor in metricas.items()})
        etapas.append(registro)

    previsoes = pd.concat(previsoes, ignore_index=True)
    totais = []
    for nome, predicao, probabilidade in (
        ("regressao_logistica", "previsao_modelo", "probabilidade_alta"),
        ("classe_mais_frequente", "previsao_referencia", "probabilidade_referencia"),
    ):
        metricas = calcular_metricas(previsoes[ALVO], previsoes[predicao], previsoes[probabilidade])
        totais.append({"metodo": nome, "exemplos_avaliados": len(previsoes), **metricas})

    return {
        "base": dados,
        "etapas": pd.DataFrame(etapas),
        "previsoes": previsoes,
        "metricas": pd.DataFrame(totais),
    }


def salvar_resultados(resultado, pasta=PASTA_RESULTADOS):
    """Mantém dados preparados e avaliação separados dos candles de origem."""
    primeira = resultado["base"].iloc[0]
    nome = f"{primeira['corretora']}_{primeira['par']}_{primeira['intervalo']}"
    destino = Path(pasta) / re.sub(r"[^a-zA-Z0-9_.-]", "_", nome)
    destino.mkdir(parents=True, exist_ok=True)
    for nome in ("base", "etapas", "previsoes", "metricas"):
        resultado[nome].to_csv(destino / f"{nome}.csv", index=False)
    return destino


def mostrar_resultados(resultado):
    print(f"\nExemplos utilizáveis: {len(resultado['base'])}")
    print("Avaliação walk-forward: três etapas, com uma hora de separação.")
    colunas = [
        "etapa", "exemplos_treino", "exemplos_teste",
        "acuracia_modelo", "acuracia_referencia",
    ]
    print(resultado["etapas"][colunas].to_string(index=False, float_format="%.4f"))
    print("\nResultado agregado, somente em exemplos posteriores ao treino:")
    print(resultado["metricas"].to_string(index=False, float_format="%.4f"))
    print("Acurácia de 0.55 significa 55% de acertos; log loss menor é melhor.")
    print("Este piloto mede previsão de direção, não lucro de uma estratégia.")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--arquivo", required=True, help="CSV de candles de uma única série de 1h")
    parser.add_argument("--inicio", default="2026-08-01T00:00:00Z")
    parser.add_argument("--fim", default="2026-09-01T00:00:00Z")
    parser.add_argument("--saida", type=Path, default=PASTA_RESULTADOS)
    args = parser.parse_args()
    try:
        tabela = pd.read_csv(args.arquivo)
        resultado = treinar_avaliar(tabela, args.inicio, args.fim)
        destino = salvar_resultados(resultado, args.saida)
    except (OSError, ValueError) as erro:
        print(f"Não foi possível concluir o treinamento: {erro}")
        return 1
    mostrar_resultados(resultado)
    print(f"Resultados salvos em: {destino}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
