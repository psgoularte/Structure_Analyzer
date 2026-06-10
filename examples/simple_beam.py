"""
Exemplo: Viga Simples Isostática

Viga bi-apoiada de 6m com carga uniformemente distribuída de 10 kN/m.
Demonstra o uso básico das classes do PEF Analyzer.
"""

import sympy as sp
from pef_analyzer.core.domain.node import Node
from pef_analyzer.core.domain.element import Element
from pef_analyzer.core.domain.support import Support, SupportType
from pef_analyzer.core.domain.load import DistributedLoad
from pef_analyzer.core.solver.analyzer import Analyzer


def main():
    print("=" * 60)
    print("PEF Analyzer - Exemplo: Viga Simples")
    print("=" * 60)
    
    # 1. Criar nós
    print("\n1. Definindo nós...")
    n1 = Node(x=0, y=0, id="A")
    n1.set_support(Support(SupportType.PINNED))
    print(f"   Nó A: {n1} - Apoio Fixo")
    
    n2 = Node(x=6, y=0, id="B")
    n2.set_support(Support(SupportType.ROLLER))
    print(f"   Nó B: {n2} - Apoio Móvel")
    
    # 2. Criar elemento (perfeito, sem material)
    print("\n2. Definindo elemento...")
    beam = Element(
        node_i=n1,
        node_f=n2,
        id="Viga-AB"
    )
    print(f"   {beam}")
    
    # 3. Aplicar cargas
    print("\n3. Aplicando cargas...")
    w = -10.0  # kN/m para baixo
    beam.add_load(DistributedLoad(w_function=w))
    print(f"   Carga distribuída uniforme: w = {w} kN/m")
    
    # 4. Analisar
    print("\n4. Executando análise...")
    analyzer = Analyzer(nodes=[n1, n2], elements=[beam])
    result = analyzer.analyze()
    
    # 5. Resultados
    print("\n" + "=" * 60)
    print("RESULTADOS DA ANÁLISE")
    print("=" * 60)
    
    print(f"\nGrau de Hiperestaticidade: {result.degree_of_indeterminacy}")
    print(f"Estrutura Isostática: {result.isostatic}")
    
    print("\nReações de Apoio:")
    for node_id, reactions in result.reactions.items():
        print(f"  Nó {node_id}:")
        for comp, value in reactions.items():
            unit = "kN" if comp != 'M' else "kN·m"
            if value is not None:
                print(f"    {comp} = {value:.4f} {unit}")
            else:
                print(f"    {comp} = Não resolvido")
    
    print("\nEsforços Internos (Funções Simbólicas):")
    for elem_id, forces in result.internal_forces.items():
        print(f"\n  Elemento {elem_id}:")
        print(f"    N(x) = {sp.pretty(forces.N)}")
        print(f"    V(x) = {sp.pretty(forces.V)}")
        print(f"    M(x) = {sp.pretty(forces.M)}")
        
        # Avaliar em pontos específicos
        x_vals = [0, 1.5, 3, 4.5, 6]
        print(f"\n    Valores numéricos:")
        print(f"    {'x (m)':<10} {'N (kN)':<12} {'V (kN)':<12} {'M (kN·m)':<12}")
        print(f"    {'-'*46}")
        for xv in x_vals:
            N, V, M = forces.evaluate_at(xv)
            print(f"    {xv:<10.1f} {N:<12.4f} {V:<12.4f} {M:<12.4f}")
    
    print("\n" + "=" * 60)


if __name__ == "__main__":
    main()
