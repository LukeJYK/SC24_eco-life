from pathlib import Path
import pandas as pd
from glob import glob
import json
import os
import csv
import numpy as np
import shutil
import sys
def read_func_mem_size(name):
    app = {}
    with open(f'{Path(__file__).parents[0]}/function_mem.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            app[row[0]] = float(row[1])
    return app[name]

def raw_to_average():
    app = {}
    with open('./function_mem.csv', newline='', encoding='utf-8') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            app[row[0]] = float(row[1])
    #read server info
    with open('./server_info.json', 'r') as file:
        inst_info = json.load(file)
    instance_name = [x['name'] for x in inst_info]
    for instance in instance_name:
        if not os.path.exists(f"./server_data/{instance}"):
            os.makedirs(f"./server_data/{instance}")
        for key in app.keys():
            with open(f"./data/raw_data/{key}_{instance}.metal.json", "r") as f1:
                app_for_server = json.load(f1)
                avg_cs = np.mean([single["cs"] for single in app_for_server])
                avg_cs_energy_cpu = np.mean([single["cs_energy_cpu"] for single in app_for_server])
                avg_cs_energy_dram = np.mean([single["cs_energy_dram"] for single in app_for_server])
                avg_exe = np.mean([single["exe"] for single in app_for_server])
                avg_exe_energy_cpu = np.mean([single["exe_energy_cpu"] for single in app_for_server])
                avg_exe_energy_dram = np.mean([single["exe_energy_dram"] for single in app_for_server])
            avg = [{"cs":avg_cs,
                       "cs_energy_cpu":avg_cs_energy_cpu,
                       "cs_energy_dram": avg_cs_energy_dram,
                       "exe":avg_exe,
                       "exe_energy_cpu":avg_exe_energy_cpu,
                       "exe_energy_dram":avg_exe_energy_dram}]
            with open(f"./data/avg_data/{key}_{instance}.metal.json", "w") as f2:
                json.dump(avg, f2, indent=4)
          
def compute_exe_energy(app, server):
    # load sevrer info
    with open(f'{Path(__file__).parents[0]}/server_info.json', 'r') as file:
        info = json.load(file)
    for index,single_info in enumerate(info):
        if single_info["name"] == server:
            server_info = info[index]
    with open(f'{Path(__file__).parents[0]}/data/avg_data/{app}_{server}.metal.json','r') as data_file:
        server_data = json.load(data_file)[0]
    cold_energy = server_data['cs_energy_cpu'] + server_data['cs_energy_dram'] + server_data['exe_energy_cpu'] + server_data['exe_energy_dram']
    warm_energy = server_data['exe_energy_cpu'] + server_data['exe_energy_dram']
    return cold_energy, warm_energy
            
def compute_kat_energy(server,kat):
    # load sevrer info
    with open(f'{Path(__file__).parents[0]}/server_info.json', 'r') as file:
        info = json.load(file)
    for index,single_info in enumerate(info):
        if single_info["name"] == server:
            server_info = info[index]
    oc_kat_dram = kat*server_info['dram_idle_energy']/10
    oc_kat_cpu = kat*server_info['cpu_idle_energy']/10
    return oc_kat_cpu+oc_kat_dram

#data during execution:
def compute_exe(app, server_pair,CI):
    old = server_pair[0]
    new = server_pair[1]
    function_size = read_func_mem_size(app)
    # load sevrer info
    with open(f'{Path(__file__).parents[0]}/server_info.json', 'r') as file:
        server_info = json.load(file)
    for index,single_info in enumerate(server_info):
        if single_info["name"] == old:
            old_info = server_info[index]
        if single_info["name"] == new:
            new_info = server_info[index]
    # read app data
    with open(f'{Path(__file__).parents[0]}/data/avg_data/{app}_{old}.metal.json','r') as old_data_file:
        old_data = json.load(old_data_file)[0]
    with open(f'{Path(__file__).parents[0]}/data/avg_data/{app}_{new}.metal.json','r') as new_data_file:
        new_data = json.load(new_data_file)[0]
    old_q = function_size / old_info["mem"]
    new_q = function_size / new_info["mem"]
    
    # carbon calculation
    #cold start
    old_cold_st = old_data['cs'] + old_data['exe']
    new_cold_st = new_data['cs'] + new_data['exe']
    #old cold oc
    old_cold_oc_cpu = ((old_data['cs_energy_cpu']+old_data['exe_energy_cpu'])*CI)/1000/3600
    old_cold_oc_dram = ((old_data['cs_energy_dram']+old_data['exe_energy_dram'])*old_q*CI)/1000/3600
    old_cold_oc = old_cold_oc_cpu+old_cold_oc_dram
    #new cold oc
    new_cold_oc_cpu = ((new_data['cs_energy_cpu']+new_data['exe_energy_cpu'])*CI)/1000/3600
    new_cold_oc_dram = ((new_data['cs_energy_dram']+new_data['exe_energy_dram'])*new_q*CI)/1000/3600
    new_cold_oc = new_cold_oc_cpu+new_cold_oc_dram
    #old cold ec
    old_cold_ec_cpu = (old_cold_st/(4*12*30*24*3600)) * old_info["ec_cpu"] * 1000
    old_cold_ec_dram = (old_cold_st/(4*12*30*24*3600)) *old_q * old_info["ec_ram"] * 1000
    old_cold_ec = old_cold_ec_cpu +old_cold_ec_dram
    #new cold ec
    new_cold_ec_cpu = (new_cold_st/(4*12*30*24*3600)) * new_info["ec_cpu"] * 1000
    new_cold_ec_dram = (new_cold_st/(4*12*30*24*3600)) *new_q * new_info["ec_ram"] * 1000
    new_cold_ec = new_cold_ec_cpu +new_cold_ec_dram
    new_cold_carbon = new_cold_oc+new_cold_ec
    old_cold_carbon = old_cold_oc+old_cold_ec
    #__________________________________________________________________________________________
    
    #warm start
    old_warm_st = old_data['exe']
    new_warm_st = new_data['exe']
    #old warm oc
    old_warm_oc_cpu = (old_data['exe_energy_cpu']*CI)/1000/3600
    old_warm_oc_dram = (old_data['exe_energy_dram']*old_q*CI)/1000/3600
    old_warm_oc = old_warm_oc_cpu+old_warm_oc_dram
    #new warm oc
    new_warm_oc_cpu = (new_data['exe_energy_cpu']*CI)/1000/3600
    new_warm_oc_dram = (new_data['exe_energy_dram']*new_q*CI)/1000/3600
    new_warm_oc = new_warm_oc_cpu+new_warm_oc_dram
    #old warm ec
    old_warm_ec_cpu = (old_warm_st/(4*12*30*24*3600)) * old_info["ec_cpu"] * 1000
    old_warm_ec_dram = (old_warm_st/(4*12*30*24*3600)) *old_q * old_info["ec_ram"] * 1000
    old_warm_ec = old_warm_ec_cpu +old_warm_ec_dram
    #new cold ec
    new_warm_ec_cpu = (new_warm_st/(4*12*30*24*3600)) * new_info["ec_cpu"] * 1000
    new_warm_ec_dram = (new_warm_st/(4*12*30*24*3600)) *new_q * new_info["ec_ram"] * 1000
    new_warm_ec = new_warm_ec_cpu +new_warm_ec_dram
    new_warm_carbon = new_warm_oc+new_warm_ec
    old_warm_carbon = old_warm_oc+old_warm_ec

    return (old_cold_carbon,new_cold_carbon),(old_warm_carbon,new_warm_carbon)



def compute_kat(app, server, kat, CI):
    #kat is min
    function_size = read_func_mem_size(app)
    # load sevrer info
    with open(f'{Path(__file__).parents[0]}/server_info.json', 'r') as file:
        info = json.load(file)
    for index,single_info in enumerate(info):
        if single_info["name"] == server:
            server_info = info[index]
    
    # read app data
    with open(f'{Path(__file__).parents[0]}/data/avg_data/{app}_{server}.metal.json','r') as data_file:
        server_data = json.load(data_file)[0]
    q = function_size / server_info["mem"]
    ec_kat_dram = (kat*1000/(4*12*30*24*60))*q*server_info['ec_ram']
    oc_kat_dram = kat*q*CI*server_info['dram_idle_energy']/1000/3600/10
    ec_kat_cpu = (kat*1000/(4*12*30*24*60))*(1/server_info['core'])*server_info['ec_cpu']
    oc_kat_cpu = kat*(1/server_info['core'])*CI*server_info['cpu_idle_energy']/1000/3600/10
    return ec_kat_cpu+ec_kat_dram+oc_kat_cpu+oc_kat_dram
    

def get_st(app, server):
    with open(f'{Path(__file__).parents[0]}/data/avg_data/{app}_{server}.metal.json','r') as data_file:
        data = json.load(data_file)[0]
    return data['cs'] + data['exe'], data['exe']


def load_carbon_intensity(
    region: str="US-CAL",
    start_hour: int=800,
    interval: int=12*24*60,
):
    region_data = glob(f"{Path(__file__).parents[0]}/carbon_intensity/{region}*_2023_hourly.csv")[0]

    df = pd.read_csv(region_data)
    data = df["Carbon Intensity gCO₂eq/kWh (direct)"].values[start_hour:start_hour+int(12*24*60/60)]
    ci_avg = df["Carbon Intensity gCO₂eq/kWh (direct)"].mean()
    ci_max = df["Carbon Intensity gCO₂eq/kWh (direct)"].max()
    ci_min = df["Carbon Intensity gCO₂eq/kWh (direct)"].min()
    data_list = data.tolist()
    ci = []
    for item in data_list:
        for _ in range(60):
            ci.append(item)
    return ci,ci_max,ci_min,ci_avg

def function_mapping(duration_list, app_list):
    duration_list_norm =  (duration_list- np.min(duration_list)) / ( np.max(duration_list) - np.min(duration_list))
    app_list_norm =  (app_list- np.min(app_list)) / ( np.max(app_list) - np.min(app_list))
    closest_list = []
    for duration_norm in duration_list_norm:
        closest_index = None
        min_difference = float('inf')
        for i, num in enumerate(app_list_norm):
            difference = abs(num - duration_norm)
            if difference < min_difference:
                min_difference = difference
                closest_index = i
        closest_list.append(closest_index)
    return closest_list

def copy_and_rename_file(source_file, destination_directory, new_filename):
    try:
        shutil.copy(source_file, destination_directory)
        source_filename = source_file.split('/')[-1]
        new_file_path = destination_directory + '/' + new_filename
        shutil.move(destination_directory + '/' + source_filename, new_file_path)
    except Exception as e:
        print("error{e}")

def read_selected_traces():
    directory_path = f"{Path(__file__).parents[0]}/selected_trace"
    traces = []
    function_names = []
    path_list = []
    original_function_names = []
    for file in os.listdir(directory_path):
        if file.endswith('.txt'):
            original_function_names.append(file.split('.txt')[0])
            function_names.append(file.split('*')[0])
            path_list.append( os.path.join(directory_path, file))
    for file in path_list:
        with open(file, 'r') as f:
            file_content = [line.strip() for line in f.readlines()]
            traces.append(file_content)
    return traces,function_names,original_function_names
def prob_cold(cur_interval, kat):
        
    if len(cur_interval)==0:
        #no invocation
        return 0.5,0.5
    else:
        cold = 0
        warm = 0
        for interval in cur_interval:
            if interval<=kat:
                #hit
                warm+=1
            else:
                cold+=1
        return cold/(cold+warm), warm/(cold+warm)

def mem_check(mem_new,mem_old, old_decision,new_decision,function_mem_trace,new_warm_pool,old_warm_pool):
    cost_old_mem = 0
    cost_new_mem = 0
    
    for key, value in old_decision.items():
        cost_old_mem+=function_mem_trace[key]*int(value['num'])
    for key, value in old_warm_pool.items():
        cost_old_mem+=function_mem_trace[key]*int(value['num'])
    for key, value in new_decision.items():
        cost_new_mem+=function_mem_trace[key]*int(value['num'])
    for key, value in new_warm_pool.items():
        cost_new_mem+=function_mem_trace[key]*int(value['num'])
    if mem_new>=cost_new_mem and mem_old>=cost_old_mem:
        # both of them are fine
        return 0
    elif mem_new>=cost_new_mem and mem_old<cost_old_mem:
        #change old
        return 1
    elif mem_new<cost_new_mem and mem_old>=cost_old_mem:
        #change new
        return 2
    elif mem_new<cost_new_mem and mem_old<cost_old_mem:
        #change both
        return 3
    else:
        sys.exit("error in mem check")
    
def adjust_pool(mem,function_mem_trace,pool,decision_pool,interval_list,old_or_new,function_names,server_pair,ci,cur_time,window_size,result_carbon):
    
    kat_carbon = 0
    #compute the kat carbon for the pool
    for key, value in pool.items():
        which_fun = key
        invoke_time = value['invoke_time']
        
        assert(int(result_carbon[which_fun][invoke_time]['num']) >= int(value['num']))
        sig_kc = compute_kat(function_names[key],server_pair[old_or_new],int(cur_time)-int(value['start_time']),ci[int(value['start_time'])])*int(value['num'])
        result_carbon[which_fun][invoke_time]["carbon"]+=sig_kc
        kat_carbon+=sig_kc

    new_pool = {}
    limit = mem
    function_index = []
    function_invocation = []
    function_ka_start = []
    function_ka_end = []
    function_mem = []
    impact_score = []
    function_invoke_time=[]
    for key, value in pool.items():
        function_index.append(key)
        function_invocation.append(value['num'])
        function_ka_start.append(value['start_time'])
        function_ka_end.append(value['end_time'])
        function_invoke_time.append(value['invoke_time'])
    for key, value in decision_pool.items():
        function_index.append(key)
        function_invocation.append(value['num'])
        function_ka_start.append(value['start_time'])
        function_ka_end.append(value['end_time'])
        function_invoke_time.append(value['invoke_time'])
    for index in function_index:
        function_mem.append(function_mem_trace[index])
        
    for i in range(len(function_index)):
        index = function_index[i]
        cold_st = get_st(function_names[index],server_pair[old_or_new])[0]
        warm_st = get_st(function_names[index],server_pair[old_or_new])[1]
        a,b = compute_exe(function_names[index], server_pair, ci[cur_time])
        cold_carbon = a[old_or_new]
        warm_carbon = b[old_or_new]
        
        p_cold, p_warm = prob_cold(interval_list[index][cur_time-window_size], function_ka_end[i]-cur_time)
        p_st = p_cold*cold_st+p_warm*warm_st
        p_carbon = p_cold*cold_carbon+p_warm*warm_carbon
        st_dif = (cold_st - p_st )/cold_st
        carbon_dif = (max(cold_carbon,warm_carbon)-p_carbon )/max(cold_carbon,warm_carbon)
        impact_score.append((0.5*st_dif+0.5*carbon_dif)/function_mem[i])
    impact_score = np.array(impact_score)
    sort_index = impact_score.argsort()[::-1]
    sort_index_list = sort_index.tolist()
    # print(sort_index_list)
    index_normal = [i for i in range(len(function_index))]
    
    _, pool_list = pack_items(limit, function_mem, function_invocation, index_normal, sort_index_list)
    for index in pool_list:
        if function_index[index] in new_pool:
            new_pool[function_index[index]]['num']+=1
        else:
            new_pool[function_index[index]] =  {"num":1,"start_time":cur_time, "end_time":function_ka_end[index],"invoke_time":function_invoke_time[index]}

    #get all discarded functions
    combined_dict = {**pool, **decision_pool}
    
    discarded_dict = {key: value for key, value in combined_dict.items() if key not in new_pool}
    assert len(set(discarded_dict.keys()).intersection(new_pool.keys())) == 0
    for key, value in discarded_dict.items():
        if discarded_dict[key]['start_time']< cur_time:
            discarded_dict[key]['start_time'] = cur_time
        elif discarded_dict[key]['start_time']== cur_time:
            pass
        else:
            sys.exit("error in discarded dict")
    return new_pool,discarded_dict,kat_carbon,result_carbon


def pack_items(box_capacity, sizes, quantities, item_indices, index_list):
    remaining_space = box_capacity
    packed_items = []

    for index in index_list:
        item_index = int(item_indices[index])
        item_size = float(sizes[item_index])
        item_quantity = int(quantities[item_index])
        while item_quantity > 0 and remaining_space >= item_size:
            packed_items.append(index)
            remaining_space -= item_size
            item_quantity -= 1

    return remaining_space, packed_items

def add_discard_pool(original_pool, discard_pool,mem,function_mem_trace,function_names,old_or_new,interval_list,server_pair,cur_time,window_size,ci,result_carbon):
    limit = mem
    assert len(set(original_pool.keys()).intersection(discard_pool.keys())) == 0
    
    cost_mem = 0
    for key, value in original_pool.items():
        cost_mem+=function_mem_trace[key]*int(value['num'])
    for key, value in discard_pool.items():
        cost_mem+=function_mem_trace[key]*int(value['num'])
    if cost_mem>limit:
        #out of memory
        
        kat_carbon = 0
        #compute the kat carbon for the pool
        for key, value in original_pool.items():
            which_fun = key
            invoke_time = value['invoke_time']
            assert(int(result_carbon[which_fun][invoke_time]['num']) >= int(value['num']))
            sig_kc = compute_kat(function_names[key],server_pair[old_or_new],cur_time-int(value['start_time']),ci[int(value['start_time'])])*int(value['num'])
            result_carbon[which_fun][invoke_time]["carbon"]+=sig_kc
            kat_carbon+=sig_kc
        
        
        new_pool = {}
        function_index = []
        function_invocation = []
        function_ka_start = []
        function_ka_end = []
        function_mem = []
        impact_score = []
        function_invoke_time=[]
        for key, value in original_pool.items():
            function_index.append(key)
            function_invocation.append(value['num'])
            function_ka_start.append(value['start_time'])
            function_ka_end.append(value['end_time'])
            function_invoke_time.append(value['invoke_time'])
        for key, value in discard_pool.items():
            function_index.append(key)
            function_invocation.append(value['num'])
            function_ka_start.append(value['start_time'])
            function_ka_end.append(value['end_time'])
            function_invoke_time.append(value['invoke_time'])
        for index in function_index:
            function_mem.append(function_mem_trace[index])
        for i in range(len(function_index)):
            index = function_index[i]
            cold_st = get_st(function_names[index],server_pair[old_or_new])[0]
            warm_st = get_st(function_names[index],server_pair[old_or_new])[1]
            a,b = compute_exe(function_names[index], server_pair, ci[cur_time])
            cold_carbon = a[old_or_new]
            warm_carbon = b[old_or_new]
            
            p_cold, p_warm = prob_cold(interval_list[index][cur_time-window_size], function_ka_end[i]-cur_time)
            p_st = p_cold*cold_st+p_warm*warm_st
            p_carbon = p_cold*cold_carbon+p_warm*warm_carbon
            st_dif = (cold_st - p_st )/cold_st
            carbon_dif = (max(cold_carbon,warm_carbon)-p_carbon )/max(cold_carbon,warm_carbon)
            impact_score.append((0.5*st_dif+0.5*carbon_dif)/function_mem[i])
        impact_score = np.array(impact_score)
        sort_index = impact_score.argsort()[::-1]
        sort_index_list = sort_index.tolist()
        # print(sort_index_list)
        index_normal = [i for i in range(len(function_index))]
        
        _, pool_list = pack_items(limit, function_mem, function_invocation, index_normal, sort_index_list)
        for index in pool_list:
            if function_index[index] in new_pool:
                new_pool[function_index[index]]['num']+=1
            else:
                new_pool[function_index[index]] =  {"num":1,"start_time":cur_time, "end_time":function_ka_end[index],"invoke_time":function_invoke_time[index]}
        combined_dict = {**original_pool, **discard_pool}
    
        discarded_dict = {key: value for key, value in combined_dict.items() if key not in new_pool}
        
        return new_pool,kat_carbon,discarded_dict,result_carbon
    else:
        #not out of memory
        #combine all
        combined_dict = {**original_pool, **discard_pool}
        return combined_dict,0,0,result_carbon

    
    