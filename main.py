"""Executa uma pequena coleta usando as funções de coleta.py."""

import ccxt

from coleta import buscar_candles, criar_corretora, listar_corretoras, listar_mercados


# Esta seleção é um teste pequeno; não limita o catálogo nem as funções.
CORRETORAS_ALVO = ["binance", "kraken"]
PARES_ALVO = ["BTC/USDT", "ETH/USDT"]
INTERVALO = "1h"
QUANTIDADE = 5


def main():
    ids_corretoras = listar_corretoras()
    print(f"Conectores conhecidos pelo CCXT instalado: {len(ids_corretoras)}")
    print(", ".join(ids_corretoras))
    print("A lista acima não confirma que todas as APIs estejam acessíveis.")
    print("Nesta execução, consultaremos:", ", ".join(CORRETORAS_ALVO))

    consultas_com_dados = 0
    for id_corretora in CORRETORAS_ALVO:
        try:
            corretora = criar_corretora(id_corretora)
            mercados = listar_mercados(corretora)
        except (ccxt.BaseError, ValueError) as erro:
            print(f"Falha no catálogo de {id_corretora}: {erro}")
            continue

        print(f"\n{id_corretora}: {len(mercados)} mercados no catálogo do conector.")
        print(mercados.head(5).to_string(index=False))

        for par in PARES_ALVO:
            try:
                tabela = buscar_candles(corretora, par, INTERVALO, QUANTIDADE)
            except (ccxt.BaseError, ValueError) as erro:
                print(f"Falha ao consultar {id_corretora} / {par}: {erro}")
                continue

            print(f"\n{id_corretora} / {par}: {len(tabela)} candles recebidos.")
            if tabela.empty:
                print("A consulta não retornou candles.")
            else:
                consultas_com_dados += 1
                print(tabela.to_string(index=False))

    print("\nOs dados desta execução ficaram apenas na memória.")
    print("Esta amostra ainda não está preparada para treinamento.")
    if consultas_com_dados == 0:
        print("Nenhuma consulta retornou candles; confira as mensagens acima.")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
