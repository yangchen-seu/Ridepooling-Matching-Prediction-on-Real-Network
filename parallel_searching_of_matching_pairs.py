"""
匹配对的并行检索
Sun Apr 17 2022
Copyright (c) 2022 Yuzhen FENG
"""
import itertools
import os
import pickle
import networkx as nx
import pandas as pd
from multiprocessing import Pool
import time
import traceback
from settings import params

if True:
    # ---------- Load data ----------
    with open("tmp/link.pickle", 'rb') as f:
        link_dict: dict = pickle.load(f)
    with open("tmp/OD.pickle", 'rb') as f:
        OD_dict: dict = pickle.load(f)
    with open("tmp/shortest_path.pickle", 'rb') as f:
        path_dict: dict = pickle.load(f)
    if len(OD_dict) < params['OD_num']:
        print("WARNING: The number of OD in OD.pickle is less than that set in settings.py")
        quit()
    with open("tmp/graph.pickle", 'rb') as f:
        G: nx.Graph = pickle.load(f)
    with open("tmp/ego_graph.pickle", 'rb') as f:
        subgraph = pickle.load(f)

def search_matching_pairs(OD_idx1, OD_idx2, OD1, OD2, L1, L2, distance_between_dest, distance_from_seeker_origin_to_taker_dest):
    """Search matching pairs whose seeker-states belong to OD1 and taker-states to OD2

    Args:
        OD_idx1 (int): The ID of OD1
        OD_idx2 (int): The ID of OD2
        OD1 (list): The information of OD1
        OD2 (list): The information of OD2
        L1 (double): The distance between OD1
        L2 (double): The distance between OD2
        distance_between_dest (double): The distance between the destinations of the two OD
        distance_from_seeker_origin_to_taker_dest (double): The distance from OD1's origin to OD2's destination

    Returns:
        list: List of matching pairs
    """
    match = []
    # ---------- get the subgraph of neighbors centered at the origin of the seeker
    nearest_G: nx.Graph = subgraph[OD_idx1]

    if nearest_G.has_node(OD2[0]):
        pickup_distance = nearest_G.nodes[OD2[0]]["weight"]
        if pickup_distance <= params["search_radius"]:
            if distance_between_dest is None:
                try:
                    distance_between_dest = nx.shortest_path_length(G, OD1[1], OD2[1], weight="weight")
                except:
                    distance_between_dest = params['M']
            if distance_from_seeker_origin_to_taker_dest is None:
                try:
                    distance_from_seeker_origin_to_taker_dest = nx.shortest_path_length(G, OD2[1], OD1[0], weight="weight")
                except:
                    distance_from_seeker_origin_to_taker_dest = params['M']
            L_taker_FOLO = pickup_distance + L1 + distance_between_dest
            L_seeker_FOLO = L1
            L_taker_FOFO = pickup_distance + distance_from_seeker_origin_to_taker_dest
            L_seeker_FOFO = distance_from_seeker_origin_to_taker_dest + distance_between_dest
            detour = min(max(L_seeker_FOFO - L1, L_taker_FOFO - L2), max(L_seeker_FOLO - L1, L_taker_FOLO - L2))
            if detour < params['max_detour']:
                if max(L_seeker_FOFO - L1, L_taker_FOFO - L2) < max(L_seeker_FOLO - L1, L_taker_FOLO - L2):
                    ride_seeker = L_seeker_FOFO
                    ride_taker = L_taker_FOFO
                    shared = distance_from_seeker_origin_to_taker_dest
                else:
                    ride_seeker = L_seeker_FOLO
                    ride_taker = L_taker_FOLO
                    shared = L1
                detour_seeker = ride_seeker - L1
                detour_taker = ride_taker - L2
                prefer = params['w_detour'] * detour + params['w_pickup'] * pickup_distance + params['w_shared'] * shared
                match.append([OD_idx1, OD_idx2, 0, prefer, ride_seeker, ride_taker, detour_seeker, detour_taker, shared])
    for edge in nearest_G.edges(data=True):
        path = path_dict[OD_idx2][:-1]
        link_id = edge[2]["key"]
        if link_id in path:
            L_taker_init = 0
            i = 0
            for path_link_id in path:
                i += 1
                if path_link_id == link_id:
                    break
                L_taker_init += link_dict[path_link_id][2]
            pickup_distance = (nearest_G.nodes[link_dict[link_id][0]]["weight"] + nearest_G.nodes[link_dict[link_id][1]]["weight"]) / 2
            if pickup_distance > params["search_radius"]:
                continue
            if distance_between_dest is None:
                try:
                    distance_between_dest = nx.shortest_path_length(G, OD1[1], OD2[1], weight="weight")
                except:
                    distance_between_dest = params['M']
            if distance_from_seeker_origin_to_taker_dest is None:
                try:
                    distance_from_seeker_origin_to_taker_dest = nx.shortest_path_length(G, OD2[1], OD1[0], weight="weight")
                except:
                    distance_from_seeker_origin_to_taker_dest = params['M']
            L_taker_FOLO = L_taker_init + pickup_distance + L1 + distance_between_dest
            L_seeker_FOLO = L1
            L_taker_FOFO = L_taker_init + pickup_distance + distance_from_seeker_origin_to_taker_dest
            L_seeker_FOFO = distance_from_seeker_origin_to_taker_dest + distance_between_dest
            detour = min(max(L_seeker_FOFO - L1, L_taker_FOFO - L2), max(L_seeker_FOLO - L1, L_taker_FOLO - L2))
            if detour < params['max_detour']:
                if max(L_seeker_FOFO - L1, L_taker_FOFO - L2) < max(L_seeker_FOLO - L1, L_taker_FOLO - L2):
                    ride_seeker = L_seeker_FOFO
                    ride_taker = L_taker_FOFO
                    shared = distance_from_seeker_origin_to_taker_dest
                else:
                    ride_seeker = L_seeker_FOLO
                    ride_taker = L_taker_FOLO
                    shared = L1
                detour_seeker = max(ride_seeker - L1, 0)
                detour_taker = max(ride_taker - L2, 0)
                prefer = params['w_detour'] * detour + params['w_pickup'] * pickup_distance + params['w_shared'] * shared
                match.append([OD_idx1, OD_idx2, i, prefer, ride_seeker, ride_taker, detour_seeker, detour_taker, shared])
    return match

