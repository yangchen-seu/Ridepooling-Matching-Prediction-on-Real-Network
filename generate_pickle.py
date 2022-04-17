"""
加载数据并缓存为二进制文件
Sun Nov 28 2021
Copyright (c) 2021 Jiayu MA, Yuzhen FENG
"""
import pandas as pd
import pickle
import networkx as nx
from progress.bar import Bar
import time
import os
import settings

start_time = time.time()
# ------------------------------ Start to load data ------------------------------
# ---------- Load and dump node.csv ----------
bar = Bar("Loading node.csv", fill='#', max=100, suffix='%(percent)d%%')
node_data = pd.read_csv("./data/node.csv")  # node文件
node_num = node_data.shape[0]  # 节点数
node_dict = dict()

for i in bar.iter(range(node_num)):
    node_dict[int(node_data.loc[i].loc["node_id"])] = [node_data.loc[i].loc["x_coord"],
                                                       node_data.loc[i].loc["y_coord"]]  # 列表[经度，纬度]

f = open('tmp/node.pickle', 'wb')
pickle.dump(node_dict, f)
f.close()
# ---------- Load and dump link.csv ----------
bar = Bar("Loading link.csv", fill='#', max=100, suffix='%(percent)d%%')
link_data = pd.read_csv("./data/link.csv")  # link文件
link_num = link_data.shape[0]  # 边数
link_dict = dict()

for i in bar.iter(range(link_num)):
    link_dict[int(link_data.loc[i].loc["link_id"])] = [int(link_data.loc[i].loc["from_node_id"]),
                                                       int(link_data.loc[i].loc["to_node_id"]),
                                                       link_data.loc[i].loc["length"]]  # 列表[起点id，终点id，长度]

f = open('tmp/link.pickle', 'wb')
pickle.dump(link_dict, f)
f.close()
# ---------- Load and dump OD.csv ----------
bar = Bar("Loading OD.csv", fill='#', max=100, suffix='%(percent)d%%')
OD_data = pd.read_csv("./data/OD.csv")  # OD文件
OD_num = OD_data.shape[0]  # OD数
OD_dict = dict()

for i in bar.iter(range(settings.params['OD_num'])):
    OD_dict[int(OD_data.loc[i].loc["OD_id"])] = [int(OD_data.loc[i].loc["origin_id"]),
                                                 int(OD_data.loc[i].loc["destination_id"]),
                                                 OD_data.loc[i].loc["lambda"]]  # 列表[起点id，终点id，lambda]

f = open('tmp/OD.pickle', 'wb')
pickle.dump(OD_dict, f)
f.close()
# ---------- Build a graph ----------
G = nx.Graph()
G.add_nodes_from(node_dict.keys())
for link_id, link in link_dict.items():
    if not G.has_edge(link[0], link[1]):
        G.add_edge(link[0], link[1], weight=link[2], key=link_id)
f = open('tmp/graph.pickle', 'wb')
pickle.dump(G, f)
f.close()
# ------------------------------ End to load data ------------------------------
end_time = time.time()
# ---------- Log ----------
with open("log.txt", "a") as f:
    f.write(time.ctime() + ": Run " + os.path.basename(__file__) + " with Params = " + str(settings.params) + "; Cost " + str(end_time - start_time) + 's\n')
