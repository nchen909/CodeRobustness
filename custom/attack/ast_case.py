import networkx as nx
from tree_sitter import Language, Parser
from networkx.drawing.nx_agraph import to_agraph
import pygraphviz as pgv

# SOY_PATH = "/path_to_your_python_binding.so"

def get_ast_nx(code, parser):
    tree = parser.parse(bytes(code, 'utf-8'))
    G = nx.DiGraph()
    cursor = tree.walk()
    traverse(cursor, G, code, came_up=False, node_tag=0, node_sum=0, parent_dict={})
    return G, code

def traverse(cursor, G, code, came_up, node_tag, node_sum, parent_dict):
    if not came_up:
        start = cursor.node.start_point
        end = cursor.node.end_point
        token = index_to_code_token(start, end, code)
        G.add_node(node_tag, label=token, features=cursor.node)
        if node_tag in parent_dict.keys():
            G.add_edge(parent_dict[node_tag], node_tag)
        if cursor.goto_first_child():
            node_sum += 1
            parent_dict[node_sum] = node_tag
            traverse(cursor, G, code, came_up=False, node_tag=node_sum, node_sum=node_sum, parent_dict=parent_dict)
        elif cursor.goto_next_sibling():
            node_sum += 1
            parent_dict[node_sum] = parent_dict[node_tag]
            traverse(cursor, G, code, came_up=False, node_tag=node_sum, node_sum=node_sum, parent_dict=parent_dict)
        elif cursor.goto_parent():
            node_tag = parent_dict[node_tag]
            traverse(cursor, G, code, came_up=True, node_tag=node_tag, node_sum=node_sum, parent_dict=parent_dict)
    else:
        if cursor.goto_next_sibling():
            node_sum += 1
            parent_dict[node_sum] = parent_dict[node_tag]
            traverse(cursor, G, code, came_up=False, node_tag=node_sum, node_sum=node_sum, parent_dict=parent_dict)
        elif cursor.goto_parent():
            node_tag = parent_dict[node_tag]
            traverse(cursor, G, code, came_up=True, node_tag=node_tag, node_sum=node_sum, parent_dict=parent_dict)

def index_to_code_token(start, end, code):
    lines = code.split('\n')
    token = '\n'.join(lines[start[0]:end[0] + 1])[start[1]:end[1] + 1]
    return token.strip()

def main():
#     code = '''
# def max(a, b):
#     x = 0 
#     if b > a:
#         x = b
#     else:
#         x = a
#     return x
#     '''
    code = '''
def max(a, b):
    x = b if b > a else a
    return x
    '''
    Language.build_library(
    # Store the library in the `build` directory
    'build/my-languages.so',

    # Include one or more languages
    [
        'evaluator/CodeBLEU/parser/tree-sitter-go',
        'evaluator/CodeBLEU/parser/tree-sitter-javascript',
        'evaluator/CodeBLEU/parser/tree-sitter-python',
        'evaluator/CodeBLEU/parser/tree-sitter-php',
        'evaluator/CodeBLEU/parser/tree-sitter-java',
        'evaluator/CodeBLEU/parser/tree-sitter-ruby',
        'evaluator/CodeBLEU/parser/tree-sitter-c-sharp',
        'evaluator/CodeBLEU/parser/tree-sitter-c',
    ]
    )
    PY_LANGUAGE = Language('build/my-languages.so', 'python')
    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    G, source = get_ast_nx(code, parser)

    T = nx.dfs_tree(G, 0)
    nodes = T.nodes()
    for node in nodes:
        feature = G.nodes[node]['features']
        if feature.type != 'comment':
            start = feature.start_point
            end = feature.end_point
            token = index_to_code_token(start, end, source)
            print(f'node: {node}, start: {start}, end: {end}, token: {token}')

    # Save AST graph to PNG
    A = to_agraph(G)

    for node in A.iternodes():
        node_id = int(node.get_name())
        if G.degree[node_id] == 1:  # If it's a leaf node
            node.attr['label'] = G.nodes[node_id]['label']
        else:  # If it's not a leaf node
            node.attr['label'] = G.nodes[node_id]['features'].type
    A.layout('dot')
    A.draw('ast_2.png')

if __name__ == "__main__":
    main()
