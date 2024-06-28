import fire
import utils
import pandas as pd
from pathlib import Path
from optimizers import  perf_opt,carbon_opt,oracle,tech
import sys

def main(
    region: str="US-CAL",
    start_hour: int=800,
    interval: int=12*24*60,
    mem_old: int = 512,
    mem_new: int = 512,
    app_list: list = None,
    server_pair: list = ['i3','m5zn'],
    kat_time:list = [i for i in range(0,31)],
    optimizer: str = 'eco-life',
    STlambda:float = 0.5,
    window_size: int = 20,
    pso_size: int = 15
):
    if app_list is None:
        df = pd.read_csv(f"{Path(__file__).parents[0]}/function_mem.csv",header=None) 
        app_list = df.iloc[:, 0].tolist()
    # load carbon intensity data
    carbon_intensity, ci_max, ci_min,ci_avg = utils.load_carbon_intensity(region, start_hour, interval)

    #load trace:
    traces, trace_function_names,_ = utils.read_selected_traces()
    for trace in traces:
        assert len(trace) == len(carbon_intensity)
    function_mem_trace = [utils.read_func_mem_size(trace_function_names[i]) for i in range(len(traces))]
    
    sum=0

    for i in range(len(traces)):
        for j in range(len(traces[0])):
            if int(traces[i][j])!=0:
                sum+=int(traces[i][j])

    if optimizer == "perf_opt":
        optimizer = perf_opt.perf_opt(traces,trace_function_names,server_pair,carbon_intensity,window_size,interval) 
        optimizer.optimize()
    elif optimizer == "carbon_opt":
        optimizer = carbon_opt.carbon_opt(traces,trace_function_names,server_pair,carbon_intensity,window_size,interval) 
        optimizer.optimize()
    elif optimizer == "oracle":
        optimizer = oracle.oracle(traces,trace_function_names,server_pair,carbon_intensity,ci_avg,STlambda, window_size,interval) 
        optimizer.optimize() 
    elif optimizer == "eco-life":
        optimizer = tech.tech(traces,trace_function_names,server_pair,kat_time,STlambda,carbon_intensity,window_size,mem_old,mem_new,ci_max,function_mem_trace,pso_size,region,interval)
        optimizer.optimize()
    else: 
        sys.exit("input optimizer is not correct!")
   
if __name__ == "__main__":
    fire.Fire(main)
