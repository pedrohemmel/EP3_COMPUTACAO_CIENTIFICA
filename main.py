import simpy
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from scipy.stats import norm
from scipy.stats import expon

#Cores para aplica nos prints do console
class bcolors:
  HEADER = '\033[95m'
  OKCYAN = '\033[96m'
  OKGREEN = '\033[92m'
  WARNING = '\033[93m'
  ENDC = '\033[0m'


def plotaFuncaoExponencial(quantidadeClientes, tempoPorQuantidadeDClientes):
  fig, ax = plt.subplots()
  x = np.random.exponential(quantidadeClientes, tempoPorQuantidadeDClientes)
  ax.text(quantidadeClientes, 400, r'$\lambda=' + str(quantidadeClientes) + '$')
  ax.hist(x, edgecolor="white")
  ax.set_xlabel('Eventos')
  ax.set_ylabel('Ocorrências')
  ax.set_title('Exponencial')
  ax.grid()

  fig.show()

def distribuicao_chegada_de_clientes():
  tempo_do_proximo_cliente = expon.rvs(scale = MEDIA_CHEGADA_CLIENTES, size = 1)
  return tempo_do_proximo_cliente

def salva_info_da_fila(env, chamada):
  horario_medicao = env.now
  tamanho_da_fila_agora = len(chamada.queue)
  horarios_nas_filas.append(horario_medicao)
  tamanho_da_fila.append(tamanho_da_fila_agora)

  return horario_medicao

def calcula_tempo_na_chamada(env, horario_chegada):
  horario_saida = env.now
  saidas.append(horario_saida)
  tempo_total = horario_saida - horario_chegada
  in_system.append(tempo_total)

# pega o tempo de chamada do cliente
def tempo_de_chamada_cliente():
  return norm.rvs(loc = MEDIA_TEMPO_ATENDIMENTO_CLIENTE, 
                  scale = DESVIO_PADRAO_TEMPO_ATENDIMENTO_CLIENTE, 
                  size = 1)


# listas de horários de chegada e saída dOS clientes
chegadas, saidas = [],[]
# listas de horários de chegada e saída das filas
in_queue, in_system  = [],[]
# tempo na fila e tamanho das fulas
horarios_nas_filas, tamanho_da_fila = [],[]

MEDIA_CHEGADA_CLIENTES = 3
MEDIA_TEMPO_ATENDIMENTO_CLIENTE = 3.0
DESVIO_PADRAO_TEMPO_ATENDIMENTO_CLIENTE = 0.5

# Função que recebe novos clientes na central telefônica
def chegada_dos_clientes(env):
    # ID para cada ciente
    cliente_id = 0

    while True:
       ## tempo de chegada do proximo cliente
       tempo_do_proximo_cliente = distribuicao_chegada_de_clientes()
       # espera pelo próximo cliente
       yield env.timeout(tempo_do_proximo_cliente)

       #cliente chegou, marca o tempo e guarda o tempo de chegada
       tempo_de_chegada = env.now
       chegadas.append(tempo_de_chegada)
       cliente_id += 1
       print(f"{bcolors.WARNING}%3d Entrou na central telefônica %.2f.{bcolors.ENDC}"  % (cliente_id, tempo_de_chegada))
       
       # executa a chamada
       env.process(chamada(env, cliente_id, tempo_de_chegada))


# executa a chamada do cliente
def chamada(env, cliente_id, horario_chegada):
    with linhas_de_chamada.request() as req:
        print(f"{bcolors.OKCYAN}%3d Entrou na fila em %.2f.{bcolors.ENDC}" % (cliente_id, env.now))
        horario_entrada_da_fila = salva_info_da_fila(env, linhas_de_chamada)
        yield req # espera a chamada ser liberada

        print(f"{bcolors.OKCYAN}%3d saiu da fila em %.2f{bcolors.ENDC}" % (cliente_id, env.now))
        horario_saida_da_fila = salva_info_da_fila(env, linhas_de_chamada)

        # Fazendo a conta de horario de entrada e saida na fila para análises
        tempo_na_fila = horario_saida_da_fila - horario_entrada_da_fila
        in_queue.append(tempo_na_fila)

        # Execução da chamada do cliente
        tempo_chamada = tempo_de_chamada_cliente()
        yield env.timeout(tempo_chamada)
        print(f"{bcolors.OKGREEN}%3d permaneceu por %.2f{bcolors.ENDC}" % (cliente_id, tempo_chamada))

        # tempo total da operacao da chamada + fila
        calcula_tempo_na_chamada(env, horario_chegada)

