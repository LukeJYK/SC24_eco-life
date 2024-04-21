import fire
import utils
import pandas as pd
from pathlib import Path
from optimizers import random_select, perf,carbon_opt,oracle,energy_opt,tech,only_new,only_old
import numpy as np
import sys

def main(
    region: str="US-CAL",
    start_hour: int=800,
    interval: int=12*24*60,
    mem_old =2000000,
    mem_new=20000000,
    app_list: list = None,
    server_pair: list = ['c5','m5zn'],
    kat_time:list = [i for i in range(0,31)],
    optimizer: str = 'tech',
    STlambda:float = 0.5,
    window_size: int = 20,
    pso_size: int = 15
):
    print(server_pair)
    # app_mem = 5*app_mem
    if app_list is None:
        df = pd.read_csv(f"{Path(__file__).parents[0]}/function_mem.csv",header=None) 
        app_list = df.iloc[:, 0].tolist()
    # load carbon intensity data
    carbon_intensity, ci_max, ci_min,ci_avg = utils.load_carbon_intensity(region, start_hour, interval)
    print(ci_max, ci_min,ci_avg)
    #load trace:
    traces, trace_function_names,original_names = utils.read_selected_traces()
    for trace in traces:
        assert len(trace) == len(carbon_intensity)
    function_mem_trace = [utils.read_func_mem_size(trace_function_names[i]) for i in range(len(traces))]
    
    sum=0

    for i in range(len(traces)):
        for j in range(len(traces[0])):
            if int(traces[i][j])!=0:
                sum+=int(traces[i][j])

    if optimizer == "perf_opt":
        optimizer = perf.perf_opt(traces,trace_function_names,server_pair,carbon_intensity) 
        a,b = optimizer.optimize()
    elif optimizer == "carbon_opt":
        optimizer = carbon_opt.carbon_opt(traces,trace_function_names,server_pair,carbon_intensity,kat_time) 
        optimizer.optimize()
    elif optimizer == "oracle":
        optimizer = oracle.oracle(traces,trace_function_names,server_pair,carbon_intensity,ci_avg, kat_time,STlambda) 
        optimizer.optimize() 
    elif optimizer == "tech":
        optimizer = tech.tech(traces,trace_function_names,server_pair,kat_time,STlambda,carbon_intensity,window_size,mem_old,mem_new,ci_max,function_mem_trace,pso_size,region)
        optimizer.optimize()
    # elif optimizer == "base":
    elif optimizer == "energy_opt":
        optimizer = energy_opt.energy_opt(traces,trace_function_names,server_pair,carbon_intensity,kat_time) 
        optimizer.optimize()
    elif optimizer == "random":
        optimizer = random_select.Random_Select(traces, trace_function_names,carbon_intensity,server_pair)
        optimizer.optimize()
    elif optimizer == "only_new":
        optimizer = only_new.only_new(traces, trace_function_names,carbon_intensity,server_pair)
        optimizer.optimize()
    elif optimizer == "only_old":
        optimizer = only_old.only_old(traces, trace_function_names,carbon_intensity,server_pair)
        optimizer.optimize()
    else: 
        sys.exit("input optimizer is not correct!")
   
if __name__ == "__main__":
    fire.Fire(main)