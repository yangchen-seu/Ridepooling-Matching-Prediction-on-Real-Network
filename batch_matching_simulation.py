"""
拼车概率、期望行驶里程与绕行里程仿真
Mon Mar 14 2022
Copyright (c) 2021 Yuzhen FENG
"""
import simpy
import random
import pandas as pd
import pickle
import time
from settings import params
import os
import gurobipy as gp
from gurobipy import GRB
import math

start_time = time.time()
# -------------------- Start Simulation --------------------
MAX_RUNTIME = 3000
READY_TIME = 500
BATCH_TIME = 1

# ---------- Load data ----------
with open("tmp/link.pickle", 'rb') as f:
    link_dict: dict = pickle.load(f)
with open("tmp/OD.pickle", 'rb') as f:
    OD_dict: dict = pickle.load(f)
with open("tmp/shortest_path.pickle", 'rb') as f:
    path_dict: dict = pickle.load(f)
with open("variables/matches.pickle", 'rb') as f:
    matches: dict = pickle.load(f)
matches_dict = {}
for i, taker_list in matches.items():
    for x in taker_list:
        matches_dict[(i,x["taker_id"],x["link_idx"])] =  x
predict_result = pd.read_csv("./result/predict_result.csv", index_col=0)
print("Data loaded.")

takers = dict()
for taker_id in OD_dict.keys():
    takers[taker_id] = dict()
    path = path_dict[taker_id][:-1]
    takers[taker_id][0] = set()
    for link_idx, link_id in enumerate(path):
        takers[taker_id][link_idx + 1] = set()

