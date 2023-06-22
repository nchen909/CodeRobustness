import random
from tqdm import tqdm
from tree_sitter import Language, Parser
import networkx as nx
from collections import deque

FUNC_TYPE_DICT= {
    'ruby': ['method','method_definition', 'singleton_method_definition'],
    'javascript': ['method_definition','function_declaration','arrow_function'],
    'go': ['function_declaration'],
    'python': ['function_definition'],
    'java': ['method_declaration'],
    'php': ['function_declaration','method_declaration','function_definition'],
    'c': ['function_definition'],
    'c_sharp': ['method_declaration'],
    'c++': ['function_definition']
}

# for i in FUNC_TYPE_DICT.values():
#     for j in i:
#         if j not in result:
#             result.append(j)
FUNC_TYPE_LIST = ['method', 'method_definition', 'singleton_method_definition', 'function_declaration', 'function_definition', 'method_declaration']

# breadth-first traverse
def traverse(cursor, G, parent_dict):
    '''
        cursor: the pointer of tree-sitter. An AST cursor is an object that is used to traverse an AST one node at a time
        G: the graph stored in the format of networkx
        parent_dict: used to store the parent nodes of all traversed nodes
    '''
    node_sum = 0
    node_tag = 0
    queue = deque([(cursor, node_tag, node_sum)])
    
    while queue:
        current_cursor, current_node_tag, current_node_sum = queue.popleft()
        G.add_node(current_node_sum, features=current_cursor.node, label=current_node_tag)
        
        if current_node_tag in parent_dict.keys():
            G.add_edge(parent_dict[current_node_tag], current_node_tag)
        
        if current_cursor.goto_first_child():
            child_node_sum = current_node_sum + 1
            parent_dict[child_node_sum] = current_node_tag
            queue.append((current_cursor.copy(), child_node_sum, child_node_sum))
            while current_cursor.goto_next_sibling():
                child_node_sum += 1
                parent_dict[child_node_sum] = parent_dict[current_node_tag]
                queue.append((current_cursor.copy(), child_node_sum, child_node_sum))
        current_cursor.goto_parent()



def get_lang_by_task(task, sub_task):
    if task in ['summarize','complete']:
        return sub_task
    elif task in ['refine','generate','clone']:
        return 'java'
    elif task == 'translate':
        if sub_task == 'cs-java':
            return 'c_sharp'
        else:
            return 'java'
    elif task == 'defect':
        return 'c'
    else:
        raise 'java'


class Attack():
    def __init__(self, args,examples):
        self.args = args
        self.examples = examples
        self.lang =  get_lang_by_task(args.task, args.sub_task)
        LANGUAGE = Language('build/my-languages.so', self.lang)
        parser = Parser()
        parser.set_language(LANGUAGE)
        self.parser = parser
        self.func_name_list= []
    def process_examples(self):
        disturbed_examples= []
        for example in tqdm(self.examples, total=len(self.examples), desc="Attack Examples"):
            example.source = self.get_attacked_code(example.source)
            disturbed_examples.append(example)
        return disturbed_examples

class TextualAttack(Attack):
    def __init__(self, args,examples):
        super().__init__(args,examples)
        args.attack_strategy = args.adversarial_strategy

    def get_function_names(self,code_list):
        function_names = []
        for code in tqdm(code_list, total=len(code_list), desc="Getting func names"):
            if self.args.sub_task == 'php':
                code = '<?php '+code
            tree = self.parser.parse(bytes(code, 'utf8'))
            root_node = tree.root_node
            
            for node in root_node.children:
                if node.type in FUNC_TYPE_LIST:
                    function_name_node = node.child_by_field_name("name")
                    if function_name_node:
                        function_name = code[function_name_node.start_byte:function_name_node.end_byte]
                        function_names.append(function_name)
        return function_names
    
    def shuffle_function_names(self,function_names):
        shuffled_names = function_names.copy()
        random.shuffle(shuffled_names)
        return shuffled_names
    def replace_examples_function_names(self):
        assert self.args.attack_strategy=='funcname'
        code_list=[]
        for example in  tqdm(self.examples, total=len(self.examples), desc="Reading examples"):
            code_list.append(example.source)
        function_names = self.get_function_names(code_list)
        function_names = self.shuffle_function_names(function_names)

        new_examples_list = []
        for example in  tqdm(self.examples, total=len(self.examples), desc="Attack Examples by shuffle function names"):
            code=example.source
            if self.args.sub_task == 'php':
                code = '<?php '+code
            tree = self.parser.parse(bytes(code, 'utf8'))
            root_node = tree.root_node
            
            for node in root_node.children:
                if node.type in FUNC_TYPE_LIST:
                    function_name_node = node.child_by_field_name("name")
                    if function_name_node:
                        new_function_name = function_names.pop(0)
                        example.source = code[:function_name_node.start_byte] + new_function_name + code[function_name_node.end_byte:]
                        if self.args.sub_task == 'php':
                            example.source = example.source[len('<?php '):]
            new_examples_list.append(example)
        
        return new_examples_list
    
    def process_examples(self):
        return self.replace_examples_function_names()
    
    def get_attacked_code(self,  code):
        #shuffle_func_names
        pass
        # if node.type == "identifier":
        #     start_byte = node.start_byte
        #     end_byte = node.end_byte
        #     identifier = code[start_byte:end_byte]

        #     if identifier in self.identifier_positions:
        #         self.identifier_positions[identifier].append(start_byte)
        #     else:
        #         self.identifier_positions[identifier] = [start_byte]

        # for child in node.children:
        #     self.find_identifiers(child, code)

