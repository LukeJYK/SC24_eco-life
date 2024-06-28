import sys 
sys.path.append("..") 
import utils
from pathlib import Path
import json

class perf_opt:
    def __init__(self,traces,trace_function_names,server_pair,ci_avg,window_size, interval)  -> None:
         self.traces = traces
         self.trace_function_names = trace_function_names
         self.server_pair = server_pair
         self.ci = ci_avg
         self.interval = interval
         self.window_size = window_size
    def optimize(self):
        function_num = len(self.traces)
        st_sum = 0
        carbon_sum = 0
        inovke_interval = []
        sum1 = 0
        result_st = {}
        result_carbon = {}
        
        for i in range(len(self.traces)):
            indices = [i for i, num in enumerate(self.traces[i][self.window_size:self.window_size+self.interval]) if int(num) != 0]
            nonzero_indices = [i+self.window_size for i in indices]
            inovke_interval = [nonzero_indices[i+1] - nonzero_indices[i] for i in range(len(nonzero_indices)-1)]
            result_st[i] = []
            result_carbon[i] = []

            for index, invoke in enumerate(inovke_interval):
                sum1+=int(self.traces[i][nonzero_indices[index]])
                cold_carbon,warm_carbon= utils.compute_exe(self.trace_function_names[i], self.server_pair,self.ci[nonzero_indices[index]])
                st_warm = utils.get_st(self.trace_function_names[i],self.server_pair[1])
                carbon_sum+=warm_carbon[1]*int(self.traces[i][nonzero_indices[index]])
                st_sum+=st_warm[1]*int(self.traces[i][nonzero_indices[index]])
                for _ in range(int(self.traces[i][nonzero_indices[index]])):
                    result_st[i].append(st_warm[1])
                kc = utils.compute_kat(self.trace_function_names[i], self.server_pair[1], invoke, self.ci[nonzero_indices[index]])
                carbon_sum+=int(self.traces[i][nonzero_indices[index]])*kc
                for _ in range(int(self.traces[i][nonzero_indices[index]])):
                    result_carbon[i].append(warm_carbon[1]+kc)   
            st_sum+=st_warm[1]*int(self.traces[i][nonzero_indices[-1]])
            carbon_sum+=warm_carbon[1]*int(self.traces[i][nonzero_indices[-1]])
            for _ in range(int(self.traces[i][nonzero_indices[-1]])):
                result_st[i].append(st_warm[1])
                result_carbon[i].append(warm_carbon[1])      
            print("finish trace:", i)
            print(f"current the avg time is:{st_sum/sum1}, and the avg carbon is {carbon_sum/sum1}")
        with open(f"{Path(__file__).parents[1]}/results/service_time_opt/st.json", "w") as file1:
            json.dump(result_st, file1, indent=4)
        with open(f"{Path(__file__).parents[1]}/results/service_time_opt/carbon.json", "w") as file2:
             json.dump(result_carbon, file2, indent=4)
        print("finish all traces!")
        print("--------------------------------------------------")