import time
from tqdm import tqdm
import osmnx as ox
import re
import pandas as pd
# Função para extrair o número que aparece depois de "h_" ou "max_"
def extrair_numero(nome):
    match = re.search(r'(?:h_|max_)(\d+)', nome)  # Captura o número após "h_" ou "max_"
    return int(match.group(1)) if match else float('inf')  # Retorna um número grande se não encontrar nada

G_dinamico = ox.load_graphml("G_dinamico.graphml")

atributos_tt = set()
    
for _, _, dados in G_dinamico.edges(data=True):
    for atributo in dados.keys():
        if atributo.startswith("tt"):
            atributos_tt.add(atributo)

atributos_tt = [linha for linha in atributos_tt if "speed"not in linha]

#Ordenar a lista pelo número extraído
atributos_tt_ord = sorted(atributos_tt, key=extrair_numero)

# Exibir a lista ordenada
for arquivo in atributos_tt_ord:
    print(arquivo)

# Limitando o tamanho da lista para facilitar o debug
atributos_tt_ord = atributos_tt_ord[6:7]
print(atributos_tt_ord)


# Função auxiliar para calcular tempos de viagem
def calcular_tempo_viagem(gdf, coluna_peso, grafo, **kwargs):
    inicio = time.time()
    tempos, sem_caminho = calcula_caminho_minimo(gdf, 'nearest_node_baseline', grafo, coluna_peso, **kwargs)
    tempo_execucao = time.time() - inicio
    tt_medio = tempo_medio_viagem(tempos) if not tempos.empty else None
    return tt_medio, sem_caminho, len(sem_caminho), tempo_execucao

# Função para processar um atributo específico
def processar_atributo(args):
    coluna, gdf_nos_aproximados, G_dinamico = args  # Desempacota os argumentos
    print(f'Iniciando o cálculo para a referência: {coluna}')
    
    tt_seco, sem_caminho_seco, viagens_ignoradas_seco, tempo_execucao_seco = calcular_tempo_viagem(
        gdf_nos_aproximados, 'tt_speed_kph', G_dinamico
    )

    tt_chuva, sem_caminho_chuva, viagens_ignoradas_chuva, tempo_execucao_chuva = calcular_tempo_viagem(
        gdf_nos_aproximados, coluna, G_dinamico
    )

    tt_seco_mod, _, viagens_ignoradas_mod, tempo_execucao_mod = calcular_tempo_viagem(
        gdf_nos_aproximados, 'tt_speed_kph', G_dinamico, revalida=True, sem_caminho=sem_caminho_chuva
    )

    return {
        'coluna': coluna,
        'tt_seco': tt_seco,
        'tt_chuva': tt_chuva,
        'tt_seco_mod': tt_seco_mod,
        'viagens_ignoradas_seco': viagens_ignoradas_seco,
        'viagens_ignoradas_chuva': viagens_ignoradas_chuva,
        'viagens_ignoradas_mod': viagens_ignoradas_mod,
        'tempo_execucao_seco': tempo_execucao_seco,
        'tempo_execucao_chuva': tempo_execucao_chuva,
        'tempo_execucao_mod': tempo_execucao_mod
    }

# Função auxiliar para calcular tempos de viagem
def calcular_tempo_viagem(gdf, coluna_peso, grafo, **kwargs):
    inicio = time.time()
    tempos, sem_caminho = calcula_caminho_minimo(gdf, 'nearest_node_baseline', grafo, coluna_peso, **kwargs)
    tempo_execucao = time.time() - inicio
    tt_medio = tempo_medio_viagem(tempos) if not tempos.empty else None
    return tt_medio, sem_caminho, len(sem_caminho), tempo_execucao

# Inicializa a lista de resultados
resultados = []