class StructuralAttack(Attack):
    def __init__(self, args,examples):
        super().__init__(args,examples)
        if args.adversarial_strategy!='none':
            args.attack_strategy = args.adversarial_strategy
    # def ast_to_graph(self,node, source_code):
    #     G = nx.Graph()
    #     queue = deque([(node, None)])
        
    #     while queue:
    #         current_node, parent_node = queue.popleft()
    #         node_id = (current_node.start_byte, current_node.end_byte)
    #         current_node_data = {
    #             'type': current_node.type,
    #             'value': source_code[current_node.start_byte:current_node.end_byte].decode('utf-8'),
    #             'start_byte': current_node.start_byte,
    #             'end_byte': current_node.end_byte,
    #         }
    #         G.add_node(node_id, **current_node_data)
            
    #         if parent_node is not None:
    #             parent_node_id = (parent_node.start_byte, parent_node.end_byte)
    #             G.add_edge(node_id, parent_node_id)
            
    #         for child in current_node.children:
    #             queue.append((child, current_node))
        
    #     return G

    # def parse_code_to_graph(self, code):
    #     tree = self.parser.parse(bytes(code, 'utf8'))
    #     root_node = tree.root_node
    #     return self.ast_to_graph(root_node, bytes(code, 'utf8'))
    
    def reconstruct_code_from_sequence(self, sequence, graph):
        reconstructed_code = []
        
        for item in sequence:
            node = item['node']
            # Check if the node is a leaf node
            if graph.out_degree[node] == 0 and graph.in_degree[node] == 1:
                reconstructed_code.append(item['value'])
        
        return ' '.join(reconstructed_code)

    def drop_subtree_from_dfs_sequence(self, sequence, graph):
        # Randomly select a parent node and remove it along with its children

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

    def parse_code_to_graph(self, code):
        tree = self.parser.parse(bytes(code, 'utf8'))
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
    

    
    def get_attacked_code(self, code):
        if self.args.sub_task == 'php':
            code = '<?php '+code
        ast_graph = self.parse_code_to_graph(code)
        if self.args.attack_strategy == 'dfs':
            dfs_sequence = []

            # Perform DFS traversal using networkx
            for node in nx.dfs_tree(ast_graph, list(ast_graph.nodes)[0]):
                dfs_sequence.append({**ast_graph.nodes[node], 'node': node})

            reconstructed_code = self.reconstruct_code_from_sequence(dfs_sequence, ast_graph)
            if self.args.sub_task == 'php':
                reconstructed_code = reconstructed_code[:-len('<?php ')]
            return reconstructed_code
        elif self.args.attack_strategy == 'bfs':
            bfs_sequence = []

            # Perform BFS traversal using networkx
            for node in nx.bfs_tree(ast_graph, list(ast_graph.nodes)[0]):
                bfs_sequence.append({**ast_graph.nodes[node], 'node': node})

            # print(bfs_sequence)
            reconstructed_code = self.reconstruct_code_from_sequence(bfs_sequence, ast_graph)
            if self.args.sub_task == 'php':
                reconstructed_code = reconstructed_code[len('<?php '):]
            return reconstructed_code

        elif self.args.attack_strategy == 'subtree':
            dfs_sequence = []

            # Perform DFS traversal using networkx
            for node in nx.dfs_tree(ast_graph, list(ast_graph.nodes)[0]):
                dfs_sequence.append({**ast_graph.nodes[node], 'node': node})

            reconstructed_code = self.drop_subtree_from_dfs_sequence(dfs_sequence, ast_graph)
            if self.args.sub_task == 'php' and reconstructed_code[:len('<?php ')]=='<?php ':
                reconstructed_code = reconstructed_code[len('<?php '):]
            return reconstructed_code