import numpy as np
import random
import utils
class PSO:
    def __init__(self, parameters,server_pair,function_name,ci_avg,cur_ci,cur_interval):
        self.max_delta_ci = 0.1
        self.prev_ci = cur_ci
        self.max_delta_fn =0.1
        self.prev_fn = len(cur_interval)
        self.w = 1
        #parameters = [size,kat_time, lambda]
        self.iteration = 1
        self.size = parameters[0]   
        self.var_num = 2
        self.var_1 = [0,1]#kat
        self.var_2 = parameters[1]# choices of kat
        self.lam = parameters[2]#lamda to control service time
        self.server_pair = server_pair
        #self.function
        self.pop_x = np.zeros((self.size, self.var_num))    # partical loc
        self.pop_v = np.zeros((self.size, self.var_num))    # partical v
        self.p_best = np.zeros((self.size, self.var_num))   # best partical loc
        self.g_best = np.zeros((1, self.var_num))   # globel partical loc
        self.function_name = function_name
        # compute max:
        old_cold,_ = utils.get_st(function_name, server_pair[0])
        new_cold,_ = utils.get_st(function_name, server_pair[1])
        cold_carbon_max,_= utils.compute_exe(function_name, server_pair,ci_avg)
        self.max_st = max(old_cold, new_cold)
        self.max_carbon_st = max(cold_carbon_max)
        self.max_carbon_kat = max(utils.compute_kat(function_name, server_pair[0],7, ci_avg),utils.compute_kat(function_name, server_pair[1],7, ci_avg))
        #self.first_ci = cur_ci
        self.bound = [[0,0],[1,max(self.var_2)]]#setting bound
        temp = np.inf
        self.temp=0
        self.st_score = []
        self.carbon_score = []
        for i in range(self.size):
            self.pop_x[i][0] = int(random.choice(self.var_1))
            self.pop_x[i][1] = int(random.choice(self.var_2))
            for j in range(self.var_num):
                self.pop_v[i][j] = random.uniform(0, 1)
            self.p_best[i] = self.pop_x[i]  
            fit = self.fitness(self.p_best[i], cur_ci,cur_interval)
            # print("{} the score is {}".format(self.p_best[i], fit))
            if fit < temp:
                self.g_best = self.p_best[i]
                temp = fit
        self.temp=temp
        
        
    def prob_cold(self, cur_interval, kat):
        
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
            
    def fitness(self,var,ci, past_interval):
        var = var.astype(int)
        ka_loc = var[0]
        kat = var[1]
        #kat carbon 
        score = 0
        old_kat_carbon = utils.compute_kat(self.function_name, self.server_pair[0],kat,ci)
        new_kat_carbon = utils.compute_kat(self.function_name, self.server_pair[1],kat, ci)
        cold_carbon,warm_carbon= utils.compute_exe(self.function_name, self.server_pair, ci)
        
        old_st = utils.get_st(self.function_name,self.server_pair[0])
        new_st = utils.get_st(self.function_name,self.server_pair[1])
        score += (1-self.lam) * (((1-ka_loc)*old_kat_carbon+ka_loc*new_kat_carbon)/self.max_carbon_kat)
    
        #print((1-self.lam) * (((1-ka_loc)*old_kat_carbon+ka_loc*new_kat_carbon)/self.max_carbon_kat))
        # expectation for st and carbon_st

        cold_prob, warm_prob = self.prob_cold(past_interval,kat)
        part_time_prob = cold_prob*((1-ka_loc)*old_st[0]+ ka_loc*new_st[0])+warm_prob*((1-ka_loc)*old_st[1]+ ka_loc*new_st[1])
        part_carbon_prob = cold_prob*((1-ka_loc)*cold_carbon[0]+ ka_loc*cold_carbon[1])+warm_prob*((1-ka_loc)*warm_carbon[0]+ ka_loc*warm_carbon[1])
        score += self.lam*(part_time_prob)/self.max_st
        score += (1-self.lam)*(part_carbon_prob)/(self.max_carbon_st)
        return score
        
            
        
 
    def update_operator(self,ci,past_interval,diff_ci,diff_fn):
        w_max = 1
        w_min = 0.5
        c1_min = 0.3
        c1_max =1
        c2_min = 0.3
        c2_max =1
        self.w= w_max*(diff_fn/self.max_delta_fn+diff_ci/self.max_delta_ci)
        c1 =  c1_max*(1-(diff_fn/self.max_delta_fn+diff_ci/self.max_delta_ci))
        c2 = c2_max*(1-(diff_fn/self.max_delta_fn+diff_ci/self.max_delta_ci))
        
        if self.w < w_min:
            self.w = w_min
        elif self.w > w_max:
            self.w = w_max
        if c1 < c1_min:
            c1 = c1_min
        elif c1 > c1_max:
            c1 = c1_max
        if c2 < c2_min:
            c2 = c2_min
        elif c2 > c2_max:
            c2 = c2_max
        for i in range(self.size):
            #update v
            #print("previous:{}".format(self.pop_x[i]))
            # print(self.g_best - self.pop_x[i])
            self.pop_v[i] =self.w * self.pop_v[i] + c1 * random.uniform(0, 1) * (
                        self.p_best[i] - self.pop_x[i]) + c2 *random.uniform(0, 1) * (self.g_best - self.pop_x[i])
            
            self.pop_x[i] = self.pop_x[i] + self.pop_v[i]
            #print("before:{}".format(self.pop_x[i]))
            self.pop_x[i] = self.pop_x[i].astype(int)
            #print(self.pop_v[i])
            # boundary
            for j in range(self.var_num):
                if self.pop_x[i][j] < self.bound[0][j]:
                    self.pop_x[i][j] = self.bound[0][j]
                if self.pop_x[i][j] > self.bound[1][j]:
                    self.pop_x[i][j] = self.bound[1][j]
            #print("current:{}".format(self.pop_x[i]))
            # update
            if self.fitness(self.pop_x[i],ci,past_interval) < self.fitness(self.p_best[i],ci,past_interval):
                self.p_best[i] = self.pop_x[i]
            if self.fitness(self.pop_x[i],ci,past_interval) < self.fitness(self.g_best,ci,past_interval):
                self.g_best = self.pop_x[i]
 
    def main(self,ci,past_interval):
        #how many particles need to be randomly initialized
        diff_ci = abs(ci-self.prev_ci)
        diff_fn = abs(len(past_interval)-self.prev_fn)
        half_indices = np.random.choice(int(self.size/2), int(self.size /2), replace=False)
        if diff_fn/self.max_delta_fn or diff_ci/self.max_delta_ci >0:
            for index in half_indices:
                i = half_indices[index]
                self.pop_x[i][0] = int(random.choice(self.var_1))
                self.pop_x[i][1] = int(random.choice(self.var_2))
                #self.p_best[i] = self.pop_x[i]
        for i in range(self.size):      
            for j in range(self.var_num):
                    self.pop_v[i][j] = random.uniform(0, 1)
                
        
            
        
        
        for _ in range(1):
            self.update_operator(ci,past_interval,diff_ci,diff_fn)
        if diff_ci>self.max_delta_ci:
            self.max_delta_ci = diff_ci
        if diff_fn>self.max_delta_fn:
            self.max_delta_fn = diff_fn
        self.prev_ci = ci
        self.prev_fn = len(past_interval)
        return self.g_best,self.p_best
    