# Simulação irá demorar 100 tempos
TEMPO_DE_SIMULACAO  = 300

np.random.seed(seed = 1)

## prepara o ambiente
env = simpy.Environment()

## Definindo recursos: Quantidade de balanças disponíveis
QUANTIDADE_DE_LINHAS = 1
linhas_de_chamada = simpy.Resource(env, capacity = QUANTIDADE_DE_LINHAS)

env.process(chegada_dos_clientes(env))

# Roda a simulação
env.run(until = TEMPO_DE_SIMULACAO)

# Análise dos resultados
df1 = pd.DataFrame(horarios_nas_filas, columns = ['horario'])
df2 = pd.DataFrame(tamanho_da_fila, columns = ['tamanho'])
df3 = pd.DataFrame(chegadas, columns = ['chegadas'])
df4 = pd.DataFrame(saidas, columns = ['partidas'])

df_tamanho_da_fila = pd.concat([df1, df2], axis = 1)
df_entrada_saida = pd.concat([df3, df4], axis = 1)

# Gráfico com as entradas e saídas dos clientes
fig, ax = plt.subplots()
fig.set_size_inches(10, 5.4)

x1, y1 = list(df_entrada_saida['chegadas'].keys()), df_entrada_saida['chegadas']
x2, y2 = list(df_entrada_saida['partidas'].keys()), df_entrada_saida['partidas']

ax.plot(x1, y1, color='blue', marker="o", linewidth=0, label="Chegada")
ax.plot(x2, y2, color='red', marker="o", linewidth=0, label="Saída")
ax.set_xlabel('Tempo')
ax.set_ylabel('Cliente ID')
ax.set_title("Chegadas & Saídas na Central Telefônica")
ax.legend()

fig.show()


NUMERO_DE_DESISTENTES  = 4

def media_fila(df_tamanho_fila):
  df_tamanho_fila['delta'] = df_tamanho_fila['horario'].shift(-1) - df_tamanho_fila['horario']
  df_tamanho_fila = df_tamanho_fila[0:-1]
  return np.average(df_tamanho_fila['tamanho'], weights=df_tamanho_fila['delta'])

def utilizacao_servico(df_tamanho_fila):
   soma_servico_livre = df_tamanho_fila[df_tamanho_fila['tamanho']==0]['delta'].sum()
   # processo começa com o serviço vazio
   primeiro_evento =  df_tamanho_fila['horario'].iloc[0]
   soma_servico_livre = soma_servico_livre + primeiro_evento
   return round((1 - soma_servico_livre / TEMPO_DE_SIMULACAO) * 100, 2)

## Encontra a procentagem de caminhões que não puderam esperar
def porcetagem_de_nao_esperaram(df_tamanho_fila):
   soma_nao_esperaram = df_tamanho_fila[df_tamanho_fila['tamanho'] >= NUMERO_DE_DESISTENTES]['delta'].sum()
   return round((soma_nao_esperaram / TEMPO_DE_SIMULACAO) * 100, 2)

print('\n\nO tempo médio na fila é de %.2f'  % (np.mean(in_queue)))
print('\nO tempo médio no sistema é %.2f' % (np.mean(in_system)))

print("\nO número médio de clientes na fila é %.2f" %  (media_fila(df_tamanho_da_fila)))
print('\nA utilizacao do serviço é %.2f' % (utilizacao_servico(df_tamanho_da_fila)) + '%' )

print('\nA probabilidade dos clientes que não podem esperar na fila é %.2f' % (porcetagem_de_nao_esperaram(df_tamanho_da_fila)) + '%')
