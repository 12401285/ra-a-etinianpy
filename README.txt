ENTREGA INDIVIDUAL - COR OU RAÇA (CENSO 2022)

1. Abra o terminal na pasta dos arquivos.
2. Instale: python -m pip install -r requirements.txt
3. Gere os dados: python etl_etnia_raca.py
4. Abra o painel: python -m streamlit run app_etnia_raca.py

O script gera os arquivos dados_etnia_raca_2022.csv e estatisticas_etnia_raca_2022.csv.
Inclua os CSVs na entrega ao professor.

Fonte: IBGE, SIDRA, tabela 9605:
https://sidra.ibge.gov.br/tabela/9605

A coleta exige internet. Se a estrutura da API mudar, o programa exibe um erro em vez de usar dados inventados.

As estatísticas são calculadas sobre as porcentagens de cada categoria nas 27 UFs.
O projeto inclui filtros, upload CSV/XLSX, barras, boxplot, medidas estatísticas e texto de interpretação.
