import pickle
import networkx as nx
import pandas as pd
import progressbar
from sklearn.cluster import SpectralClustering
import numpy as np

CLUSTER_NUM = 3

with open("variables/matches.pickle", 'rb') as f:
    matches: dict = pickle.load(f)
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
            G.edges[seeker_id, taker_id]["weight"] += taker["eta_match"]
        else:
            G.add_edge(seeker_id, taker_id, weight=taker["eta_match"])

print("Select maximum subgraph from connected component with " + str([len(c) for c in sorted(nx.weakly_connected_components(G), key=len, reverse=True)]) + " nodes.")
connected_G = G.subgraph(max(nx.weakly_connected_components(G), key=len)).copy()
adjacency_matrix = nx.linalg.graphmatrix.adjacency_matrix(connected_G)
adjacency_matrix = adjacency_matrix.T + adjacency_matrix


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
    clusters.setdefault(labels[i], list()).append(dict({"OD_id": OD_id, "origin_id": origin, "destination_id": destination, "lambda": OD[2]}))
for cluster_id, ODs in clusters.items():
    OD_df = pd.DataFrame(ODs)
    OD_df.to_csv("clusters/cluster_" + str(cluster_id) + ".csv", index=False)