# ---------- Start Simulation ----------
class Simulator:
    def __init__(self, env, OD_dict):
        self.PICKUP_TIME = params["pickup_time"]
        self.MAX_DETOUR_TIME = params["max_detour"]
        self.SEARCH_RADIUS = params["search_radius"]
        self.SPEED = params["speed"]
        
        self.env: simpy.Environment() = env
        self.OD_dict: dict = OD_dict
        self.passengers = {}
        self.passenger_num = 0
        self.matched_pairs = []
        self.finished_passengers = []
        
        self.generate_OD_of_network()

    def generate_OD_of_network(self):
        for OD_id, OD in self.OD_dict.items():
            self.env.process(self.generate_passengers_of_OD(OD_id, OD))
        self.env.process(self.batch_matching())

    def batch_matching(self):
        while True:
            seeker_passengers_cand = []
            taker_passengers = {}
            for passenger_id, passenger in self.passengers.items():
                state = passenger[2]
                if state == 0:
                    seeker_passengers_cand.append(passenger_id)
            taker_passenger_num = len(self.passengers) - len(seeker_passengers_cand)
            weight = {}
            seeker_passengers = []
            for i, passenger_id in enumerate(seeker_passengers_cand):
                passenger = self.passengers[passenger_id]
                OD_id = passenger[0]
                start_time = passenger[1]
                taker_num = 0
                seeker_passengers_idx = len(seeker_passengers)
                for taker_state in matches[OD_id]:
                    taker_id = taker_state["taker_id"]
                    link_idx = taker_state["link_idx"]
                    taker_set: set = takers[taker_id][link_idx]
                    for taker in taker_set:
                        if taker in taker_passengers.keys():
                            j = taker_passengers[taker]
                        else:
                            taker_passengers[taker] = len(taker_passengers)
                            j = len(taker_passengers) - 1
                        taker_num += 1
                        weight[(seeker_passengers_idx, j)] = -taker_state["shared"]
                weight_become_taker = -(predict_result.loc[OD_id, "shared_distance_for_taker"])
                weight_wait = (self.env.now - start_time) * self.SPEED - (predict_result.loc[OD_id, "shared_distance_for_seeker"])
                if taker_num == 0 and weight_become_taker < weight_wait:
                    self.passengers[passenger_id][2] = 1
                elif taker_num != 0:
                    seeker_passengers.append(passenger_id)
                    weight[(seeker_passengers_idx, taker_passenger_num)] = weight_become_taker
                    weight[(seeker_passengers_idx, taker_passenger_num + 1)] = weight_wait
            m = gp.Model()
            m.setParam('OutputFlag', 0)
            vars = m.addVars(weight.keys(), obj=weight, vtype=GRB.BINARY, name='e')
            m.addConstrs(vars.sum(i, '*') == 1 for i in range(len(seeker_passengers)))
            m.addConstrs(vars.sum('*', j) <= 1 for j in range(len(taker_passengers)))
            m._vars = vars
            m.optimize()

            taker_passengers_inv = {v: k for k, v in taker_passengers.items()}
            vals = m.getAttr('X', vars)
            edges = [(i, j) for i, j in vals.keys() if vals[i, j] > 0.5]
            
            seeker_matched_num = seeker_vacant_num = seeker_wait_num = 0
            for i, j in edges:
                passenger_id = seeker_passengers[i]
                OD_id = self.passengers[passenger_id][0]
                if j < len(taker_passengers):
                    seeker_matched_num += 1
                    matched_taker_id = taker_passengers_inv[j]
                    taker_id = self.passengers[matched_taker_id][0]
                    link_idx = self.passengers[matched_taker_id][3]
                    taker_set: set = takers[taker_id][link_idx]
                    taker_set.remove(matched_taker_id)
                    taker = matches_dict[(OD_id, taker_id, link_idx)]
                    self.matched_pairs.append([passenger_id, matched_taker_id, OD_id, taker_id, link_idx, taker["ride_seeker"], taker['ride_taker'], taker['detour_seeker'], taker['detour_taker'], taker['shared']])
                    self.finished_passengers.append([passenger_id, OD_id, start_time, self.env.now, "seeker", taker["ride_seeker"], taker['detour_seeker'], taker['shared']])
                    self.finished_passengers.append([matched_taker_id, taker_id, self.passengers[matched_taker_id][1], self.env.now, "taker", taker['ride_taker'], taker['detour_taker'], taker['shared']])
                    self.passengers.pop(matched_taker_id)
                    self.passengers.pop(passenger_id)
                elif j == taker_passenger_num:
                    seeker_vacant_num += 1
                    self.passengers[passenger_id][2] = 1
                else:
                    seeker_wait_num += 1
            # input()
            yield self.env.timeout(BATCH_TIME)


    def generate_passengers_of_OD(self, OD_id, OD):
        while True:
            lam = OD[2]
            if lam != 0:
                yield self.env.timeout(random.expovariate(lam))  # 指数分布
                self.env.process(self.passenger(OD_id, OD))

    def passenger(self, OD_id, OD):
        start_time = self.env.now
        origin = OD[0]
        destin = OD[1]
        current_loc = 0

        passenger_id = self.passenger_num
        self.passenger_num += 1

        if passenger_id % 10000 == 0:
            print("The", passenger_id, "passenger shows up at", start_time, "min.")
        
        self.passengers[passenger_id] = [OD_id, start_time, 0, current_loc]  # status: 0, seeker; 1, taker; 2, matched

        while passenger_id in self.passengers.keys() and self.passengers[passenger_id][2] == 0:
            yield self.env.timeout(BATCH_TIME - (self.env.now % BATCH_TIME) + 1e-6)
        if passenger_id not in self.passengers.keys():
            return
        takers[OD_id][0].add(passenger_id)
        yield self.env.timeout(self.PICKUP_TIME)

        link_idx = 0
        for link in path_dict[OD_id][:-1]:
            x = link_dict[link][1]
            if passenger_id in self.passengers.keys():
                takers[OD_id][link_idx].remove(passenger_id)
                link_idx += 1
                takers[OD_id][link_idx].add(passenger_id)
                self.passengers[passenger_id] = [OD_id, start_time, 1, link_idx]
                yield self.env.timeout(link_dict[link][2] / self.SPEED)
            else:
                return
        
        if passenger_id in self.passengers.keys():
            takers[OD_id][link_idx].remove(passenger_id)
            self.finished_passengers.append([passenger_id, OD_id, start_time, self.env.now, "none", path_dict[OD_id][-1], 0, 0])
            self.passengers.pop(passenger_id)


    def output_matching_pairs(self):
        df = pd.DataFrame(self.matched_pairs, columns=["seeker_passenger_id", "taker_passenger_id", "seeker_id", "taker_id", "link_idx", "ride_seeker", "ride_taker", "detour_seeker", "detour_taker", "shared"])
        df.to_csv("result/simu_matching_pairs_batch.csv", index=False)

    def output_log(self):
        df = pd.DataFrame(self.finished_passengers, columns=["passenger_id", "OD_id", "start_time", "end_time", "state", "ride_distance", "detour_distance", "shared_distance"])
        df.to_csv("result/simu_log_batch.csv", index=False)
        df.loc[df["state"] != "none", "state"] = 1
        df.loc[df["state"] == "none", "state"] = 0
        stat = df.loc[df["start_time"] > READY_TIME, ["OD_id", "ride_distance", "detour_distance", "shared_distance", "state"]].astype({'state':'int32'}).groupby(by=["OD_id"]).mean()
        stat.to_csv("result/simu_stat_batch.csv")


random.seed(0)
env = simpy.Environment()
network = Simulator(env, OD_dict)
try:
    env.run(until=MAX_RUNTIME)
except KeyboardInterrupt:
    pass
network.output_matching_pairs()
network.output_log()

end_time = time.time()
# ---------- log ----------
with open("log.txt", "a") as f:
    f.write(time.ctime() + ": Run " + os.path.basename(__file__) + " with Params = " + str(params) + "; Cost " + str(end_time - start_time)  + 's\n')
