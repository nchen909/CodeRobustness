import networkx as nx
from tree_sitter import Language, Parser
from networkx.drawing.nx_agraph import to_agraph
import pygraphviz as pgv
import numpy as np
# SOY_PATH = "/path_to_your_python_binding.so"
import sys
sys.setrecursionlimit(10000) 
def get_ast_nx(code, parser):
    tree = parser.parse(bytes(code, 'utf-8'))
    G = nx.Graph()
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

def index_to_code_token(start_point,end_point, code):
    code = code.split('\n')
    if start_point[0] == end_point[0]:
        s = code[start_point[0]][start_point[1]:end_point[1]]
    else:
        s = ""
        s += code[start_point[0]][start_point[1]:]
        for i in range(start_point[0] + 1, end_point[0]):
            s += code[i]
        s += code[end_point[0]][:end_point[1]]
    return s

def get_sast(T, leaves, tokens_dict, tokens_type_dict):
    # print("len(leaves), len(tokens_dict), len(tokens_type_dict)", len(leaves), len(tokens_dict), len(tokens_type_dict))
    
    # add subtoken edges and Data flow edges to T
    T = nx.Graph(T)
    subtoken_edges = []
    dataflow_edges = []
    identifier_dict = {}
    i = 0
    for leaf in leaves:
        token_type = tokens_type_dict[leaf]
        token = tokens_dict[leaf]
        if token_type == 'identifier':
            if token not in identifier_dict:
                identifier_dict[token] = leaf
            else:
                dataflow_edges.append((identifier_dict[token], leaf))
                identifier_dict[token] = leaf
        if i > 0:
            subtoken_edges.append((old_leaf, leaf))
        old_leaf = leaf
        i += 1
    T.add_edges_from(subtoken_edges)
    T.add_edges_from(dataflow_edges)
    return T  # new_T

def get_token_distance( leaves, sast, distance_metric='shortest_path_length'):  # 4min
    # print('get token distance')
    if distance_metric == 'shortest_path_length':
        ast_distance = nx.shortest_path_length(sast)
    elif distance_metric == 'simrank_similarity':
        ast_distance = nx.simrank_similarity(sast)
    # print(list(ast_distance))
    leaf=leaves
    token_num = len(leaves)
    distance = np.zeros((token_num, token_num))
    ast_distance = dict(ast_distance)
    for j in range(token_num):
        for k in range(token_num):
            if leaf[k] in ast_distance[leaf[j]].keys():
                distance[j][k] = ast_distance[leaf[j]
                                            ][leaf[k]]  # just token distance

    return distance

import networkx as nx

def calculate_global_efficiency(G, leaves):
    n = len(leaves)
    sum_inverse_distance = 0.0
    for i in range(n):
        for j in range(i+1, n):
            try:
                d = nx.shortest_path_length(G, source=leaves[i], target=leaves[j])
                sum_inverse_distance += 1/d
            except nx.NetworkXNoPath:
                continue  # ignore if no path exists
    GE = sum_inverse_distance / (0.5 * n * (n - 1))
    L = 1 / GE if GE != 0 else float('inf')  # handle division by zero
    return GE, L


