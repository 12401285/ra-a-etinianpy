
import pandas as pd
import streamlit as st
import plotly.express as px
from etl_etnia_raca import coletar, estatisticas, CATEGORIAS

st.set_page_config(page_title="Cor ou raça - Censo 2022", layout="wide")
st.title("Cor ou raça no Brasil")
st.write("Distribuição da população por cor ou raça - Censo 2022 (IBGE).")


@st.cache_data
def carregar():
    try:
        return pd.read_csv("dados_etnia_raca_2022.csv")
    except FileNotFoundError:
        return coletar()


try:
    dados = carregar()
except Exception as erro:
    st.error(f"Não foi possível carregar a base: {erro}")
    st.info("Execute no terminal: python etl_etnia_raca.py")
    st.stop()


st.sidebar.header("Consultar dados")

arquivo = st.sidebar.file_uploader(
    "Carregar CSV ou Excel (opcional)",
    type=["csv", "xlsx"]
)

if arquivo is not None:
    try:
        if arquivo.name.endswith(".xlsx"):
            dados = pd.read_excel(arquivo)
        else:
            dados = pd.read_csv(arquivo)

        colunas = {"UF", "Regiao", "Cor_ou_raca", "Populacao", "Total_UF", "Percentual"}
        if not colunas.issubset(dados.columns):
            st.error("O arquivo não possui as colunas necessárias.")
            st.stop()

    except Exception as erro:
        st.error(f"Erro ao carregar arquivo: {erro}")
        st.stop()


regiao = st.sidebar.selectbox("Região", ["Brasil"] + sorted(dados["Regiao"].unique()))

if regiao == "Brasil":
    base = dados.copy()
else:
    base = dados[dados["Regiao"] == regiao].copy()

uf = st.sidebar.selectbox("Estado", ["Todos"] + sorted(base["UF"].unique()))

if uf != "Todos":
    base = base[base["UF"] == uf].copy()


st.subheader("Distribuição da população")

resumo = base.groupby("Cor_ou_raca", as_index=False)["Populacao"].sum()
resumo["Percentual"] = resumo["Populacao"] / resumo["Populacao"].sum() * 100

resumo["Cor_ou_raca"] = pd.Categorical(
    resumo["Cor_ou_raca"],
    categories=CATEGORIAS,
    ordered=True
)

resumo = resumo.sort_values("Cor_ou_raca")

fig = px.bar(resumo, x="Cor_ou_raca", y="Percentual", text="Percentual",
             color_discrete_sequence=["#7653a6"],
             labels={"Cor_ou_raca": "Cor ou raça", "Percentual": "População (%)"})
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig.update_layout(showlegend=False, margin=dict(t=25, b=20),
                  yaxis_range=[0, max(5, resumo["Percentual"].max() * 1.17)])
st.plotly_chart(fig, use_container_width=True)


st.subheader("Comparação entre estados")

categoria = st.selectbox("Cor ou raça para comparar", CATEGORIAS, index=3)
comparacao = base[base["Cor_ou_raca"] == categoria].sort_values("Percentual")
fig2 = px.bar(comparacao, x="Percentual", y="UF", orientation="h",
              color_discrete_sequence=["#597b72"],
              labels={"Percentual": "Participação na população do estado (%)",
                      "UF": "Estado"})
fig2.update_layout(height=max(350, 30 * len(comparacao)))
st.plotly_chart(fig2, use_container_width=True)


st.subheader("Estatísticas por estado")

quantidade_estados = base["UF"].nunique()

st.caption(f"Estatísticas calculadas com os dados de "
           f"{quantidade_estados} estado(s) selecionado(s).")

if quantidade_estados > 1:
    resultado = estatisticas(base)
    st.dataframe(
        resultado.round(2), hide_index=True, use_container_width=True
    )
else:
    st.info("Você selecionou apenas um estado. Para comparar estatísticas entre "
            "estados, selecione uma região ou o Brasil inteiro.")

    tabela_estado = base[["Cor_ou_raca", "Percentual"]].copy()
    tabela_estado.columns = ["Cor ou raça", "Percentual (%)"]
    st.dataframe(tabela_estado.round(2), hide_index=True, use_container_width=True)


st.subheader("Boxplot")

if quantidade_estados > 1:
    fig3 = px.box(base, x="Cor_ou_raca", y="Percentual", points="outliers",
                  labels={"Cor_ou_raca": "Cor ou raça",
                          "Percentual": "Participação na UF (%)"})
    st.plotly_chart(fig3, use_container_width=True)
else:
    st.write("O boxplot compara a distribuição entre estados. "
             "Selecione mais de um estado para visualizá-lo.")


st.subheader("Base de dados")

st.dataframe(base, hide_index=True, use_container_width=True)

st.download_button(
    "Baixar CSV filtrado",
    base.to_csv(index=False).encode("utf-8-sig"),
    "etnia_raca_filtrado.csv",
    mime="text/csv"
)


st.subheader("Análise")

st.write("A composição por cor ou raça varia entre os estados brasileiros. "
         "Os percentuais permitem comparar lugares com populações de tamanhos "
         "diferentes. Essas diferenças podem contribuir para estudos sobre acesso "
         "a serviços públicos, mas não demonstram, sozinhas, desigualdade de acesso.")
st.caption("Fonte: IBGE, Censo Demográfico 2022, tabela SIDRA 9605.")