def generate_matches(OD_infor):
    """Search matching pairs whose taker-states belong to the OD in the parameter

    Args:
        OD_infor (tuple): The first element is the ID of the OD. The second is a list of the information of the OD including its origin node ID, destination node ID and the lambda (the mean demand)

    Raises:
        ValueError: The shortest path of the OD has not been include in shortest_path.pickle

    Returns:
        list: List of matching pairs, which is a list of [seeker's ID, taker's ID, taker's link's index, prederence, ride distance of the seeker, ride distance of the taker, detour distance of the seeker, detour distance of the taker, shared distance of the matching pair]
    """
    OD2_id, OD2 = OD_infor
    match_tmp = []
    if OD2_id not in path_dict:
        raise ValueError("Path not found.")
    distance_from_dest = nx.single_source_dijkstra_path_length(G, source=OD2[1], weight="weight")
    for OD1_id, OD1 in OD_dict.items():
        L1 = path_dict[OD1_id][-1]
        L2 = path_dict[OD2_id][-1]
        try:
            distance_between_dest = distance_from_dest[OD1[1]]
            distance_from_seeker_origin_to_taker_dest = distance_from_dest[OD1[0]]
        except KeyError:
            distance_between_dest = distance_from_seeker_origin_to_taker_dest = None
            
        try:
            match_ = search_matching_pairs(OD1_id, OD2_id, OD1, OD2, L1, L2, distance_between_dest, distance_from_seeker_origin_to_taker_dest)
            match_tmp += match_
        except KeyError:
                traceback.print_exc()
    return match_tmp

if __name__ == '__main__':
    all_start_time = time.time()
    pool = Pool(processes=params['process_num'])
    # ---------- search the matching pairs ----------
    print("Start searching matching pairs: ")
    start_time = time.time()
    result = pool.map(generate_matches, OD_dict.items(), len(OD_dict) // (params["process_num"] * params["chunk_num"]))
    end_time = time.time()
    print("Finish seaching matching pairs:", end_time - start_time)
    # ---------- dump the matching pairs ----------
    result = list(itertools.chain.from_iterable(result))
    m = pd.DataFrame(result, columns=["seeker_id", "taker_id", "link_idx", "preference", "ride_seeker", "ride_taker", "detour_seeker", "detour_taker", "shared"])
    m.sort_values(by=["seeker_id", "preference"], ascending=[True, False])
    m.to_csv("result/match.csv", index=False)
    # ---------- close the process pool ----------
    pool.close()
    pool.join()
    all_end_time = time.time()

    with open("log.txt", "a") as f:
        f.write(time.ctime() + ": Run " + os.path.basename(__file__) + " with Params = " + str(params) + "; Cost " + str(all_end_time - all_start_time) + 's\n')