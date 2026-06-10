"""
Módulo persistence - Serialização e desserialização de projetos em JSON.

Permite salvar e carregar estruturas (nós, elementos, cargas, apoios) em formato JSON.
"""

from __future__ import annotations
import json
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..core.domain.node import Node
from ..core.domain.element import Element, ElementType
from ..core.domain.support import Support, SupportType
from ..core.domain.load import PointLoad, DistributedLoad, LoadDirection


def _support_to_dict(support: Optional[Support]) -> Optional[Dict[str, Any]]:
    """Converte Support para dicionário."""
    if support is None:
        return None
    return {
        "type": support.support_type.name,
        "angle": support.angle,
    }


def _support_from_dict(data: Optional[Dict[str, Any]]) -> Optional[Support]:
    """Cria Support a partir de dicionário."""
    if data is None:
        return None
    support_type = SupportType[data["type"]]
    angle = data.get("angle")
    return Support(support_type=support_type, angle=angle)


def _point_load_to_dict(load: PointLoad) -> Dict[str, Any]:
    """Converte PointLoad para dicionário."""
    return {
        "type": "point",
        "fx": load.fx,
        "fy": load.fy,
        "fz": load.fz,
        "position": load.position,
    }


def _point_load_from_dict(data: Dict[str, Any]) -> PointLoad:
    """Cria PointLoad a partir de dicionário."""
    return PointLoad(
        fx=data.get("fx", 0.0),
        fy=data.get("fy", 0.0),
        fz=data.get("fz", 0.0),
        position=data.get("position"),
    )


def _distributed_load_to_dict(load: DistributedLoad) -> Dict[str, Any]:
    """Converte DistributedLoad para dicionário."""
    w_str = str(load.w_function)
    return {
        "type": "distributed",
        "w_function": w_str,
        "direction": load.direction.name,
        "start_position": load.start_position,
        "end_position": load.end_position,
    }


def _distributed_load_from_dict(data: Dict[str, Any]) -> DistributedLoad:
    """Cria DistributedLoad a partir de dicionário."""
    import sympy as sp
    x = sp.Symbol('x')
    w_expr = data["w_function"]
    try:
        w_function = sp.sympify(w_expr)
    except (sp.SympifyError, Exception):
        # Fallback: tentar avaliar como float
        try:
            w_function = float(w_expr)
        except ValueError:
            w_function = 0.0
    return DistributedLoad(
        w_function=w_function,
        direction=LoadDirection[data["direction"]],
        start_position=data.get("start_position", 0.0),
        end_position=data.get("end_position"),
    )


def _node_to_dict(node: Node) -> Dict[str, Any]:
    """Converte Node para dicionário."""
    return {
        "id": node.id,
        "x": node.x,
        "y": node.y,
        "support": _support_to_dict(node.support),
        "loads": [_point_load_to_dict(l) for l in node.loads],
    }


def _node_from_dict(data: Dict[str, Any]) -> Node:
    """Cria Node a partir de dicionário."""
    node = Node(
        x=data["x"],
        y=data["y"],
        id=data.get("id"),
    )
    node.support = _support_from_dict(data.get("support"))
    for load_data in data.get("loads", []):
        node.add_load(_point_load_from_dict(load_data))
    return node


def _element_to_dict(element: Element) -> Dict[str, Any]:
    """Converte Element para dicionário."""
    return {
        "id": element.id,
        "node_i_id": element.node_i.id,
        "node_f_id": element.node_f.id,
        "element_type": element.element_type.name,
        "loads": [_distributed_load_to_dict(l) for l in element.loads],
        "point_loads": [_point_load_to_dict(l) for l in element.point_loads],
    }


def _element_from_dict(data: Dict[str, Any], nodes: Dict[str, Node]) -> Element:
    """Cria Element a partir de dicionário e dicionário de nós."""
    node_i = nodes[data["node_i_id"]]
    node_f = nodes[data["node_f_id"]]
    elem = Element(
        node_i=node_i,
        node_f=node_f,
        id=data.get("id"),
        element_type=ElementType[data["element_type"]],
    )
    for load_data in data.get("loads", []):
        elem.add_load(_distributed_load_from_dict(load_data))
    for pload_data in data.get("point_loads", []):
        elem.add_point_load(_point_load_from_dict(pload_data))
    return elem


def save_project(nodes: List[Node], elements: List[Element], filepath: str) -> None:
    """
    Salva um projeto em arquivo JSON.
    
    Args:
        nodes: Lista de nós da estrutura.
        elements: Lista de elementos da estrutura.
        filepath: Caminho do arquivo JSON.
    """
    data = {
        "version": "1.0",
        "nodes": [_node_to_dict(n) for n in nodes],
        "elements": [_element_to_dict(e) for e in elements],
    }
    path = Path(filepath)
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def load_project(filepath: str) -> tuple[List[Node], List[Element]]:
    """
    Carrega um projeto de arquivo JSON.
    
    Args:
        filepath: Caminho do arquivo JSON.
        
    Returns:
        Tupla (nodes, elements) com a estrutura carregada.
    """
    path = Path(filepath)
    data = json.loads(path.read_text(encoding="utf-8"))
    
    nodes = [_node_from_dict(n) for n in data["nodes"]]
    nodes_dict = {n.id: n for n in nodes}
    
    elements = [_element_from_dict(e, nodes_dict) for e in data["elements"]]
    
    return nodes, elements
