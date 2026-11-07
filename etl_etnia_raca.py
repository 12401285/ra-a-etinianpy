"""Coleta dados de cor ou raça do Censo 2022 no SIDRA/IBGE."""

import pandas as pd
import requests

URL = 'https://apisidra.ibge.gov.br/values/t/9605/n3/all/v/93/p/2022/c86/all'
CATEGORIAS = ['Branca', 'Preta', 'Amarela', 'Parda', 'Indígena']
REGIOES = {
    'Rondônia': 'Norte',
    'Acre': 'Norte',
    'Amazonas': 'Norte',
    'Roraima': 'Norte',
    'Pará': 'Norte',
    'Amapá': 'Norte',
    'Tocantins': 'Norte',
    'Maranhão': 'Nordeste',
    'Piauí': 'Nordeste',
    'Ceará': 'Nordeste',
    'Rio Grande do Norte': 'Nordeste',
    'Paraíba': 'Nordeste',
    'Pernambuco': 'Nordeste',
    'Alagoas': 'Nordeste',
    'Sergipe': 'Nordeste',
    'Bahia': 'Nordeste',
    'Minas Gerais': 'Sudeste',
    'Espírito Santo': 'Sudeste',
    'Rio de Janeiro': 'Sudeste',
    'São Paulo': 'Sudeste',
    'Paraná': 'Sul',
    'Santa Catarina': 'Sul',
    'Rio Grande do Sul': 'Sul',
    'Mato Grosso do Sul': 'Centro-Oeste',
    'Mato Grosso': 'Centro-Oeste',
    'Goiás': 'Centro-Oeste',
    'Distrito Federal': 'Centro-Oeste'
}


def coletar():
    resposta = requests.get(URL, timeout=90)
    resposta.raise_for_status()
    registros = resposta.json()
    if not isinstance(registros, list) or len(registros) < 2:
        raise ValueError('A consulta não retornou registros. Confira a tabela 9605 no SIDRA.')

    linhas = []
    for item in registros[1:]:
        uf = item.get('D1N', '').strip()
        raca = ''
        for chave, valor in item.items():
            descricao = str(valor).strip()
            if (
                chave.startswith('D')
                and chave.endswith('N')
                and descricao in CATEGORIAS
            ):
                raca = descricao
                break

        if raca not in CATEGORIAS or uf not in REGIOES:
            continue

        valor = item.get('V', '')
        try:
            numero = int(str(valor))
        except (ValueError, TypeError):
            continue

        linhas.append({
            'UF': uf,
            'Regiao': REGIOES[uf],
            'Cor_ou_raca': raca,
            'Populacao': numero
        })

    dados = pd.DataFrame(linhas)
    if dados.empty:
        raise ValueError('A API respondeu, mas as categorias não foram reconhecidas. Verifique os parâmetros da tabela 9605.')

    dados = dados.groupby(
        ['UF', 'Regiao', 'Cor_ou_raca'], as_index=False
    )['Populacao'].sum()
    validacao = dados.groupby('UF')['Cor_ou_raca'].nunique()
    if len(validacao) != 27 or not (validacao == 5).all():
        raise ValueError('A extração não contém as cinco categorias em todas as 27 UFs. Não serão gerados resultados incompletos.')

    dados['Total_UF'] = dados.groupby('UF')['Populacao'].transform('sum')
    dados['Percentual'] = dados['Populacao'] / dados['Total_UF'] * 100
    dados = dados.sort_values(['Regiao', 'UF', 'Cor_ou_raca'])
    dados.to_csv('dados_etnia_raca_2022.csv', index=False, encoding='utf-8-sig')
    return dados


def estatisticas(dados):
    linhas = []
    for raca in CATEGORIAS:
        serie = dados.loc[dados['Cor_ou_raca'] == raca, 'Percentual']
        q1, q2, q3 = serie.quantile([.25, .5, .75])
        iqr = q3 - q1
        outliers = dados.loc[
            (dados['Cor_ou_raca'] == raca)
            & (
                (dados['Percentual'] < q1 - 1.5 * iqr)
                | (dados['Percentual'] > q3 + 1.5 * iqr)
            ),
            'UF'
        ].tolist()
        moda = serie.round(2).mode()

        linhas.append({
            'Cor ou raça': raca,
            'Média': serie.mean(),
            'Mediana': q2,
            'Moda (arred. 2 casas)': (
                moda.iloc[0] if len(moda) == 1 else 'Sem moda única'
            ),
            'Q1': q1,
            'Q2': q2,
            'Q3': q3,
            'IQR': iqr,
            'Amplitude': serie.max() - serie.min(),
            'Desvio padrão': serie.std(ddof=1),
            'Outliers': ', '.join(outliers) or 'Nenhum'
        })

    resultado = pd.DataFrame(linhas)
    resultado.to_csv(
        'estatisticas_etnia_raca_2022.csv',
        index=False,
        encoding='utf-8-sig'
    )
    return resultado


if __name__ == '__main__':
    df = coletar()
    print('Dados salvos:', len(df), 'linhas')
    print(estatisticas(df).to_string(index=False))
