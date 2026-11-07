"""Dashboard de cor ou raça. Estatísticas sempre respeitam os filtros."""
import pandas as pd
import plotly.express as px
import streamlit as st

from etl_etnia_raca import coletar, CATEGORIAS

st.set_page_config(page_title="Etnia e raça - IBGE", layout="wide")
st.title("Cor ou raça no Brasil")
st.caption("Censo Demográfico 2022 - IBGE")

@st.cache_data
def carregar_dados():
    try:
        return pd.read_csv("dados_etnia_raca_2022.csv", encoding="utf-8-sig")
    except FileNotFoundError:
        return coletar()


def calcular_estatisticas(dados_filtrados):
    """Recebe SOMENTE as UFs filtradas; nunca usa a base nacional global."""
    resultado = []
    for categoria in CATEGORIAS:
        serie = dados_filtrados.loc[
            dados_filtrados["Cor_ou_raca"] == categoria, "Percentual"
        ].dropna().astype(float)
        if serie.empty:
            continue
        q1 = serie.quantile(0.25)
        mediana = serie.quantile(0.50)
        q3 = serie.quantile(0.75)
        iqr = q3 - q1
        limites = (q1 - 1.5 * iqr, q3 + 1.5 * iqr)
        outliers = dados_filtrados.loc[
            (dados_filtrados["Cor_ou_raca"] == categoria)
            & (
                (dados_filtrados["Percentual"] < limites[0])
                | (dados_filtrados["Percentual"] > limites[1])
            ),
            "UF",
        ].tolist()
        valores_arredondados = serie.round(2)
        frequencias = valores_arredondados.value_counts()
        if frequencias.max() == 1:
            moda = "Sem moda"
        else:
            repetidos = sorted(frequencias[frequencias == frequencias.max()].index)
            moda = ", ".join(f"{n:.2f}" for n in repetidos)

        resultado.append({
            "Cor ou raça": categoria,
            "Média": serie.mean(),
            "Mediana": mediana,
            "Moda": moda,
            "Q1": q1,
            "Q2": mediana,
            "Q3": q3,
            "IQR": iqr,
            "Amplitude": serie.max() - serie.min(),
            "Desvio padrão": serie.std(ddof=1) if len(serie) > 1 else None,
            "Outliers": ", ".join(outliers) if outliers else "Nenhum",
        })
    return pd.DataFrame(resultado)


st.sidebar.header("Filtros")
try:
    dados = carregar_dados()
except Exception as erro:
    st.error(f"Não consegui abrir os dados: {erro}")
    st.info("No terminal, execute: python etl_etnia_raca.py")
    st.stop()

arquivo = st.sidebar.file_uploader("Carregar CSV ou Excel (opcional)", type=["csv", "xlsx"])
if arquivo is not None:
    try:
        dados = pd.read_excel(arquivo) if arquivo.name.endswith(".xlsx") else pd.read_csv(arquivo)
    except Exception as erro:
        st.error(f"Problema ao ler o arquivo: {erro}")
        st.stop()

colunas = {"UF", "Regiao", "Cor_ou_raca", "Populacao"}
if not colunas.issubset(dados.columns):
    st.error("Faltam colunas: " + ", ".join(sorted(colunas - set(dados.columns))))
    st.stop()

# Agrupa uma única linha por estado/categoria e recalcula os percentuais.
dados = dados.groupby(["UF", "Regiao", "Cor_ou_raca"], as_index=False)["Populacao"].sum()
dados["Total_UF"] = dados.groupby("UF")["Populacao"].transform("sum")
dados["Percentual"] = 100 * dados["Populacao"] / dados["Total_UF"]

regiao = st.sidebar.selectbox("Região", ["Brasil"] + sorted(dados["Regiao"].dropna().unique().tolist()))
base = dados.copy() if regiao == "Brasil" else dados.loc[dados["Regiao"] == regiao].copy()
estado = st.sidebar.selectbox("Estado", ["Todos"] + sorted(base["UF"].dropna().unique().tolist()))
if estado != "Todos":
    base = base.loc[base["UF"] == estado].copy()

if base.empty:
    st.warning("Não há dados para este filtro.")
    st.stop()

# Esta frase permite verificar de imediato se a seleção está sendo aplicada.
n_ufs = base["UF"].nunique()
st.info(f"Exibindo: {regiao} | Estado: {estado} | {n_ufs} UF(s)")

st.subheader("População por cor ou raça")
resumo = base.groupby("Cor_ou_raca", as_index=False)["Populacao"].sum()
resumo["Percentual"] = 100 * resumo["Populacao"] / resumo["Populacao"].sum()
resumo["Cor_ou_raca"] = pd.Categorical(resumo["Cor_ou_raca"], categories=CATEGORIAS, ordered=True)
resumo = resumo.sort_values("Cor_ou_raca")
fig = px.bar(resumo, x="Cor_ou_raca", y="Percentual", text="Percentual",
             color_discrete_sequence=["#7059A3"],
             labels={"Cor_ou_raca": "Cor ou raça", "Percentual": "Porcentagem (%)"})
fig.update_traces(texttemplate="%{text:.1f}%", textposition="outside")
fig.update_layout(showlegend=False)
st.plotly_chart(fig, use_container_width=True)

st.subheader("Comparação entre estados")
categoria = st.selectbox("Cor ou raça para comparar", CATEGORIAS, index=3)
comparacao = base.loc[base["Cor_ou_raca"] == categoria].sort_values("Percentual")
fig2 = px.bar(comparacao, x="Percentual", y="UF", orientation="h",
              labels={"Percentual": "Porcentagem (%)", "UF": "Estado"},
              color_discrete_sequence=["#528577"])
fig2.update_layout(height=max(300, 27 * len(comparacao)))
st.plotly_chart(fig2, use_container_width=True)

st.subheader("Estatísticas por estado")
st.caption(f"Cálculos feitos apenas com os {n_ufs} estado(s) selecionado(s).")
if n_ufs == 1:
    st.write("Apenas um estado selecionado. Seguem seus percentuais por cor ou raça:")
    st.dataframe(base[["Cor_ou_raca", "Percentual"]].rename(
        columns={"Cor_ou_raca": "Cor ou raça", "Percentual": "Porcentagem (%)"}
    ).round(2), hide_index=True, use_container_width=True)
else:
    # O cálculo NÃO consulta a base original e não importa a função do ETL.
    tabela = calcular_estatisticas(base)
    st.dataframe(tabela.round(2), hide_index=True, use_container_width=True)

st.subheader("Boxplot")
if n_ufs > 1:
    st.plotly_chart(px.box(base, x="Cor_ou_raca", y="Percentual", points="outliers",
                           labels={"Cor_ou_raca": "Cor ou raça", "Percentual": "Porcentagem (%)"}),
                    use_container_width=True)
else:
    st.caption("Selecione mais de um estado para comparar a dispersão no boxplot.")

st.subheader("Análise")
st.write("Os percentuais por cor ou raça variam entre os estados brasileiros. "
         "A comparação ajuda a compreender diferenças na composição da população.")

st.subheader("Dados utilizados")
st.dataframe(base.round(2), hide_index=True, use_container_width=True)
st.download_button("Baixar CSV filtrado", base.to_csv(index=False).encode("utf-8-sig"),
                   "etnia_raca_filtrado.csv", mime="text/csv")
st.caption("Fonte: IBGE - Censo Demográfico 2022, tabela SIDRA 9605.")
