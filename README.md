# PEF Analyzer

Software educacional para análise de estruturas isostáticas e hiperestáticas em 2D, desenvolvido com ênfase didática para exibir as funções analíticas (equações) dos esforços internos além dos diagramas.

## Características Principais

- **Cálculo Simbólico**: Utiliza SymPy para gerar funções analíticas exatas de esforços internos
- **Interface Intuitiva**: GUI moderna com PyQt6 e visualização via Matplotlib
- **Vínculos Completos**: Suporte aos 3 gêneros de apoios (1º, 2º e 3º)
- **Cargas Flexíveis**: Aceita cargas pontuais e distribuídas com funções matemáticas arbitrárias
- **Diagramas de Esforços**: Visualização completa de Normal, Cortante e Momento Fletor
- **Equações Analíticas**: Exibição legível das funções N(x), V(x) e M(x) geradas

## Stack Tecnológico

| Componente | Tecnologia |
|------------|------------|
| Linguagem | Python 3.10+ |
| Interface Gráfica | PyQt6 |
| Matemática Simbólica | SymPy |
| Processamento Numérico | NumPy / SciPy |
| Visualização | Matplotlib |
| Gerenciamento de Pacotes | Poetry |

## Instalação

### Pré-requisitos

- Python 3.10 ou superior
- Poetry (gerenciador de dependências)
- pyenv (recomendado para gerenciamento de versões Python)

### Passos

1. Clone o repositório:
```bash
git clone <url-do-repositorio>
cd pef-analyzer
```

2. Configure o ambiente com pyenv (opcional):
```bash
pyenv install 3.11
pyenv local 3.11
```

3. Instale as dependências com Poetry:
```bash
poetry install
```

4. Ative o ambiente virtual:
```bash
# Poetry 2.0+ (recomendado)
poetry env activate

# Ou ative manualmente:
source .venv/bin/activate
```

## Uso

### Executar a aplicação GUI:

```bash
python -m pef_analyzer.gui.app
```

### Exemplo Programático:

```python
from pef_analyzer.core.domain.node import Node
from pef_analyzer.core.domain.element import Element
from pef_analyzer.core.domain.support import Support, SupportType
from pef_analyzer.core.domain.load import PointLoad, DistributedLoad
from pef_analyzer.core.solver.analyzer import Analyzer

# Criar nós
n1 = Node(x=0, y=0, id="A")
n1.set_support(Support(SupportType.FIXED))

n2 = Node(x=4, y=0, id="B")
n2.add_load(PointLoad(fy=-20.0))  # Carga de 20 kN para baixo

# Criar elemento
beam = Element(node_i=n1, node_f=n2, id="Viga")

# Adicionar carga distribuída
import sympy as sp
x = sp.Symbol('x')
beam.add_load(DistributedLoad(w_function=-10 + 2*x))  # Carga variável

# Analisar
analyzer = Analyzer(nodes=[n1, n2], elements=[beam])
result = analyzer.analyze()

# Exibir resultados
print("Reações:", result.reactions)
for elem_id, forces in result.internal_forces.items():
    print(f"\nElemento {elem_id}:")
    print(f"  N(x) = {forces.N}")
    print(f"  V(x) = {forces.V}")
    print(f"  M(x) = {forces.M}")
```

## Arquitetura do Projeto

```
pef_analyzer/
├── core/                   # Núcleo da aplicação
│   ├── domain/             # Classes de domínio (OO)
│   │   ├── node.py         # Classe Node (Nó)
│   │   ├── element.py      # Classe Element (Barra/Viga)
│   │   ├── support.py      # Classes de vínculos
│   │   └── load.py         # Classes de carregamento
│   └── solver/             # Motor de cálculo
│       └── analyzer.py     # Analisador simbólico
├── gui/                    # Interface gráfica
│   ├── main_window.py      # Janela principal
│   └── app.py              # Ponto de entrada
├── utils/                  # Utilitários
└── tests/                  # Testes automatizados
    ├── unit/
    └── integration/
```

## Classes Principais

### Node (Nó)
```python
@dataclass
class Node:
    x: float
    y: float
    id: Optional[str]
    support: Optional[Support]
    loads: List[PointLoad]
```

### Element (Barra/Viga)
```python
@dataclass
class Element:
    node_i: Node
    node_f: Node
    E: float          # Módulo de elasticidade
    A: float          # Área da seção
    I: float          # Momento de inércia
    loads: List[DistributedLoad]
```

### Load (Carga)
```python
# Carga pontual
load = PointLoad(fx=10.0, fy=-20.0)

# Carga distribuída com função simbólica
import sympy as sp
x = sp.Symbol('x')
dist_load = DistributedLoad(w_function=5*x + 10)  # Carga linear
```

### Analyzer (Motor de Cálculo)
```python
analyzer = Analyzer(nodes=nodes, elements=elements)
result = analyzer.analyze()
```

## Funcionalidades Previstas

- [x] Estrutura de dados orientada a objetos
- [x] Classes Node, Element, Support, Load
- [x] Motor de cálculo simbólico com SymPy
- [x] Interface gráfica básica PyQt6
- [ ] Análise de estruturas hiperestáticas
- [ ] Exportação de relatórios
- [ ] Salvamento/carregamento de projetos

## Solução de Problemas

### Poetry Shell não funciona

Se `poetry shell` não estiver disponível (Poetry 2.0+):

```bash
# Use o novo comando
poetry env activate

# Ou ative manualmente
source .venv/bin/activate
```

### Dependências não instalam

```bash
# Limpe o cache e reinstale
poetry cache clear --all pypi
poetry install
```

### Erro de versão Python

```bash
# Verifique a versão
python --version

# Use pyenv para gerenciar versões
pyenv install 3.11
pyenv local 3.11
```
# Structure_Analyzer
