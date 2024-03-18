from collections import defaultdict
import logging

# must convert between px and inches as positions are defined in pixels whereas width in inches
PIXELS_IN_INCH=96
GAP = 0
ORD_OFFSET = 20

def get_right_border(node):
    width = float(node.attr["width"]) * PIXELS_IN_INCH
    x, _ = [float(coord) for coord in node.attr["pos"].split(",", 2)]
    return x + width

def get_y_str(node):
    _, y_str = [coord for coord in node.attr["pos"].split(",", 2)]
    return y_str

def assign_ords_to_nodes(graph, ords_by_nodeid):
    full_ords_by_nodeid = {}
    for node_id in graph:
        ords = ords_by_nodeid.get(node_id)
        if ords:
            full_ords_by_nodeid[node_id] = ords
            continue
        parent_ords = None
        parent_id = node_id
        while not parent_ords:
            inedge = graph.in_edges(parent_id)[0]
            if not inedge:
                parent_ords = [0]
                break
            parent_id = inedge[0]
            parent_ords = ords_by_nodeid[parent_id]
        full_ords_by_nodeid[node_id] = parent_ords
    return full_ords_by_nodeid

def sort_and_group_nodes_by_ord(ords_by_nodeid, graph):
    def cumul_ords(ords):
        return ords[0]
    groups = defaultdict(list)
    for node_id, ords in ords_by_nodeid.items():
        cumul_ord = cumul_ords(ords)
        groups[cumul_ord].append(graph.get_node(node_id))
    return [groups[cumul_ord] for cumul_ord in sorted(groups.keys())]

def min_x_center(node, xmin_by_level):
    width = float(node.attr["width"]) * PIXELS_IN_INCH
    logging.debug(f"WIDTH of {node}: {width}")
    return xmin_by_level[get_y_str(node)] + width / 2

def find_x_center(nodes, prev_x_center, xmin_by_level):
    min_x_centers = [min_x_center(node, xmin_by_level) for node in nodes]
    calc_x_center = prev_x_center
    return max([calc_x_center, *min_x_centers])

def position_node_by_x(node, x_center):
    precision_tag = ".2f"
    width = float(node.attr["width"]) * PIXELS_IN_INCH
    x = x_center - width / 2
    y_str = get_y_str(node)
    pos_value = f"{x:{precision_tag}},{y_str}"
    node.attr["pos"] = pos_value

def layout_graph_by_ord(graph, ords_by_nodeid):
    # assign ords to nodes with no alignment: copy the values from their parents or [0]
    ords_by_nodeid = assign_ords_to_nodes(graph, ords_by_nodeid)
    # create a list of node ids sorted and grouped by their cumulated ord value
    ordered_grouped_nodes = sort_and_group_nodes_by_ord(ords_by_nodeid, graph)
    logging.debug(f"{ordered_grouped_nodes = }")
    xmin_by_level = {get_y_str(node): 0 for node in graph}
    prev_x_center = 0
    # iterate over graph nodes ordered and grouped by their ord value
    for ord_group in ordered_grouped_nodes:
        logging.debug(f"{xmin_by_level = }")
        logging.debug(f"{prev_x_center = }")
        x_center = find_x_center(ord_group, prev_x_center, xmin_by_level)
        logging.debug(f"{x_center = }")
        # position the nodes that share the same ord value
        for node in ord_group:
            position_node_by_x(node, x_center)
        # determine the right border for this ord group and use it to set the minimum x for levels of this ord group
        min_x = max([get_right_border(node) for node in ord_group]) + GAP
        logging.debug(f"{min_x = }")
        for node in ord_group:
            xmin_by_level[get_y_str(node)] = min_x
        prev_x_center = x_center + ORD_OFFSET
        logging.debug(f"{[node.attr['pos'] for node in ord_group] = }")
    # position at edges must be deleted, otherwise they would be placed as lay out by "dot" algorithm
    for edge in graph.edges_iter():
        del edge.attr["pos"]
        del edge.attr["lp"]
        logging.debug(f"{edge} {edge.attr.to_dict() = }")
    graph.has_layout = True

