"""
Módulo Parsers - Funções para análise de dados de entrada em vários formatos.
"""

import json

def parse_json(file_path):
    """Lê um arquivo JSON e retorna os dados como um dicionário."""
    with open(file_path, 'r') as file:
        data = json.load(file)
    return data

def parse_csv(file_path):
    """Lê um arquivo CSV e retorna os dados como uma lista de dicionários."""
    import csv
    with open(file_path, 'r') as file:
        reader = csv.DictReader(file)
        data = [row for row in reader]
    return data

def parse_txt(file_path):
    """Lê um arquivo de texto e retorna os dados como uma lista de linhas."""
    with open(file_path, 'r') as file:
        data = file.readlines()
    return [line.strip() for line in data]
    
def parse_data(file_path):
    """Determina o formato do arquivo e chama a função de análise apropriada."""
    if file_path.endswith('.json'):
        return parse_json(file_path)
    elif file_path.endswith('.csv'):
        return parse_csv(file_path)
    elif file_path.endswith('.txt'):
        return parse_txt(file_path)
    else:
        raise ValueError("Formato de arquivo não suportado.")
"""