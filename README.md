# Simulador de Cache em Python

Simulador de memória cache que suporta diferentes configurações e políticas de substituição:  
- Associatividade (número de conjuntos e vias)  
- Tamanho do bloco  
- Políticas: Random (R), FIFO (F) e LRU (L)

Este simulador lê um arquivo binário contendo endereços de memória (32 bits) e simula acessos à cache, gerando estatísticas detalhadas de acertos e tipos de misses.

---

## Funcionalidades

- Suporte a caches totalmente associativas e conjunto-associativas  
- Políticas de substituição: Random, FIFO e LRU  
- Classificação detalhada dos misses: compulsório, de capacidade e de conflito  
- Validação dos parâmetros de entrada (potências de 2, políticas válidas, etc)  
- Saída customizável (formato detalhado ou compacto)

---
## Requisitos

- Python 3.6 ou superior  

---

## Estrutura do código

- `SimuladorCache`: classe principal que implementa a cache e suas operações  
- `ler_arquivo_binario`: função que lê o arquivo binário de endereços  
- `main`: função que trata argumentos, executa a simulação e imprime resultados

---

## Informações adicionais

- O endereço de memória é tratado como um inteiro de 32 bits  
- O simulador calcula automaticamente os bits de offset, índice e tag a partir dos parâmetros fornecidos  
- A fila FIFO é implementada com `collections.deque`  
- Os contadores para LRU são atualizados a cada acesso
  
---
## Como usar

```bash
python cache_simulator.py <nsets> <bsize> <assoc> <substituição> <flag_saida> <arquivo_de_entrada> ```
