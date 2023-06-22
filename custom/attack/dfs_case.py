import json
import networkx as nx
from tree_sitter import Language, Parser
from collections import deque

PYTHON_LANGUAGE = Language('build/my-languages.so', 'java')

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

def reconstruct_code_from_bfs_sequence(sequence, graph):
    reconstructed_code = []
    
    for item in sequence:
        node = item['node']
        # Check if the node is a leaf node
        if graph.out_degree[node] == 0 and graph.in_degree[node] == 1:
            reconstructed_code.append(item['value'])
    
    return ' '.join(reconstructed_code)

# def reconstruct_code_from_bfs_sequence(sequence, graph):
#     sorted_sequence = sorted(sequence, key=lambda x: x['start_byte'])
#     reconstructed_code = []
    
#     for item in sorted_sequence:
#         node = item['node']
#         # Check if the node is a leaf node
#         if graph.out_degree(node) == 0 and graph.in_degree(node) == 1:
#             reconstructed_code.append(item['value'])
    
#     return ' '.join(reconstructed_code)

# php_code = 'def print_summary ( status ) status_string = status . to_s . humanize . upcase if status == :success heading ( "Result: " , status_string , :green ) level = :info elsif status == :timed_out heading ( "Result: " , status_string , :yellow ) level = :fatal else heading ( "Result: " , status_string , :red ) level = :fatal end if ( actions_sentence = summary . actions_sentence . presence ) public_send ( level , actions_sentence ) blank_line ( level ) end summary . paragraphs . each do | para | msg_lines = para . split ( "\n" ) msg_lines . each { | line | public_send ( level , line ) } blank_line ( level ) unless para == summary . paragraphs . last end end'

python_code = '''
private void download(String address, String localFileName) throws UrlNotFoundException, Exception {
    String ext = G_File.getExtensao(address);
    if (ext.equals("jsp")) {
        throw new Exception("Erro ao baixar pagina JSP, tipo negado." + address);
    }
    File temp = new File(localFileName + ".tmp");
    if (temp.exists()) temp.delete();
    OutputStream out = null;
    URLConnection conn = null;
    InputStream in = null;
    try {
        try {
            URL url = new URL(address);
            conn = url.openConnection();
            in = conn.getInputStream();
        } catch (FileNotFoundException e2) {
            throw new UrlNotFoundException();
        }
        out = new BufferedOutputStream(new FileOutputStream(temp));
        byte[] buffer = new byte[1024];
        int numRead;
        long numWritten = 0;
        while ((numRead = in.read(buffer)) != -1) {
            out.write(buffer, 0, numRead);
            numWritten += numRead;
        }
    } catch (UrlNotFoundException exception) {
        throw exception;
    } catch (Exception exception) {
        throw exception;
    } finally {
        try {
            if (in != null) {
                in.close();
            }
            if (out != null) {
                out.close();
            }
        } catch (IOException ioe) {
        }
    }
'''
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

ast_graph = parse_code_to_graph(python_code, PYTHON_LANGUAGE)

import json
import networkx as nx
from tree_sitter import Language, Parser
from collections import deque

PYTHON_LANGUAGE = Language('build/my-languages.so', 'python')

# ... (省略了之前定义的函数)

ast_graph = parse_code_to_graph(python_code, PYTHON_LANGUAGE)

dfs_sequence = []

# Perform DFS traversal using networkx
for node in nx.dfs_tree(ast_graph, list(ast_graph.nodes)[0]):
    dfs_sequence.append({**ast_graph.nodes[node], 'node': node})

reconstructed_code = reconstruct_code_from_bfs_sequence(dfs_sequence, ast_graph)

print(reconstructed_code)
