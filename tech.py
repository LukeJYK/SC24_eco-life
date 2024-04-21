import numpy as np
from pathlib import Path
import pandas as pd
import sys 
sys.path.append("..") 
import utils
import exe_decide
import pso
from pathlib import Path
import json
import time
class tech:
    def __init__(self,
                traces: list,
                trace_function_names: list,
                server_pair: list,
                kat_time:list,
                st_lambda,
                carbon_intenstiy: list,
                window_size:int,
                mem_old_limit:int,
                mem_new_limit:int,
                ci_avg:float,
                function_mem_trace:list,
                pso_size:int,
                region:str
                )  -> None:
         self.traces = traces
         self.trace_function_names = trace_function_names
         self.server_pair = server_pair
         self.carbon_intensity = carbon_intenstiy
         self.kat_time = [int (x) for x in kat_time]
         self.st_lambda =st_lambda
         self.carbon_lambda = 1-self.st_lambda
         self.window_size = window_size
         self.mem_old_limit = mem_old_limit
         self.mem_new_limit = mem_new_limit
         self.ci_avg = ci_avg
         self.function_mem_trace = function_mem_trace
         self.pso_size = pso_size
         self.region = region
    def optimize(self):
        
        time_length = len(self.traces[0])
        function_num = len(self.traces)
        invoke_interval = [[] for _ in range(function_num)]#this is used for the past window size invocation interval
        old_warm_pool = {}
        new_warm_pool = {}

        new_function={}
        sum_st = 0
        sum_carbon = 0
        discard_list = []
        result_st = [{} for _ in  range(function_num)]
        result_carbon = [{} for _ in  range(function_num)]
        sum1 = 0
        for i in range(function_num):
            result_st[i] = {}
            
        for i in range(function_num):
            result_carbon[i] = {}

        for j in range(self.window_size,self.window_size+1440):
            print(f"begin{j}")
            old_decision = {}
            new_decision = {}
            # making execution decision
            start = time.time()
            sum_discard =0
            sum_per_function = 0
            for i in range(function_num):
                window_invoc = self.traces[i][j-self.window_size:j]
                invoc_index = [i for i, num in enumerate(window_invoc) if int(num) != 0]
                interval = [invoc_index[i+1] - invoc_index[i] for i in range(len(invoc_index)-1)]
                invoke_interval[i].append(interval)
                
                function_name = self.trace_function_names[i]
                old_cold_st, old_warm_st = utils.get_st(function_name, self.server_pair[0])
                new_cold_st, new_warm_st = utils.get_st(function_name, self.server_pair[1])
                cold_carbon, warm_carbon = utils.compute_exe(function_name, self.server_pair,self.carbon_intensity[j])
                old_cold_carbon = cold_carbon[0]
                new_cold_carbon =cold_carbon[1]
                old_warm_carbon = warm_carbon[0]
                new_warm_carbon = warm_carbon[1]
                
                concurrent_function = int(self.traces[i][j])
                
                if concurrent_function==0:
                    # this function in not invoked, if it contains in the warm pool, then we need to check whether it is expired
                    if i in old_warm_pool:
                        if int(old_warm_pool[i]["end_time"]) <= j:
                            
                            last = int(old_warm_pool[i]["end_time"]) - int(old_warm_pool[i]["start_time"])
                            kat_carbon = int(old_warm_pool[i]['num'])*utils.compute_kat(function_name,self.server_pair[0],last,self.carbon_intensity[int(old_warm_pool[i]["start_time"])])
                            sum_carbon += kat_carbon
                            
                            #write result:
                            invoke_time = int(old_warm_pool[i]["invoke_time"])
                            if invoke_time not in result_carbon[i]:
                                sys.exit("error")
                            else:
                                result_carbon[i][invoke_time]["carbon"]+=kat_carbon
                                
                            
                            
                            del old_warm_pool[i]
                    if i in new_warm_pool:
                        if new_warm_pool[i]["end_time"] <= j:
                            last = int(new_warm_pool[i]["end_time"] - new_warm_pool[i]["start_time"])
                            kat_carbon = int(new_warm_pool[i]['num'])*utils.compute_kat(function_name,self.server_pair[1],last,self.carbon_intensity[new_warm_pool[i]["start_time"]])
                            sum_carbon += kat_carbon
                            
                            #write result:
                            invoke_time = int(new_warm_pool[i]["invoke_time"])
                            if invoke_time not in result_carbon[i]:
                                sys.exit("error")
                            else:
                                result_carbon[i][invoke_time]["carbon"]+=kat_carbon
                            
                            
                            del new_warm_pool[i]
                else:
                    sum_per_function +=concurrent_function
                    sum1+=concurrent_function
                    #execute function:
                    st_per_func,carbon_per_func = exe_decide.exe_loc_decision(old_warm_pool, 
                     new_warm_pool,
                     i,
                     concurrent_function,
                     old_cold_st,
                     new_cold_st,
                     old_cold_carbon,
                     new_cold_carbon,
                     old_warm_st,
                     new_warm_st,
                     old_warm_carbon,
                     new_warm_carbon,
                     self.st_lambda,
                     self.trace_function_names[i],
                     self.server_pair,
                     self.carbon_intensity,int(j),result_st[i],result_carbon[i])
                    assert(st_per_func>0)
                    assert(carbon_per_func>0)
                    sum_st+=st_per_func
                    sum_carbon+=carbon_per_func
                
                    # function is invoked    
                    if i not in new_function:
                        #first invoke set the pso optimzier
                        parameters = [self.pso_size,self.kat_time, self.st_lambda]
                        new_function[i]= pso.PSO(parameters,self.server_pair,function_name,self.ci_avg,self.carbon_intensity[j],invoke_interval[i][j-self.window_size])
                        a,_ = new_function[i].main(self.carbon_intensity[j],invoke_interval[i][j-self.window_size])
                        decision = a
                        ka_loc = int(decision[0])
                        ka_last = int(decision[1])
                        if ka_loc == 0 and ka_last!=0:
                            going_ka = {"num":int(self.traces[i][j]),
                            "start_time":j,
                            "end_time":int(j+ka_last),
                            "invoke_time":int(j)
                             }
                            old_decision[i] = going_ka
                        elif ka_loc == 1 and ka_last!=0:
                            going_ka = {"num":int(self.traces[i][j]),
                            "start_time":j,
                            "end_time":int(j+ka_last),
                            "invoke_time":int(j)
                             }
                            new_decision[i] = going_ka
                        else:
                            pass
                    else: 
                        
                        decision,b = new_function[i].main(self.carbon_intensity[j],invoke_interval[i][j-self.window_size])
                        ka_loc = int(decision[0])
                        ka_last = int(decision[1])
                        if ka_loc == 0 and ka_last!=0:
                            going_ka = {"num":int(self.traces[i][j]),
                            "start_time":j,
                            "end_time":int(j+ka_last),
                            "invoke_time":int(j)
                            }
                            old_decision[i] = going_ka
                        elif ka_loc == 1 and ka_last!=0:
                            going_ka = {"num":int(self.traces[i][j]),
                            "start_time":int(j),
                            "end_time":int(j+ka_last),
                            "invoke_time":int(j)
                             }
                            new_decision[i] = going_ka
                        else:
                            pass

            
            mem_checker =utils.mem_check(self.mem_new_limit,self.mem_old_limit, old_decision,new_decision,self.function_mem_trace,new_warm_pool,old_warm_pool)
            if mem_checker==0:
                #not exceed the mem limit
                for key, value in old_decision.items():
                    old_warm_pool[key] = value
                for key, value in new_decision.items():
                    new_warm_pool[key] = value

            elif  mem_checker==1:
                #change old
                for key, value in new_decision.items():
                    new_warm_pool[key] = value
                old_warm_pool,left_pool,kat_carbon = utils.adjust_pool(self.mem_old_limit,self.function_mem_trace,old_warm_pool,old_decision,invoke_interval,0,self.trace_function_names,self.server_pair,self.carbon_intensity,int(j),self.window_size,result_carbon)
                sum_carbon+=kat_carbon
                new_warm_pool,kat_carbon1,discard = utils.add_discard_pool(new_warm_pool,left_pool,self.mem_new_limit,self.function_mem_trace,self.trace_function_names,1,invoke_interval,self.server_pair,int(j),self.window_size,self.carbon_intensity,result_carbon)
                sum_carbon+=kat_carbon1
                if discard!=0:
                    for key,value in discard.items():
                        sum_discard+=value['num']
                #exceed old mem limit
            elif mem_checker ==2:
                for key, value in old_decision.items():
                    old_warm_pool[key] = value
                new_warm_pool,left_pool,kat_carbon = utils.adjust_pool(self.mem_new_limit,self.function_mem_trace,new_warm_pool,new_decision,invoke_interval,1,self.trace_function_names,self.server_pair,self.carbon_intensity,j,self.window_size,result_carbon)
                sum_carbon+=kat_carbon
                old_warm_pool,kat_carbon1,discard = utils.add_discard_pool(old_warm_pool,left_pool,self.mem_old_limit,self.function_mem_trace,self.trace_function_names,0,invoke_interval,self.server_pair,int(j),self.window_size,self.carbon_intensity,result_carbon)
                sum_carbon+=kat_carbon1
                if discard!=0:
                    for key,value in discard.items():
                        sum_discard+=value['num']
                #change new
            elif mem_checker ==3:
                old_warm_pool,left1,kat_carbon1 = utils.adjust_pool(self.mem_old_limit,self.function_mem_trace,old_warm_pool,old_decision,invoke_interval,0,self.trace_function_names,self.server_pair,self.carbon_intensity,int(j),self.window_size,result_carbon)
                new_warm_pool,left2,kat_carbon2 = utils.adjust_pool(self.mem_new_limit,self.function_mem_trace,new_warm_pool,new_decision,invoke_interval,1,self.trace_function_names,self.server_pair,self.carbon_intensity,int(j),self.window_size,result_carbon)
                sum_carbon+=kat_carbon1+kat_carbon2
                for key,value in left1.items():
                    sum_discard+=value['num']
                for key,value in left2.items():
                    sum_discard+=value['num']
            else:
                sys.exit("mem_checker is not correct!")     
            # print("time:",(time.time()-start)/sum_per_function)
            print(f"end {j}")
            discard_list.append(sum_discard)
            print(f"discard funcions: {sum_discard}")
            print(f"service time is:{sum_st/sum1}, carbon is: {sum_carbon/sum1}")
        print(f"service time is:{sum_st/sum1}, carbon is: {sum_carbon/sum1}")
        # with open(f"{Path(__file__).parents[1]}/results/result_eco_carbon_.json", "w") as file:
        #     json.dump(result_carbon, file, indent=4)
        # with open(f"{Path(__file__).parents[1]}/results/result_eco_st_{self.mem_new_limit}_{self.mem_old_limit}.json", "w") as file:
        #     json.dump(result_st, file, indent=4)
        # with open(f"{Path(__file__).parents[1]}/results/discard_with_adjust_{self.mem_new_limit}_{self.mem_old_limit}.json", "w") as file:
        #     json.dump(discard_list, file, indent=4)