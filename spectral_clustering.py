import pickle
import networkx as nx
import pandas as pd
import progressbar
from sklearn.cluster import SpectralClustering
import numpy as np
import matplotlib.pyplot as plt

with open("variables/seekers.pickle", 'rb') as f:
    seekers: dict = pickle.load(f)
with open("variables/takers.pickle", 'rb') as f:
    takers: dict = pickle.load(f)
with open("variables/matches.pickle", 'rb') as f:
    matches: dict = pickle.load(f)
with open("tmp/node.pickle", 'rb') as f:
    node_dict: dict = pickle.load(f)
with open("tmp/OD.pickle", 'rb') as f:
    OD_dict: dict = pickle.load(f)

bar = progressbar.ProgressBar(widgets=[progressbar.Percentage(), ' (', progressbar.SimpleProgress(), ' ', progressbar.AbsoluteETA(), ')'])

print("Start to load matching pairs: ", end='')
G = nx.DiGraph()
G.add_nodes_from(matches.keys())
for seeker_id, takers_of_seeker in bar(matches.items()):
    for taker in takers_of_seeker:
        taker_id = taker["taker_id"]
        if G.has_edge(seeker_id, taker_id):
            G.edges[seeker_id, taker_id]["weight"] += taker["eta_match"] * takers[taker_id][taker["link_idx"]]["rho_taker"]
            # G.edges[seeker_id, taker_id]["weight"] += taker["eta_match"]
        else:
            G.add_edge(seeker_id, taker_id, weight=taker["eta_match"] * takers[taker_id][taker["link_idx"]]["rho_taker"])
            # G.add_edge(seeker_id, taker_id, weight=taker["eta_match"])

print("Select maximum subgraph from connected component with " + str([len(c) for c in sorted(nx.weakly_connected_components(G), key=len, reverse=True)]) + " nodes.")
connected_G = G.subgraph(max(nx.weakly_connected_components(G), key=len)).copy()
adjacency_matrix = nx.linalg.graphmatrix.adjacency_matrix(connected_G)
adjacency_matrix = adjacency_matrix.T + adjacency_matrix

CLUSTER_NUM = 4
clustering = SpectralClustering(
    n_clusters=CLUSTER_NUM,
    n_components=CLUSTER_NUM,
    affinity='precomputed',
    random_state=0,
    assign_labels='kmeans').fit(adjacency_matrix)
labels = clustering.labels_
print("All the ODs are divided into the following clusters:")
for n in range(CLUSTER_NUM):
    print(n, np.sum(labels == n))

clusters = {}
for i, OD_id in enumerate(connected_G.nodes.keys()):
    OD = OD_dict[OD_id]
    origin = OD[0]
    destination = OD[1]
    string = "LINESTRING ("
    string += str(node_dict[origin][0]) + ' ' + str(node_dict[origin][1]) + ", "
    # end = origin
    # path = path_dict[OD_id]
    # for link_id in path:
    #     link_end_1 = link_dict[link_id][0]
    #     link_end_2 = link_dict[link_id][1]
    #     if link_end_1 == end:
    #         string += str(node_dict[link_end_2][0]) + ' ' + str(node_dict[link_end_2][1]) + ", "
    #         end = link_end_2
    #     else:
    #         string += str(node_dict[link_end_1][0]) + ' ' + str(node_dict[link_end_1][1]) + ", "
    #         end = link_end_1
    string += str(node_dict[destination][0]) + ' ' + str(node_dict[destination][1]) + ')'
    clusters.setdefault(labels[i], list()).append(dict({"OD_id": OD_id, "origin_id": origin, "destination_id": destination, "lambda": OD[2], "geometry": string}))

for cluster_id, ODs in clusters.items():
    OD_df = pd.DataFrame(ODs)
    OD_df.to_csv("clusters/cluster_" + str(cluster_id) + ".csv", index=False)
