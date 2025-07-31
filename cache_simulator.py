import sys
import struct
import random
import math
from typing import Any
from collections import deque

class SimuladorCache:
    def __init__(self, num_conjuntos, tamanho_bloco, associatividade, politica_substituicao) -> None:
        # basico da cache
        self.num_conjuntos = num_conjuntos
        self.tamanho_bloco = tamanho_bloco
        self.associatividade = associatividade
        self.politica_substituicao = politica_substituicao
        
        # calculo dos bits pro endereçamento 
        self.num_bits_offset = int(math.log2(tamanho_bloco))  # bits offset dentro do bloco 
        self.num_bits_indice = int(math.log2(num_conjuntos))  # bits indice pro conjunto
        self.num_bits_tag = 32 - self.num_bits_offset - self.num_bits_indice  # restante dos bits pra tag 
        
        # estrutura da cache 
        # matriz pros blocos validos, matriz pras tags do bloco, matriz para controlar contadores - LRU
        self.cache_valido =   [[False for _ in range(associatividade)] for _ in range(num_conjuntos)]
        self.cache_tag =      [[0     for _ in range(associatividade)] for _ in range(num_conjuntos)]
        self.cache_contador = [[0     for _ in range(associatividade)] for _ in range(num_conjuntos)]
        
        # politicas de substituicao
        self.fila_fifo: deque = deque() # fila do fifo 
        self.contador_global = 0        # contador do lru
        
        # ve se a cache ta cheia 
        self.capacidade_total = num_conjuntos * associatividade
        self.slots_ocupados = 0
        
        # ve as estatisticas
        self.total_acessos = 0
        self.acertos = 0
        self.misses_compulsorios = 0
        self.misses_capacidade = 0
        self.misses_conflito = 0
        
    def analisar_endereco(self, endereco) -> tuple:
        """extrai tag, índice e offset do endereço de 32 bits"""
        
        offset = endereco & ((1 << self.num_bits_offset) - 1)
        indice = (endereco >> self.num_bits_offset) & ((1 << self.num_bits_indice) - 1)
        tag = endereco >> (self.num_bits_offset + self.num_bits_indice)
        
        return tag, indice, offset
    
    def buscar_bloco(self, indice, tag) -> int:
        """procura um bloco específico no conjunto indicado pelo indice"""
        for via in range(self.associatividade):
            # confere se o bloco é válido e se a tag coincide
            if self.cache_valido[indice][via] and self.cache_tag[indice][via] == tag:
                return via  # retorna a via onde encontrou o bloco
        return -1  # se o bloco não foi encontrado
    
    def buscar_via_vazia(self, indice) -> int:
        """encontra uma via vazia no conjunto especificado"""
        for via in range(self.associatividade):
            if not self.cache_valido[indice][via]:
                return via  # retorna a primeira via vazia que encontrou
        return -1  #  se não há vias vazias
    
    def cache_esta_cheia(self) -> bool:
        """ve se todos os blocos da cache estão ocupados"""
        for indice_conjunto in range(self.num_conjuntos):
            for via in range(self.associatividade):
                if not self.cache_valido[indice_conjunto][via]:
                    return False  # encontrou ocupado
        return True  # tudo ocupado
    
    def escolher_vitima(self, indice) -> int:
        """seleciona qual bloco será substituido conforme a politica"""
        if self.politica_substituicao == 'R':  # random
            return random.randint(0, self.associatividade - 1)
        elif self.politica_substituicao == 'F':  # FIFO
            return self.fila_fifo.popleft()  # remove e traz o primeiro da fila
        elif self.politica_substituicao == 'L':  # LRU
            menor_contador = float('inf')
            via_vitima = 0
            # encontra a via com menor contador  - que foi usada menos recente
            for via in range(self.associatividade):
                if self.cache_contador[indice][via] < menor_contador:
                    menor_contador = self.cache_contador[indice][via]
                    via_vitima = via
            return via_vitima
        return 0  # via 0
    
    def classificar_miss(self, indice, tag) -> str:
        """classifica o miss"""
        # ve se tem bloco vazio no conjunto atual
        via_vazia = self.buscar_via_vazia(indice)
        
        if via_vazia >= 0:
            # tem bloco vazio no conjunto - sempre é miss compulsório
            return "compulsorio"
        else:
            # não tem bloco vazio no conjunto, precisa fazer substituição
            if self.num_conjuntos == 1:
                # cache totalmente associativa (1 conjunto)
                return "capacidade"
            else:
                # cache conjunto-associativa (multiplos conjuntos)
                if self.cache_esta_cheia():
                    return "capacidade"  # cache completamente cheia
                else:
                    return "conflito"  # tem espaço na cache, mas não tem neste conjunto
    
    def acessar_cache(self, endereco) -> None:
        """simula um acesso a cache com o endereço fornecido"""
        self.total_acessos += 1
        tag, indice, offset = self.analisar_endereco(endereco)
        
        # tenta encontrar o bloco na cache
        via = self.buscar_bloco(indice, tag)
        
        if via >= 0:  # hit
            self.acertos += 1
            # atualiza contador se for hit
            if self.politica_substituicao == 'L':
                self.cache_contador[indice][via] = self.contador_global
                self.contador_global += 1
        else:  # miss
            # classifica o miss
            tipo_miss = self.classificar_miss(indice, tag)
            
            # coloca o contador de acordo com o resultado do miss
            if tipo_miss == "compulsorio":
                self.misses_compulsorios += 1
            elif tipo_miss == "capacidade":
                self.misses_capacidade += 1
            else:  # conflito
                self.misses_conflito += 1
            
            # ve via vazia no conjunto 
            via_vazia = self.buscar_via_vazia(indice)
            
            if via_vazia >= 0:  # se tem vazia
                via = via_vazia
                self.slots_ocupados += 1
                # coloca na fila fifo quando ocupa um bloco vazio
                if self.politica_substituicao == 'F':
                    self.fila_fifo.append(via)
            else:  # precisa substituir um bloco existente
                via = self.escolher_vitima(indice)
                # reinsere na fila fifo após substituir
                if self.politica_substituicao == 'F':
                    self.fila_fifo.append(via)
            
            # instala o novo bloco na cache
            self.cache_valido[indice][via] = True
            self.cache_tag[indice][via] = tag
            
            # atualiza contador lru para o novo bloco
            if self.politica_substituicao == 'L':
                self.cache_contador[indice][via] = self.contador_global
                self.contador_global += 1
    
    def obter_estatisticas(self):
        """calcula e retorna os resultados"""
        
        if self.total_acessos == 0:
            return 0, 0, 0, 0, 0, 0
        
        total_misses = self.misses_compulsorios + self.misses_capacidade + self.misses_conflito
        
        # calcula as taxas principais
        taxa_acerto = self.acertos / self.total_acessos
        taxa_miss = total_misses / self.total_acessos
        
        # calcula distribuicao dos tipos de miss
        if total_misses == 0:
            taxa_compulsorio = taxa_capacidade = taxa_conflito = 0
        else:
            taxa_compulsorio = self.misses_compulsorios / total_misses
            taxa_capacidade = self.misses_capacidade / total_misses
            taxa_conflito = self.misses_conflito / total_misses
        
        return self.total_acessos, taxa_acerto, taxa_miss, taxa_compulsorio, taxa_capacidade, taxa_conflito

