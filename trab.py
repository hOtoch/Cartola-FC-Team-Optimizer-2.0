import requests
import json as json
import pandas as pd
import gurobipy as gp
from gurobipy import GRB

url_table = "https://api.football-data.org/v4/competitions/BSA/standings?season=2024"

headers = {
  'X-Auth-Token': 'cede0c34a4a54ca4a4bfe9bdd942b518',
}

response = requests.request("GET", url, headers=headers)

table = response.json()['standings'][0]['table']

df_table = pd.DataFrame(table)

# Passo 1: Obter dados da API do Cartola FC
url_atletas = "https://api.cartolafc.globo.com/atletas/mercado"
resposta_atletas = requests.get(url_atletas)
result_json = json.loads(resposta_atletas.content)

# Filtrar os jogadores conforme a condição de estarem "prováveis" (status_id == 7)
atletas_filter = []

for atleta in result_json['atletas']:
    if atleta['status_id'] == 7:  # 7 indica que o jogador está "Provável"
        atletas_filter.append({
            'id': atleta['atleta_id'],
            'apelido': atleta['apelido'],
            'posicao': result_json['posicoes'][str(atleta['posicao_id'])]['nome'],
            'preco': atleta['preco_num'],
            'media': atleta['media_num'],
        })

# Convertendo a lista filtrada em dicionários para uso no modelo
ids = [atleta['id'] for atleta in atletas_filter]
medias = {atleta['id']: atleta['media'] for atleta in atletas_filter}
precos = {atleta['id']: atleta['preco'] for atleta in atletas_filter}
posicoes = {atleta['id']: atleta['posicao'] for atleta in atletas_filter}
apelidos = {atleta['id']: atleta['apelido'] for atleta in atletas_filter}

# Definição das restrições
orcamento = 100.0  # Orçamento máximo
num_jogadores_total = 11
num_goleiros = 1
num_zagueiros = 2
num_laterais = 2
num_meias = 3
num_atacantes = 3

# Inicializa o modelo
model = gp.Model("time_futebol_cartola")

# Adiciona as variáveis de decisão
x = model.addVars(ids, vtype=GRB.BINARY, name="x")

# Define a função objetivo: maximizar a média total do time
model.setObjective(gp.quicksum(medias[j] * x[j] for j in ids), GRB.MAXIMIZE)

# Adiciona a restrição de orçamento
model.addConstr(gp.quicksum(precos[j] * x[j] for j in ids) <= orcamento, "Orcamento")

# Adiciona a restrição do número total de jogadores
model.addConstr(gp.quicksum(x[j] for j in ids) == num_jogadores_total, "Total_Jogadores")

# Adiciona as restrições para cada posição
model.addConstr(gp.quicksum(x[j] for j in ids if posicoes[j] == 'Goleiro') == num_goleiros, "Goleiros")
model.addConstr(gp.quicksum(x[j] for j in ids if posicoes[j] == 'Zagueiro') == num_zagueiros, "Zagueiros")
model.addConstr(gp.quicksum(x[j] for j in ids if posicoes[j] == 'Lateral') == num_laterais, "Laterais")
model.addConstr(gp.quicksum(x[j] for j in ids if posicoes[j] == 'Meia') == num_meias, "Meias")
model.addConstr(gp.quicksum(x[j] for j in ids if posicoes[j] == 'Atacante') == num_atacantes, "Atacantes")

# Resolve o modelo
model.optimize()

# Verifica o status da solução
if model.status == GRB.OPTIMAL:
    print("Solução Ótima Encontrada")
    for j in ids:
        if x[j].x > 0.5:  # Verifica se o jogador foi selecionado
            print(f"Jogador: {apelidos[j]}, Posição: {posicoes[j]}, Média: {medias[j]}, Preço: {precos[j]}")
else:
    print("Não foi possível encontrar uma solução ótima.")
    
    
