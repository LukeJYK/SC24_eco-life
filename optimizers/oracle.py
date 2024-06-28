import sys 
sys.path.append("..") 
import utils
import json
from pathlib import Path
import numpy as np

class oracle:
    def __init__(self,traces,trace_function_names,server_pair,ci,ci_max, STlambda,window_size,interval)  -> None:
         self.traces = traces
         self.trace_function_names = trace_function_names
         self.server_pair = server_pair
         self.ci = ci
         self.kat_time = [i for i in range(0,31)]
         self.ci_max =ci_max
         self.STlambda =STlambda
         self.ci_avg = np.mean(ci)
         self.window_size = window_size
         self.interval = interval
    def optimize(self):

        time_length = len(self.traces[0])
        function_num = len(self.traces)
        
        function_carbon = {}
        function_st = {}
        sum_st = 0
        sum_carbon = 0
        sum_invoke = 0
        for i in range(function_num):
            sum_invoke1= 0
            old_st = utils.get_st(self.trace_function_names[i],self.server_pair[0])
            new_st = utils.get_st(self.trace_function_names[i],self.server_pair[1])
            max_st =  max(old_st[0],new_st[0])
            cold_carbon_max,warm_carbon_max= utils.compute_exe(self.trace_function_names[i], self.server_pair,self.ci_max)
            max_carbon_st = max(cold_carbon_max)
            
            max_carbon_kat = max(utils.compute_kat(self.trace_function_names[i], self.server_pair[0],7, self.ci_max),utils.compute_kat(self.trace_function_names[i], self.server_pair[1],7,self.ci_max))
         
            
            #store the results for each function
            result_st = []
            result_carbon = []
            
            for j in range(self.window_size,self.window_size+self.interval):
                if int(self.traces[i][j])!=0:
                    sum_invoke+=int(self.traces[i][j])
                    sum_invoke1+=int(self.traces[i][j])
                    cold_carbon,warm_carbon= utils.compute_exe(self.trace_function_names[i], self.server_pair,self.ci[j])
                    st_carbon_per = []
                    kat_carbon_per = []
                    st_per = []
                    select_kat = []
                    #choices of kat
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
                            select_kat.append(0)
                            st_per.append(st_1)
                            st_carbon_per.append(carbon_2)
                            st_per.append(st_2)
                            kat_carbon_per.append(0)
                            select_kat.append(0)
                            continue
                        
                        if kat+j>=self.window_size+self.interval:
                            
                            break
                        
                        if int(self.traces[i][j+kat]) == 0:
                            #kat old exe old,
                            old_kat_carbon = utils.compute_kat(self.trace_function_names[i],self.server_pair[0],kat,self.ci[j])
                            new_kat_carbon = utils.compute_kat(self.trace_function_names[i], self.server_pair[1],kat,self.ci[j]) 
                            kat_carbon_per.append(old_kat_carbon)
                            st_carbon_per.append(cold_carbon[0])
                            st_per.append(old_st[0])
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
                            st_carbon_per.append(cold_carbon[1])
                            st_per.append(new_st[0])
                            select_kat.append(kat)
                            
                        else:
                            #hit
                            #kat old exe old,
                            old_kat_carbon = utils.compute_kat(self.trace_function_names[i], self.server_pair[0],kat,self.ci[j])
                            new_kat_carbon = utils.compute_kat(self.trace_function_names[i], self.server_pair[1],kat,self.ci[j]) 
                            kat_carbon_per.append(old_kat_carbon)
                            st_carbon_per.append(warm_carbon[0])
                            st_per.append(old_st[1])
                            select_kat.append(kat)
                            #kat new exe new
                            kat_carbon_per.append(new_kat_carbon)
                            st_carbon_per.append(warm_carbon[1])
                            st_per.append(new_st[1])
                            select_kat.append(kat)
                            break
                    st_norm_list = [x/max_st for x in st_per]
                    carbon_norm_list = [x/max_carbon_st+y/max_carbon_kat for x,y in zip(st_carbon_per,kat_carbon_per)]
                    score_list = [(1-self.STlambda)*x + self.STlambda*y for x, y in zip(carbon_norm_list,st_norm_list)]
                    index = score_list.index(min(score_list))
                    my_kat = select_kat[index]

                    #this is the best choice 
                    if int(self.traces[i][j+my_kat])!=0:
                        #warm
                        for _ in range(int(self.traces[i][j])):
                            result_st.append( (int(self.traces[i][j+my_kat])*kat_carbon_per[index]+ min(int(self.traces[i][j]),int(self.traces[i][j+my_kat])) *st_carbon_per[index])/int(self.traces[i][j]) )
                            result_carbon.append(st_per[index])
                    elif int(self.traces[i][j+my_kat])==0:
                        #cold
                        for _ in range(int(self.traces[i][j])):
                            result_st.append(kat_carbon_per[index]+st_carbon_per[index])
                            result_carbon.append(st_per[index])
                    else:
                        sys.exit("error")
            #complete on function
            assert len(result_st) == sum_invoke1
            assert len(result_carbon) == sum_invoke1
            function_st[i] = result_st
            function_carbon[i] = result_carbon
            sum_st+=sum(result_st)
            sum_carbon+=sum(result_carbon)
            print("finish trace:",i)   
            print(f"current time is {sum_carbon/sum_invoke}, service carbon is {sum_st/sum_invoke}")
        with open(f"{Path(__file__).parents[1]}/results/oracle/st.json", "w") as file1:
            json.dump(function_carbon, file1, indent=4)
        with open(f"{Path(__file__).parents[1]}/results/oracle/carbon.json", "w") as file2:
            json.dump(function_st, file2, indent=4)
        print("finish all traces!")
        print("--------------------------------------------------")          
                
            
                        
            