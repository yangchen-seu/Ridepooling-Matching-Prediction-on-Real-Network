"""
配置文件
Sun Nov 28 2021
Copyright (c) 2021 Yuzhen FENG
"""
params = {
    'lowest_road_class': 5,
    'OD_num': 5000,
    'process_num': 24,
    'chunk_num': 5,
    'search_radius': 2000,
    'max_detour': 3000,
    'w_detour': -0.5,
    'w_pickup': -0.3,
    'w_shared': 0.2,
    'pickup_time': 2,
    'speed': 600, # m/min
    'max_iter_time': 200,
    'convergent_condition': 1e-6,
    'M': 100000000,
}
