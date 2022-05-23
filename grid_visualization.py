import matplotlib.pyplot as plt
import pickle
import pandas as pd

CLUSTER_NUM = 3

with open("tmp/node.pickle", 'rb') as f:
    node_dict: dict = pickle.load(f)
with open("tmp/link.pickle", 'rb') as f:
    link_dict: dict = pickle.load(f)
with open("tmp/shortest_path.pickle", 'rb') as f:
    path_dict: dict = pickle.load(f)

plt.figure()
OD_df = pd.read_csv("data/OD.csv", index_col="OD_id")
for j in range(OD_df.shape[0]):
    OD_id = OD_df.index[j]
    path = path_dict[OD_id][:-1]
    plt.plot(node_dict[OD_df.iloc[j, 0]][0], node_dict[OD_df.iloc[j, 0]][1], 'ro', markersize=1)
    plt.plot(node_dict[OD_df.iloc[j, 1]][0], node_dict[OD_df.iloc[j, 1]][1], 'bo', markersize=1)
    for link_id in path:
        from_node = node_dict[link_dict[link_id][0]]
        to_node = node_dict[link_dict[link_id][1]]
        plt.plot([from_node[0], to_node[0]], [from_node[1], to_node[1]], linewidth=0.2, c='g')
plt.show()

color = ['r', 'g', 'b', 'y']
for i in range(CLUSTER_NUM):
    plt.figure()
    OD_df = pd.read_csv("clusters/cluster_{}.csv".format(i), index_col="OD_id")
    for j in range(OD_df.shape[0]):
        OD_id = OD_df.index[j]
        path = path_dict[OD_id][:-1]
        plt.plot(node_dict[OD_df.iloc[j, 0]][0], node_dict[OD_df.iloc[j, 0]][1], 'ro', markersize=1)
        plt.plot(node_dict[OD_df.iloc[j, 1]][0], node_dict[OD_df.iloc[j, 1]][1], 'bo', markersize=1)
        for link_id in path:
            from_node = node_dict[link_dict[link_id][0]]
            to_node = node_dict[link_dict[link_id][1]]
            plt.plot([from_node[0], to_node[0]], [from_node[1], to_node[1]], linewidth=0.2, c='g')
    plt.show()