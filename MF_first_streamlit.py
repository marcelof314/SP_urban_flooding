import streamlit as st
import geopandas as gpd
import pandas as pd
import matplotlib.pyplot as plt

# Funções fictícias - substitua pelas suas
def plot_rede_viaria(subprefeitura): pass
def plot_histograma_viagens_perdidas(subprefeitura): pass
def plot_fdp(subprefeitura): pass
def plot_cdp(subprefeitura): pass

# Carregar dados (substitua com os reais)
df = pd.read_csv("dados_subprefeituras.csv")  # Exemplo
subprefeituras = sorted(df['Subprefeitura'].dropna().unique())

# --- Streamlit UI ---
st.set_page_config(layout="wide")
st.title("LPT - Laboratório de Planejamento em Transportes")
st.subheader("Estudos sobre a mobilidade")

# Seleção de subprefeitura
opcao = st.selectbox("Selecione a subprefeitura", options=["Todas", "Top 10", "Top 5"] + subprefeituras)

# Filtragem fictícia (você pode ajustar com base em seus dados)
if opcao == "Todas":
    subprefs_selecionadas = subprefeituras
elif opcao == "Top 10":
    subprefs_selecionadas = subprefeituras[:10]
elif opcao == "Top 5":
    subprefs_selecionadas = subprefeituras[:5]
else:
    subprefs_selecionadas = [opcao]

# Layout 2x2 com 4 gráficos
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### (1,1) Rede viária")
    fig1 = plot_rede_viaria(subprefs_selecionadas)
    st.pyplot(fig1)

with col2:
    st.markdown("#### (1,2) Histograma de viagens perdidas")
    fig2 = plot_histograma_viagens_perdidas(subprefs_selecionadas)
    st.pyplot(fig2)

col3, col4 = st.columns(2)
with col3:
    st.markdown("#### (2,1) Função Densidade de Probabilidade (FDP)")
    fig3 = plot_fdp(subprefs_selecionadas)
    st.pyplot(fig3)

with col4:
    st.markdown("#### (2,2) Função Densidade Acumulada (CDP)")
    fig4 = plot_cdp(subprefs_selecionadas)
    st.pyplot(fig4)
