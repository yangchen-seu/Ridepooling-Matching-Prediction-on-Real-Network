"""
配置文件
Sun Nov 28 2021
Copyright (c) 2021 Yuzhen FENG
"""
params = {
    'lowest_road_class': 5,
    'max_combined_length': 1000,
    'OD_num': 500,
    'process_num': 4,
    'chunk_num': 5,
    'search_radius': 2000,
    'max_detour': 3000,
    'w_detour': 0,
    'w_pickup': 0,
    'w_shared': 0,
    "w_ride": -1,
    'pickup_time': 2,
    'speed': 600, # m/min
    'max_iter_time': 200,
    "min_iter_time": 5,
    'convergent_condition': 1e-6,
    'M': 1e6,
    'epsilon': 1e-6,
}
