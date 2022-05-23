import pandas as pd
import numpy as np

GRID_SIZE = 30
MAIN_ROAD_GAP = 3
MAIN_ROAD_LENGTH_RATIO = 0.95
OD_NUM = 300
nodes = {}
nodes_reverse = {}
links = {}

node_id = 0
for i in range(GRID_SIZE + 1):
    for j in range(GRID_SIZE + 1):
        nodes[(i, j)] = node_id
        nodes_reverse[node_id] = [i, j]
        node_id += 1

nodes_df = pd.DataFrame.from_dict(nodes_reverse, columns=["x_coord", "y_coord"], orient='index')
nodes_df.index.name = "node_id"
nodes_df.to_csv("data/node.csv")

link_id = 0
for node_id, node in nodes_reverse.items():
    x = node[0]
    y = node[1]
    if x < GRID_SIZE:
        adj_node = (x + 1, y)
        length = 1
        if int(y % MAIN_ROAD_GAP) == 0:
            length *= MAIN_ROAD_LENGTH_RATIO
        links[link_id] = [node_id, nodes[adj_node], length]
        link_id += 1
    if y < GRID_SIZE:
        adj_node = (x, y + 1)
        length = 1
        if int(x % MAIN_ROAD_GAP) == 0:
            length *= MAIN_ROAD_LENGTH_RATIO
        links[link_id] = [node_id, nodes[adj_node], length]
        link_id += 1
links_df = pd.DataFrame.from_dict(links, columns=["from_node_id", "to_node_id", "length"], orient='index')
links_df.index.name = "link_id"
links_df.to_csv("data/link.csv")

def generateODPairs(o_xmin, o_ymin, o_xmax, o_ymax, d_xmin, d_ymin, d_xmax, d_ymax, num):
    global nodes
    origin_dest = np.empty((num, 2))
    for i in range(num):
        ox = np.random.randint(o_xmin, o_xmax)
        oy = np.random.randint(o_ymin, o_ymax)
        dx = np.random.randint(d_xmin, d_xmax)
        dy = np.random.randint(d_ymin, d_ymax)
        origin = nodes[(ox, oy)]
        dest = nodes[(dx, dy)]
        origin_dest[i] = np.array([origin, dest])
    return origin_dest

origin_dest = np.random.randint(0, nodes_df.shape[0], (120, 2))
origin_dest = np.row_stack((generateODPairs(0, 0, 10, 10, 20, 20, 30, 30, 60), origin_dest))
origin_dest = np.row_stack((generateODPairs(20, 20, 30, 30, 0, 0, 10, 10, 60), origin_dest))
origin_dest = np.row_stack((generateODPairs(0, 20, 10, 30, 20, 0, 30, 10, 60), origin_dest))
demand = np.random.triangular(0.003, 0.015, 0.055, (OD_NUM, 1))
OD = np.column_stack((origin_dest, demand))
OD_df = pd.DataFrame(OD, columns=["origin_id", "destination_id", "lambda"])
OD_df.index.name = "OD_id"
OD_df.to_csv("data/OD.csv")