def main():
    code = '''
static int config_props(AVFilterLink *inlink)\n\n{\n\n    AVFilterContext *ctx = inlink->dst;\n\n    LutContext *lut = ctx->priv;\n\n    const AVPixFmtDescriptor *desc = &av_pix_fmt_descriptors[inlink->format];\n\n    int min[4], max[4];\n\n    int val, comp, ret;\n\n\n\n    lut->hsub = desc->log2_chroma_w;\n\n    lut->vsub = desc->log2_chroma_h;\n\n\n\n    lut->var_values[VAR_W] = inlink->w;\n\n    lut->var_values[VAR_H] = inlink->h;\n\n\n\n    switch (inlink->format) {\n\n    case PIX_FMT_YUV410P:\n\n    case PIX_FMT_YUV411P:\n\n    case PIX_FMT_YUV420P:\n\n    case PIX_FMT_YUV422P:\n\n    case PIX_FMT_YUV440P:\n\n    case PIX_FMT_YUV444P:\n\n    case PIX_FMT_YUVA420P:\n\n        min[Y] = min[U] = min[V] = 16;\n\n        max[Y] = 235;\n\n        max[U] = max[V] = 240;\n\n        min[A] = 0; max[A] = 255;\n\n        break;\n\n    default:\n\n        min[0] = min[1] = min[2] = min[3] = 0;\n\n        max[0] = max[1] = max[2] = max[3] = 255;\n\n    }\n\n\n\n    lut->is_yuv = lut->is_rgb = 0;\n\n    if      (ff_fmt_is_in(inlink->format, yuv_pix_fmts)) lut->is_yuv = 1;\n\n    else if (ff_fmt_is_in(inlink->format, rgb_pix_fmts)) lut->is_rgb = 1;\n\n\n\n    if (lut->is_rgb) {\n\n        switch (inlink->format) {\n\n        case PIX_FMT_ARGB:  lut->rgba_map[A] = 0; lut->rgba_map[R] = 1; lut->rgba_map[G] = 2; lut->rgba_map[B] = 3; break;\n\n        case PIX_FMT_ABGR:  lut->rgba_map[A] = 0; lut->rgba_map[B] = 1; lut->rgba_map[G] = 2; lut->rgba_map[R] = 3; break;\n\n        case PIX_FMT_RGBA:\n\n        case PIX_FMT_RGB24: lut->rgba_map[R] = 0; lut->rgba_map[G] = 1; lut->rgba_map[B] = 2; lut->rgba_map[A] = 3; break;\n\n        case PIX_FMT_BGRA:\n\n        case PIX_FMT_BGR24: lut->rgba_map[B] = 0; lut->rgba_map[G] = 1; lut->rgba_map[R] = 2; lut->rgba_map[A] = 3; break;\n\n        }\n\n        lut->step = av_get_bits_per_pixel(desc) >> 3;\n\n    }\n\n\n\n    for (comp = 0; comp < desc->nb_components; comp++) {\n\n        double res;\n\n\n\n        /* create the parsed expression */\n\n        ret = av_expr_parse(&lut->comp_expr[comp], lut->comp_expr_str[comp],\n\n                            var_names, funcs1_names, funcs1, NULL, NULL, 0, ctx);\n\n        if (ret < 0) {\n\n            av_log(ctx, AV_LOG_ERROR,\n\n                   \"Error when parsing the expression '%s' for the component %d.\\n\",\n\n                   lut->comp_expr_str[comp], comp);\n\n            return AVERROR(EINVAL);\n\n        }\n\n\n\n        /* compute the lut */\n\n        lut->var_values[VAR_MAXVAL] = max[comp];\n\n        lut->var_values[VAR_MINVAL] = min[comp];\n\n\n\n        for (val = 0; val < 256; val++) {\n\n            lut->var_values[VAR_VAL] = val;\n\n            lut->var_values[VAR_CLIPVAL] = av_clip(val, min[comp], max[comp]);\n\n            lut->var_values[VAR_NEGVAL] =\n\n                av_clip(min[comp] + max[comp] - lut->var_values[VAR_VAL],\n\n                        min[comp], max[comp]);\n\n\n\n            res = av_expr_eval(lut->comp_expr[comp], lut->var_values, lut);\n\n            if (isnan(res)) {\n\n                av_log(ctx, AV_LOG_ERROR,\n\n                       \"Error when evaluating the expression '%s' for the value %d for the component #%d.\\n\",\n\n                       lut->comp_expr_str[comp], val, comp);\n\n                return AVERROR(EINVAL);\n\n            }\n\n            lut->lut[comp][val] = av_clip((int)res, min[comp], max[comp]);\n\n            av_log(ctx, AV_LOG_DEBUG, \"val[%d][%d] = %d\\n\", comp, val, lut->lut[comp][val]);\n\n        }\n\n    }\n\n\n\n    return 0;\n\n}\n
    '''
#     code = '''
# def max(a, b):
#     x = b if b > a else a
#     return x
#     '''
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
    PY_LANGUAGE = Language('build/my-languages.so', 'java')
    parser = Parser()
    parser.set_language(PY_LANGUAGE)
    G, source = get_ast_nx(code, parser)
    # print(source)
    T = nx.dfs_tree(G, 0)


    # Copy node attributes from G to T
    for node in T.nodes():
        T.nodes[node]['label'] = G.nodes[node]['label']
        T.nodes[node]['features'] = G.nodes[node]['features']

    nodes = T.nodes()
    leaves = [x for x in T.nodes() if T.out_degree(x) ==
                    0 and T.in_degree(x) == 1]
    tokens_dict = {}
    tokens_type_dict = {}
    for leaf in leaves[:]:
        feature = G.nodes[leaf]['features']
        if feature.type == 'comment':
            leaves.remove(leaf)
            T.remove_node(leaf)
        else:
            start = feature.start_point
            end = feature.end_point
            token = index_to_code_token(start, end, source)
            # print('leaf: ', leaf, 'start: ', start,
            #     ', end: ', end, ', token: ', token)
            tokens_dict[leaf] = token
            tokens_type_dict[leaf] = feature.type
    assert len(leaves) == len(tokens_dict)
    sast = get_sast(T, leaves, tokens_dict, tokens_type_dict)
    # for node in nodes:
    #     feature = G.nodes[node]['features']
    #     if feature.type != 'comment':
    #         start = feature.start_point
    #         end = feature.end_point
    #         token = index_to_code_token(start, end, source)
    #         print(f'node: {node}, start: {start}, end: {end}, token: {token}')

    # Save AST graph to PNG
    A = to_agraph(sast)
    # print(G.nodes[0])

    for node in A.iternodes():
        node_id = int(node.get_name())
        if sast.degree[node_id] == 1:  # If it's a leaf node
            node.attr['label'] = sast.nodes[node_id]['label']
        else:  # If it's not a leaf node
            node.attr['label'] = sast.nodes[node_id]['features'].type
    A.layout('dot')
    A.draw('SAST.png')
    print(get_token_distance(leaves,sast))
    GE, L = calculate_global_efficiency(sast, leaves)
    print(GE,L)
    # strategy='GE'/'L'
if __name__ == "__main__":
    main()
