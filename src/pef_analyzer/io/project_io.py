"""
Módulo project_io - Manipulação de entrada/saída de arquivos de projeto.

Este módulo contém funções para salvar e carregar dados de projeto,
incluindo esforços, forças ativas e reativas, e as propriedades das barras e nós.
"""

import json
import os

def load_project(file_path):
    """Carrega os dados do projeto a partir de um arquivo JSON."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"O arquivo {file_path} não foi encontrado.")
    
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    return data

def save_project(file_path, data):
    """Salva os dados do projeto em um arquivo JSON."""
    with open(file_path, 'w') as file:
        json.dump(data, file, indent=4)

def validate_project_data(data):
    """Valida os dados do projeto para garantir que estão completos e corretos."""
    required_keys = ['nodes', 'bars', 'loads']
    for key in required_keys:
        if key not in data:
            raise ValueError(f"Dados do projeto estão faltando a chave: {key}")
    
    # Adicione mais validações conforme necessário
    return True
