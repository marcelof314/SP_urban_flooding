import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import geopandas as gpd
import osmnx as ox
from matplotlib import cm 
from scipy.stats import gaussian_kde

st.set_page_config(layout="wide")

# Carregar os dados
@st.cache_data
def carregar_dados():
    return pd.read_csv("dados_subprefeituras.csv")

#df = carregar_dados()
subprefeituras = [
    'CASA VERDE-CACHOEIRINHA', 'LAPA', 'SE', 'SANTANA-TUCURUVI',
    'PINHEIROS', 'VILA MARIA-VILA GUILHERME', 'MOOCA',
    'SAO MIGUEL', 'ARICANDUVA-FORMOSA-CARRAO', 'SANTO AMARO',
    'FREGUESIA-BRASILANDIA','PIRITUBA-JARAGUA', 'BUTANTA', 'JABAQUARA',
    'ITAQUERA', 'CAMPO LIMPO', 'PENHA', 'VILA MARIANA', 'ERMELINO MATARAZZO','PERUS',
    'GUAIANASES', 'PARELHEIROS', 'CIDADE TIRADENTES', 'M BOI MIRIM',
    'VILA PRUDENTE', 'IPIRANGA', 'ITAIM PAULISTA', 'CAPELA DO SOCORRO',
    'SAPOPEMBA', 'JACANA-TREMEMBE', 'CIDADE ADEMAR', 'SAO MATEUS']

# Listar subprefeituras
#subprefeituras = sorted(df['Subprefeitura'].dropna().unique())

# --- Funções de Plotagem ---
def plot_rede_viaria(subprefs):
    subprefeituras_shp = '/Users/marcelofernandes/Library/CloudStorage/GoogleDrive-marcelo.fernandes@alumni.usp.br/.shortcut-targets-by-id/1M--OnzbTYagrNv5Ss9fjWlBxCMmasz-Y/10_Mestrado_2021_Marcelo Fernandes/8_Dados/SIRGAS_SHP_subprefeitura/SIRGAS_SHP_subprefeitura_polygon.shp'
    gdf_sp_filtrado = gpd.read_file(subprefeituras_shp)
    
    # Dados da subprefeitura
    linha_sp = gdf_sp_filtrado[gdf_sp_filtrado['sp_nome'].isin(subprefs)].iloc[0]
    nome_sp = linha_sp['sp_nome']

    # Verifica e define o CRS
    if gdf_sp_filtrado.crs is None:
        gdf_sp_filtrado.set_crs(epsg=4326, inplace=True)

    # Extrai a geometria
    poligono = linha_sp.geometry

    # Certifique-se de que o polígono está em EPSG:4326
    if gdf_sp_filtrado.crs.to_epsg() != 4326:
        poligono = gdf_sp_filtrado.to_crs(epsg=4326).loc[linha_sp.name].geometry

    # Obtém o grafo
    G_baseline = ox.graph_from_polygon(poligono, network_type="drive")
    G_baseline = ox.routing.add_edge_speeds(G_baseline, fallback=50)

    node_baseline, edges_baseline = ox.graph_to_gdfs(G_baseline)

    # Verificar o CRS atual
    print("CRS atual do edges_baseline:", edges_baseline.crs)

    # Reprojetar para EPSG:31983
    edges_baseline_reprojected = edges_baseline.to_crs(epsg=31983)

    velocidades = [data['speed_kph'] for _, _, data in G_baseline.edges(data=True)]

    norm = mcolors.Normalize(vmin=min(velocidades), vmax=max(velocidades))
    cmap = cm.viridis

    edge_colors = [cmap(norm(v)) for v in velocidades]

    fig, ax = ox.plot_graph(
        G_baseline,
        edge_color=edge_colors,
        node_size=5,
        edge_linewidth=2
    )

    ax.set_title("Rede Viária (simulada)")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    return fig

def plot_histograma_viagens_perdidas(subprefs):
    fig, ax = plt.subplots()
    df_sel = df[df['Subprefeitura'].isin(subprefs)]
    ax.hist(df_sel['Viagens_Perdidas'], bins=20, color='orange', edgecolor='black')
    ax.set_title("Histograma de Viagens Perdidas")
    ax.set_xlabel("Nº de Viagens Perdidas")
    ax.set_ylabel("Frequência")
    return fig

def plot_fdp(subprefs):
    fig, ax = plt.subplots()
    df_sel = df[df['Subprefeitura'].isin(subprefs)]
    valores = df_sel['Resiliencia'].dropna()
    if not valores.empty:
        kde = gaussian_kde(valores)
        x_vals = np.linspace(valores.min(), valores.max(), 100)
        ax.plot(x_vals, kde(x_vals), color='green')
    ax.set_title("Função Densidade de Probabilidade (Resiliência)")
    ax.set_xlabel("Resiliência")
    ax.set_ylabel("Densidade")
    return fig

def plot_cdp(subprefs):
    fig, ax = plt.subplots()
    df_sel = df[df['Subprefeitura'].isin(subprefs)]
    valores = df_sel['Resiliencia'].dropna().sort_values()
    if not valores.empty:
        y_vals = np.linspace(0, 1, len(valores))
        ax.step(valores, y_vals, where='post', color='blue')
    ax.set_title("Função Densidade Acumulada (Resiliência)")
    ax.set_xlabel("Resiliência")
    ax.set_ylabel("Probabilidade Acumulada")
    return fig

# --- Interface Streamlit ---
st.title("LPT - Laboratório de Planejamento em Transportes")
st.subheader("Estudos sobre a mobilidade")

# Seleção de subprefeitura
opcao = st.selectbox("Selecione a subprefeitura", options=subprefeituras)

# Filtrar subprefeituras
subprefs_selecionadas = [opcao]

# Layout 2x2
col1, col2 = st.columns(2)
with col1:
    st.markdown("#### Rede viária")
    st.pyplot(plot_rede_viaria(subprefs_selecionadas))

#with col2:
#    st.markdown("#### Histograma de viagens perdidas")
#    st.pyplot(plot_histograma_viagens_perdidas(subprefs_selecionadas))

#col3, col4 = st.columns(2)
#with col3:
#    st.markdown("#### (2,1) Função Densidade de Probabilidade (FDP)")
#    st.pyplot(plot_fdp(subprefs_selecionadas))

#with col4:
#    st.markdown("#### (2,2) Função Densidade Acumulada (CDP)")
    st.pyplot(plot_cdp(subprefs_selecionadas))