def ler_arquivo_binario(nome_arquivo) -> list:
    """le endereços do arquivo binário (32 bits cada)"""
    enderecos = []
    try:
        with open(nome_arquivo, 'rb') as arquivo:
            while True:
                # lê 4 bytes (32 bits) do arquivo
                dados = arquivo.read(4)
                if len(dados) < 4:
                    break  # fim
                # converte pra inteiro 
                endereco = struct.unpack('>I', dados)[0]
                enderecos.append(endereco)
    except FileNotFoundError:
        print(f"Erro: Arquivo '{nome_arquivo}' não encontrado.")
        sys.exit(1)
    except Exception as erro:
        print(f"Erro ao ler arquivo: {erro}")
        sys.exit(1)
    
    return enderecos

def main() -> None:
    # ve se o ta certo os argumentos 
    if len(sys.argv) != 7:
        print("Numero de argumentos incorreto. Utilize:")
        print("python cache_simulator.py <nsets> <bsize> <assoc> <substituição> <flag_saida> arquivo_de_entrada")
        sys.exit(1)
    
    # lê os argumentos (parametros)
    try:
        num_conjuntos = int(sys.argv[1])
        tamanho_bloco = int(sys.argv[2])
        associatividade = int(sys.argv[3])
        politica_subst = sys.argv[4]
        flag_saida = int(sys.argv[5])
        arquivo_entrada = sys.argv[6]
    except ValueError:
        print("Erro: Parâmetros numéricos inválidos.")
        sys.exit(1)
    
    # valida os parâmetros de entrada
    if num_conjuntos <= 0 or tamanho_bloco <= 0 or associatividade <= 0:
        print("Erro: Parâmetros devem ser positivos.")
        sys.exit(1)
    
    if politica_subst not in ['R', 'F', 'L']:
        print("Erro: Política de substituição deve ser R, F ou L.")
        sys.exit(1)
    
    if flag_saida not in [0, 1]:
        print("Erro: Flag de saída deve ser 0 ou 1.")
        sys.exit(1)
    
    # verifica se num_conjuntos e tamanho_bloco são potências de 2
    if not (num_conjuntos & (num_conjuntos - 1)) == 0:
        print("Erro: Número de conjuntos deve ser potência de 2.")
        sys.exit(1)
    
    if not (tamanho_bloco & (tamanho_bloco - 1)) == 0:
        print("Erro: Tamanho do bloco deve ser potência de 2.")
        sys.exit(1)
    
    # lê os endereços do arquivo BIN
    enderecos = ler_arquivo_binario(arquivo_entrada)
    
    if not enderecos:
        print("Erro: Arquivo de entrada está vazio.")
        sys.exit(1)
    
    # cria e executa 
    simulador = SimuladorCache(num_conjuntos, tamanho_bloco, associatividade, politica_subst)
    
    # endereço de acessp
    for endereco in enderecos:
        simulador.acessar_cache(endereco)
    
    # pega os resultados finais 
    total, taxa_acerto, taxa_miss, taxa_comp, taxa_cap, taxa_conf = simulador.obter_estatisticas()
    
    # resultados
    if flag_saida == 0:
        print(f"========== Estatísticas da Cache ==========")
        print(f"Total de acessos: {total}")
        print(f"Taxa de hits: {taxa_acerto:.4f} ({taxa_acerto*100:.2f}%)")
        print(f"Taxa de misses: {taxa_miss:.4f} ({taxa_miss*100:.2f}%)")
        print(f"Taxa de miss compulsório: {taxa_comp:.4f} ({taxa_comp*100:.2f}%)")
        print(f"Taxa de miss de capacidade: {taxa_cap:.4f} ({taxa_cap*100:.2f}%)")
        print(f"Taxa de miss de conflito: {taxa_conf:.4f} ({taxa_conf*100:.2f}%)")
        print(f"==========================================")
    else:
        # versão compactada
        print(f"{total} {taxa_acerto:.4f} {taxa_miss:.4f} {taxa_comp:.4f} {taxa_cap:.4f} {taxa_conf:.4f}")
 
if __name__ == '__main__':
    main()