# Loop sobre os atributos
for coluna in tqdm(atributos_tt_ord, desc="Processando atributos", unit='atributo'):
    print(f'Iniciando o cálculo para a referência: {coluna}')
    
    # 1. Cálculo sem chuva
    print('Calculando tempo de viagem SEM CHUVA...')
    tt_seco, sem_caminho_seco, viagens_ignoradas_seco, tempo_execucao_seco = calcular_tempo_viagem(
        gdf_nos_aproximados, 'tt_speed_kph', G_dinamico
    )
    
    # 2. Cálculo com chuva
    print('Calculando tempo de viagem COM CHUVA...')
    tt_chuva, sem_caminho_chuva, viagens_ignoradas_chuva, tempo_execucao_chuva = calcular_tempo_viagem(
        gdf_nos_aproximados, coluna, G_dinamico
    )
    
    # 3. Cálculo sem chuva, modificado
    print('Calculando tempo de viagem SEM CHUVA, MODIFICADO...')
    tt_seco_mod, _, viagens_ignoradas_mod, tempo_execucao_mod = calcular_tempo_viagem(
        gdf_nos_aproximados, 'tt_speed_kph', G_dinamico, revalida=True, sem_caminho=sem_caminho_chuva
    )

    # Adiciona os resultados à lista
    resultados.append({
        'coluna': coluna,
        'tt_seco': tt_seco,
        'tt_chuva': tt_chuva,
        'tt_seco_mod': tt_seco_mod,
        'viagens_ignoradas_seco': viagens_ignoradas_seco,
        'viagens_ignoradas_chuva': viagens_ignoradas_chuva,
        'viagens_ignoradas_mod': viagens_ignoradas_mod,
        'tempo_execucao_seco': tempo_execucao_seco,
        'tempo_execucao_chuva': tempo_execucao_chuva,
        'tempo_execucao_mod': tempo_execucao_mod
    })

# Converte os resultados para um DataFrame
df_resultados_resiliencia = pd.DataFrame(resultados)

def calcula_caminho_minimo(gdf_OD, referencia_OD, G, referencia, revalida=False, sem_caminho=None):
    """
    Calcula caminhos mínimos entre pares de nós em um grafo OSMnx, considerando apenas vias transitáveis.

    Parâmetros:
        gdf_OD: GeoDataFrame - Contém os nós de origem e destino.
        referencia_OD: str - Nome da coluna no gdf_OD com os IDs dos nós.
        G: networkx.MultiDiGraph - Grafo de ruas OSMnx.
        referencia: str - Nome da referência usada para tempo de viagem.
        revalida: bool - Se True, ignora pares já conhecidos sem caminho.
        sem_caminho: set - Conjunto de pares (origem, destino) sem caminho (para revalidação).

    Retorna:
        tempos_e_viagens_arquivo: DataFrame - Resultados das viagens calculadas.
        sem_caminho: set - Atualização dos pares sem caminho.
    """

    if sem_caminho is None:
        sem_caminho = set()

    data_batch = []
    start_time = time.time()
    
    if revalida:
        print(f'Modo revalidação ativado. Ignorando {len(sem_caminho)} pares sem caminho.')

    # Itera sobre todas as combinações de pares de nós
    for node1, node2 in itertools.combinations(gdf_OD[referencia_OD], 2):
        if node1 == node2 or (revalida and (node1, node2) in sem_caminho):
            continue  # Ignorar nós idênticos ou já marcados como sem caminho

        if node1 in G.nodes and node2 in G.nodes:
            try:
                # Obter o número de viagens entre os nós
                num_trips = get_number_of_trips(node1, node2, referencia_OD, matriz_od_25)
                if num_trips > 0:
                    # Usar a função otimizada para calcular o caminho mínimo
                    caminho, tempo = caminho_minimo(G, node1, node2, referencia)

                    if caminho is not None:  # Garantir que existe um caminho
                        weighted_time_rain = tempo * num_trips
                        data_batch.append({
                            'Referência': referencia,
                            'Origem': node1,
                            'Destino': node2,
                            'Num_viagens': num_trips,
                            'Tempo de viagem (min)': tempo / 60,
                            'Número de nós': len(caminho),
                            'Percurso entre nós': list(caminho),
                            'Tempo ponderado (min)': weighted_time_rain / 60
                        })
                    else:
                        sem_caminho.add((node1, node2))  # Registrar nós sem caminho
            except nx.NetworkXNoPath:
                sem_caminho.add((node1, node2))
        else:
            print(f"⚠️ Nó(s) {node1} ou {node2} não encontrado(s) no grafo.")

    # Calcular tempo de processamento
    processing_time = time.time() - start_time
    print(f"Tempo de processamento: {processing_time/60:.2f} minutos")
    print(f'Foram calculadas {len(data_batch)} viagens')
    print('Total de viagens sem conexão:', len(sem_caminho))

    return pd.DataFrame(data_batch), sem_caminho