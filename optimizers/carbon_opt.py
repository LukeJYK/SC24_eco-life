import sys 
sys.path.append("..") 
import utils
from pathlib import Path
import json

class carbon_opt:
    def __init__(self,traces,trace_function_names,server_pair,ci_avg,window_size,interval)  -> None:
         self.traces = traces
         self.trace_function_names = trace_function_names
         self.server_pair = server_pair
         self.ci = ci_avg
         self.kat_time = [i for i in range(0,31)]
         self.window_size = window_size
         self.interval = interval
    def optimize(self):
        #time_length = len(self.traces[0])
        time_length = self.interval
        function_num = len(self.traces)
        function_carbon = {}
        function_st = {}
        sum_st = 0
        sum_carbon = 0
        sum_invoke1= 0
        for i in range(function_num):
            sum_invoke= 0
            old_st = utils.get_st(self.trace_function_names[i],self.server_pair[0])
            new_st = utils.get_st(self.trace_function_names[i],self.server_pair[1])
            
            result_st = []
            result_carbon = []
            for j in range(self.window_size,self.window_size+time_length):
                if int(self.traces[i][j])!=0:
                    sum_invoke1+=int(self.traces[i][j])
                    sum_invoke+=int(self.traces[i][j])
                    cold_carbon,warm_carbon= utils.compute_exe(self.trace_function_names[i], self.server_pair,self.ci[j])
                    st_carbon_per = []
                    kat_carbon_per = []
                    st_per = []
                    select_kat = []
                    for kat in self.kat_time:
                        if int(kat) == 0:
                            #old
                            carbon_1 = cold_carbon[0]
                            st_1 = old_st[0]
                            #new
                            carbon_2 = cold_carbon[1]
                            st_2 = new_st[0]
                            st_carbon_per.append(carbon_1)
                            kat_carbon_per.append(0)
                            st_per.append(st_1)
                            st_carbon_per.append(carbon_2)
                            st_per.append(st_2)
                            select_kat.append(0)
                            select_kat.append(0)
                            kat_carbon_per.append(0)
                            continue
                        
                        if j+kat>=self.window_size+self.interval:
                            
                            break
                        
                        if int(self.traces[i][j+kat]) == 0:
                            #kat old exe old,
                            old_kat_carbon = utils.compute_kat(self.trace_function_names[i], self.server_pair[0],kat,self.ci[j])
                            new_kat_carbon = utils.compute_kat(self.trace_function_names[i], self.server_pair[1],kat, self.ci[j]) 
                            kat_carbon_per.append(old_kat_carbon)
                            st_carbon_per.append(cold_carbon[0])
                            st_per.append(old_st[0])
                            select_kat.append(kat)
                            # kat old exe new, 
                            kat_carbon_per.append(old_kat_carbon)
                            st_carbon_per.append(cold_carbon[1])
                            select_kat.append(kat)
                            st_per.append(new_st[0])
                            # kat new exe old
                            kat_carbon_per.append(new_kat_carbon)
                            st_carbon_per.append(cold_carbon[0])
                            select_kat.append(kat)
                            st_per.append(old_st[0])
                            #kat new exe new
                            kat_carbon_per.append(new_kat_carbon)
                            st_carbon_per.append(cold_carbon[1])
                            st_per.append(new_st[0])
                            select_kat.append(kat)
                            
                        else:
                            #hit
                            #kat old exe old,
                            old_kat_carbon = utils.compute_kat(self.trace_function_names[i], self.server_pair[0],kat,self.ci[j])
                            new_kat_carbon = utils.compute_kat(self.trace_function_names[i], self.server_pair[1],kat, self.ci[j]) 
                            kat_carbon_per.append(old_kat_carbon)
                            st_carbon_per.append(warm_carbon[0])
                            st_per.append(old_st[1])
                            select_kat.append(kat)
                            # kat old exe new, 
                            kat_carbon_per.append(old_kat_carbon)
                            st_carbon_per.append(cold_carbon[1])
                            st_per.append(new_st[0])
                            select_kat.append(kat)
                            # kat new exe old
                            kat_carbon_per.append(new_kat_carbon)
                            st_carbon_per.append(cold_carbon[0])
                            st_per.append(old_st[0])
                            select_kat.append(kat)
                            #kat new exe new
                            kat_carbon_per.append(new_kat_carbon)
                            st_carbon_per.append(warm_carbon[1])
                            st_per.append(new_st[1])
                            select_kat.append(kat)
                            break
                    
                    carbon_list = [x + y for x, y in zip(kat_carbon_per, st_carbon_per)]
                    index = carbon_list.index(min(carbon_list))
                    my_kat = select_kat[index]
                    if int(self.traces[i][j+my_kat])!=0:
                        #warm
                        for _ in range(int(self.traces[i][j])):
                            result_st.append( (int(self.traces[i][j+my_kat])*kat_carbon_per[index]+ min(int(self.traces[i][j]),int(self.traces[i][j+my_kat])) *st_carbon_per[index])/int(self.traces[i][j]) )
                            result_carbon.append(st_per[index])
                    else:
                        #cold
                        for _ in range(int(self.traces[i][j])):
                            result_st.append(kat_carbon_per[index]+st_carbon_per[index])
                            result_carbon.append(st_per[index])
            #complete on function
            assert len(result_st) == sum_invoke
            assert len(result_carbon) == sum_invoke
            function_st[i] = result_st
            function_carbon[i] = result_carbon
            sum_st+=sum(result_st)
            sum_carbon+=sum(result_carbon)
            print("finish trace",i)
            print(f"current the avg time is:{sum_carbon/sum_invoke1}, and the avg carbon is {sum_st/sum_invoke1}")
        with open(f"{Path(__file__).parents[1]}/results/carbon_opt/st.json", "w") as file1:
            json.dump(function_carbon, file1, indent=4)
        with open(f"{Path(__file__).parents[1]}/results/carbon_opt/carbon.json", "w") as file2:
            json.dump(function_st, file2, indent=4)
        print("finish all traces!")
        print("--------------------------------------------------")
