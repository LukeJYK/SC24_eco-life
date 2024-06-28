import utils
import sys
def exe_loc_decision(old_warm_pool, 
                     new_warm_pool,
                     function,
                     invocation,
                     old_cold_st,
                     new_cold_st,
                     old_cold_carbon,
                     new_cold_carbon,
                     old_warm_st,
                     new_warm_st,
                     old_warm_carbon,
                     new_warm_carbon,
                     STlambda,name,server_pair,ci,cur_time,result_st,result_carbon):
    service_time = 0
    carbon = 0
    kat_carbon = 0
    old_score = STlambda*(old_warm_st/max(new_cold_st,old_cold_st)) + (1-STlambda)*(old_warm_carbon/max(old_cold_carbon,new_cold_carbon))
    new_score = STlambda*(new_warm_st/max(new_cold_st,old_cold_st)) + (1-STlambda)*(new_warm_carbon/max(old_cold_carbon,new_cold_carbon))

    cold_old_score = STlambda*(old_cold_st/max(new_cold_st,old_cold_st)) + (1-STlambda)*(old_cold_carbon/max(old_cold_carbon,new_cold_carbon))
    cold_new_score = STlambda*(new_cold_st/max(new_cold_st,old_cold_st)) + (1-STlambda)*(new_cold_carbon/max(old_cold_carbon,new_cold_carbon))
    #write result:
    if cur_time not in result_carbon:
        result_carbon[cur_time] = {"num":invocation,"carbon":0}
        result_st[cur_time] =  {"num":invocation,"st":0}
    else:
        sys.exit("error")
    if function in old_warm_pool or function in new_warm_pool:
        '''
        This function has been kept alive in the pool, warm start
        note: function is the function index
        '''
        # assert(function)
        if function in old_warm_pool:
            num_in_old = int(old_warm_pool[function]["num"])
            
            
        else:
            num_in_old =0
        if function in new_warm_pool:
            num_in_new = int(new_warm_pool[function]["num"])
        else: 
            num_in_new = 0
        if num_in_old == 0 and num_in_new>0:
            start = int(new_warm_pool[function]['start_time'])
            kat =cur_time-start
            kat_carbon+=utils.compute_kat(name, server_pair[1], kat, ci[start])*num_in_new
            invoke_time= int(new_warm_pool[function]['invoke_time'])
            result_carbon[invoke_time]["carbon"]+= kat_carbon
    
        elif num_in_old>0 and num_in_new==0:
            start = int(old_warm_pool[function]['start_time'])
            kat =cur_time-start
            kat_carbon+=utils.compute_kat(name, server_pair[0],kat, ci[start])*num_in_old
            invoke_time= int(old_warm_pool[function]['invoke_time'])
            result_carbon[invoke_time]["carbon"]+= kat_carbon
        elif num_in_new>0 and num_in_old>0:
            start1 = int(new_warm_pool[function]['start_time'])
            start2 = int(old_warm_pool[function]['start_time'])
            kat1 =cur_time-start1
            kat2 = cur_time-start2
            kat_carbon+=utils.compute_kat(name, server_pair[1], kat1, ci[start1])*num_in_new
            kat_carbon+=utils.compute_kat(name, server_pair[0], kat2, ci[start2])*num_in_old
            
            invoke_time1= int(old_warm_pool[function]['invoke_time'])
            invoke_time2= int(new_warm_pool[function]['invoke_time'])
            assert(invoke_time1==invoke_time2)
            result_carbon[invoke_time1]["carbon"]+= kat_carbon
        else:
            sys.exit("error")
            
            
        
    
        if old_score>new_score:
            #get all from new
            if num_in_new >= invocation:
                service_time += invocation*new_warm_st
                carbon += invocation*new_warm_carbon
                
            else:
                #get some from old
                remain = invocation-num_in_new
                service_time += num_in_new*new_warm_st
                carbon += num_in_new*new_warm_carbon
                
  
                if remain<=num_in_old:
                    #
                    service_time += remain*old_warm_st
                    carbon += remain*old_warm_carbon
                    
                else:
                    service_time += num_in_old*old_warm_st
                    carbon += num_in_old*old_warm_carbon
                    #some needs cold start
                    if cold_old_score<cold_new_score:
                        #on old
                        service_time += (remain-num_in_old)*old_cold_st
                        carbon += (remain-num_in_old)*old_cold_carbon
                    else:
                        #on new
                        service_time += (remain-num_in_old)*new_cold_st
                        carbon += (remain-num_in_old)*new_cold_carbon
                
        else:
            #get all from old
            if num_in_old >= invocation:
                service_time += invocation*old_warm_st
                carbon += invocation*old_warm_carbon
            else:
                #get some from new
                remain = invocation-num_in_old
                service_time += num_in_old*old_warm_st
                carbon += num_in_old*old_warm_carbon
                if remain<=num_in_new:
                    #
                    service_time += remain*new_warm_st
                    carbon += remain*new_warm_carbon
                else:
                    service_time += num_in_new*new_warm_st
                    carbon += num_in_new*new_warm_carbon
                    #some needs cold start
                    if cold_old_score<cold_new_score:
                        #on old
                        service_time += (remain-num_in_new)*old_cold_st
                        carbon += (remain-num_in_new)*old_cold_carbon
                    else:
                        #on new
                        service_time += (remain-num_in_new)*new_cold_st
                        carbon += (remain-num_in_new)*new_cold_carbon
    else:
        '''
        no keep alive at all
        '''
        if cold_old_score<cold_new_score:
             #on old
            service_time += invocation*old_cold_st
            carbon +=invocation*old_cold_carbon
        else:
            #on new
            service_time += invocation*new_cold_st
            carbon += invocation*new_cold_carbon
    if function in new_warm_pool:
        del new_warm_pool[function] 
    if function in old_warm_pool:
        del old_warm_pool[function] 
    
    #write result
    result_carbon[cur_time]["carbon"]+=carbon
    result_st[cur_time]["st"]+=service_time
    
    carbon = carbon+kat_carbon
    return service_time, carbon, result_st, result_carbon