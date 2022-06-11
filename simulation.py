"""
拼车概率、期望行驶里程与绕行里程仿真
Mon Mar 14 2022
Copyright (c) 2021 LI Weibo, Yuzhen FENG
"""
import simpy
import random
import pandas as pd
import pickle
import time
from settings import params
import os

start_time = time.time()
# -------------------- Start Simulation --------------------
MAX_RUNTIME = 3000
READY_TIME = 500

# ---------- Load data ----------
with open("tmp/link.pickle", 'rb') as f:
    link_dict: dict = pickle.load(f)
with open("tmp/OD.pickle", 'rb') as f:
    OD_dict: dict = pickle.load(f)
with open("tmp/shortest_path.pickle", 'rb') as f:
    path_dict: dict = pickle.load(f)
with open("variables/matches.pickle", 'rb') as f:
    matches: dict = pickle.load(f)
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

    def generate_passengers_of_OD(self, OD_id, OD):
        while True:
            lam = OD[2]
            if lam != 0:
                yield self.env.timeout(random.expovariate(lam))  # 指数分布
                # yield self.env.timeout(1 / lam)  # 定长分布
                # yield self.env.timeout(np.random.binomial((2 / lam), 0.5))  # 二项分布
                # yield self.env.timeout(np.random.uniform(0, 2*(1/lam)))  # 均匀分布
                self.env.process(self.passenger(OD_id, OD))

    def passenger(self, OD_id, OD):
        start_time = self.env.now
        origin = OD[0]
        destin = OD[1]
        current_loc = origin

        passenger_id = self.passenger_num
        self.passenger_num += 1

        if passenger_id % 10000 == 0:
            print("The", passenger_id, "passenger shows up at", start_time, "min.")
        
        self.passengers[passenger_id] = [OD_id, start_time, 0, current_loc]  # status: 0, seeker; 1, taker; 2, matched

        for taker in matches[OD_id]:
            taker_id = taker["taker_id"]
            link_idx = taker["link_idx"]
            taker_set: set = takers[taker_id][link_idx]
            if len(taker_set) != 0:
                matched_taker_id = taker_set.pop()
                self.matched_pairs.append([passenger_id, matched_taker_id, OD_id, taker_id, link_idx, taker["ride_seeker"], taker['ride_taker'], taker['detour_seeker'], taker['detour_taker'], taker['shared']])
                self.finished_passengers.append([passenger_id, OD_id, start_time, self.env.now, "seeker", taker["ride_seeker"], taker['detour_seeker'], taker['shared']])
                self.finished_passengers.append([matched_taker_id, taker_id, self.passengers[matched_taker_id][1], self.env.now, "taker", taker['ride_taker'], taker['detour_taker'], taker['shared']])
                self.passengers.pop(matched_taker_id)
                self.passengers.pop(passenger_id)
                return

        self.passengers[passenger_id] = [OD_id, start_time, 1, current_loc]
        takers[OD_id][0].add(passenger_id)
        yield self.env.timeout(self.PICKUP_TIME)

        link_idx = 0
        for link in path_dict[OD_id][:-1]:
            x = link_dict[link][1]
            if passenger_id in self.passengers.keys():
                self.passengers[passenger_id] = [OD_id, start_time, 1, x]
                takers[OD_id][link_idx].remove(passenger_id)
                link_idx += 1
                takers[OD_id][link_idx].add(passenger_id)
                yield self.env.timeout(link_dict[link][2] / self.SPEED)
            else:
                return
        
        if passenger_id in self.passengers.keys():
            takers[OD_id][link_idx].remove(passenger_id)
            self.finished_passengers.append([passenger_id, OD_id, start_time, self.env.now, "none", path_dict[OD_id][-1], 0, 0])
            self.passengers.pop(passenger_id)


    def output_matching_pairs(self):
        df = pd.DataFrame(self.matched_pairs, columns=["seeker_passenger_id", "taker_passenger_id", "seeker_id", "taker_id", "link_idx", "ride_seeker", "ride_taker", "detour_seeker", "detour_taker", "shared"])
        df.to_csv("result/simu_matching_pairs.csv", index=False)

    def output_log(self):
        df = pd.DataFrame(self.finished_passengers, columns=["passenger_id", "OD_id", "start_time", "end_time", "state", "ride_distance", "detour_distance", "shared_distance"])
        df.to_csv("result/simu_log.csv", index=False)
        df.loc[df["state"] != "none", "state"] = 1
        df.loc[df["state"] == "none", "state"] = 0
        stat = df.loc[df["start_time"] > READY_TIME, ["OD_id", "ride_distance", "detour_distance", "shared_distance", "state"]].astype({'state':'int32'}).groupby(by=["OD_id"]).mean()
        stat.to_csv("result/simu_stat.csv")


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
