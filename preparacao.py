def adicionar_features(tabela):
    dados = tabela.copy()

    dados["retorno_1h"] = dados["fechamento"].pct_change(fill_method=None)

    media20 = dados["fechamento"].rolling(window=20, min_periods=20).mean()
    dados["distancia_media20"] = dados["fechamento"] / media20 - 1

    return dados