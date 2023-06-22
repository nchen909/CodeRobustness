import json
import networkx as nx
from tree_sitter import Language, Parser
from collections import deque

def ast_to_graph(node, source_code):
    G = nx.Graph()
    queue = deque([(node, None)])
    
    while queue:
        current_node, parent_node = queue.popleft()
        node_id = (current_node.start_byte, current_node.end_byte)
        current_node_data = {
            'type': current_node.type,
            'value': source_code[current_node.start_byte:current_node.end_byte].decode('utf-8'),
            'start_byte': current_node.start_byte,
            'end_byte': current_node.end_byte,
        }
        G.add_node(node_id, **current_node_data)
        
        if parent_node is not None:
            parent_node_id = (parent_node.start_byte, parent_node.end_byte)
            G.add_edge(node_id, parent_node_id)
        
        for child in current_node.children:
            queue.append((child, current_node))
    
    return G

def parse_code_to_graph(code, language):
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(bytes(code, 'utf8'))
    root_node = tree.root_node
    return ast_to_graph(root_node, bytes(code, 'utf8'))

# def reconstruct_code_from_bfs_sequence(sequence, graph):
#     reconstructed_code = []
    
#     for item in sequence:
#         node = item['node']
#         # Check if the node is a leaf node
#         if graph.out_degree[node] == 0 and graph.in_degree[node] == 1:
#             reconstructed_code.append(item['value'])
    
#     return ' '.join(reconstructed_code)

import random

def reconstruct_code_from_dfs_sequence(sequence, graph):
    # Find all leaf nodes' parents
    leaf_parents = set()
    for node in graph.nodes:
        if graph.out_degree(node) > 0 and all(graph.out_degree(child) == 0 for child in graph.successors(node)):
            leaf_parents.add(node)

    # Randomly select a parent node and remove it along with its children
    if leaf_parents:
        selected_parent = random.choice(list(leaf_parents))
        children_to_remove = list(graph.successors(selected_parent))
        graph.remove_nodes_from([selected_parent] + children_to_remove)

    # Create a new DFS sequence without the removed nodes
    new_sequence = []
    for node in nx.dfs_tree(graph, list(graph.nodes)[0]):
        new_sequence.append({**graph.nodes[node], 'node': node})

    # Convert the DFS sequence to a code string
    sorted_sequence = sorted(new_sequence, key=lambda x: x['start_byte'])
    reconstructed_code = []
    
    for item in sorted_sequence:
        node = item['node']
        # Check if the node is a leaf node
        if graph.out_degree(node) == 0 and graph.in_degree(node) == 1:
            reconstructed_code.append(item['value'])
    
    return ' '.join(reconstructed_code)



# python_code = 'def print_summary ( status ) status_string = status . to_s . humanize . upcase if status == :success heading ( "Result: " , status_string , :green ) level = :info elsif status == :timed_out heading ( "Result: " , status_string , :yellow ) level = :fatal else heading ( "Result: " , status_string , :red ) level = :fatal end if ( actions_sentence = summary . actions_sentence . presence ) public_send ( level , actions_sentence ) blank_line ( level ) end summary . paragraphs . each do | para | msg_lines = para . split ( "\n" ) msg_lines . each { | line | public_send ( level , line ) } blank_line ( level ) unless para == summary . paragraphs . last end end'
python_code ='''
def max(a, b):
    x = b if b > a else a
    return x
}'''
def parse_code_to_graph(code, language):
    parser = Parser()
    parser.set_language(language)
    tree = parser.parse(bytes(code, 'utf8'))
    root_node = tree.root_node
    
    G = nx.DiGraph()
    code_bytes = bytes(code, 'utf8')
    nodes_to_add = [(root_node, None)]
    
    while nodes_to_add:
        node, parent = nodes_to_add.pop()
        node_id = (node.start_byte, node.end_byte)
        G.add_node(node_id, type=node.type, value=code_bytes[node.start_byte:node.end_byte].decode('utf-8'), start_byte=node.start_byte, end_byte=node.end_byte)
        
        if parent is not None:
            parent_id = (parent.start_byte, parent.end_byte)
            G.add_edge(parent_id, node_id)
        
        nodes_to_add.extend((child, node) for child in node.children)
    
    return G


PYTHON_LANGUAGE = Language('build/my-languages.so', 'python')

# ... (省略了之前定义的函数)

ast_graph = parse_code_to_graph(python_code, PYTHON_LANGUAGE)

dfs_sequence = []

# Perform DFS traversal using networkx
for node in nx.dfs_tree(ast_graph, list(ast_graph.nodes)[0]):
    dfs_sequence.append({**ast_graph.nodes[node], 'node': node})

reconstructed_code = reconstruct_code_from_dfs_sequence(dfs_sequence, ast_graph)

print(reconstructed_code)