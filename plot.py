import json
import sys
import numpy as np
import matplotlib
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
# gill sans
import matplotlib.pyplot as plt
plt.rcParams["font.family"] = "Gill Sans"
import sys 
sys.path.append("..") 
import matplotlib.ticker as mtick
import fire
import utils

def read_json_file(file_path):
    with open(file_path, 'r') as file:
        data = json.load(file)
        return data
    
def verify(
    window_size: int=20,
    interval: int=24*60,
):
    traces, trace_function_names,original_names = utils.read_selected_traces()
    sum_invoke = 0
    for j in range(window_size, window_size+interval):
         for i in range(len(traces)):
                if int(traces[i][j])!=0:
                    sum_invoke+=int(traces[i][j])
                    
    #read the oracle results
    oracle_carbon = read_json_file("./results/oracle/carbon.json")
    oracle_st = read_json_file("./results/oracle/st.json")

    sum_carbon_oracle = 0
    sum_st_oracle =0

    for i in range(len(traces)):
        sum_carbon_oracle+=np.sum(oracle_carbon[str(i)])
        sum_st_oracle+=np.sum(oracle_st[str(i)])   
    print(f"Oracle AVG Carbon is:{sum_carbon_oracle/sum_invoke}, Oracle AVG Service Time is: {sum_st_oracle/sum_invoke}")

    #read the performance optimal results
    perf_carbon = read_json_file("./results/service_time_opt/carbon.json")
    perf_st = read_json_file("./results/service_time_opt/st.json")

    sum_carbon_perf = 0
    sum_st_perf =0

    for i in range(len(traces)):
        sum_carbon_perf+=np.sum(perf_carbon[str(i)])
        sum_st_perf+=np.sum(perf_st[str(i)])
    print(f"Performance Optimal AVG Carbon is:{sum_carbon_perf/sum_invoke}, Performance Optimal AVG Service Time is: {sum_st_perf/sum_invoke}")

    #read the carbon optimal results
    carbon_carbon = read_json_file("./results/carbon_opt/carbon.json")
    carbon_st = read_json_file("./results/carbon_opt/st.json")

    sum_carbon_carbon = 0
    sum_st_carbon =0

    for i in range(len(traces)):
        sum_carbon_carbon+=np.sum(carbon_carbon[str(i)])
        sum_st_carbon+=np.sum(carbon_st[str(i)])
    print(f"Carbon Optimal AVG Carbon is:{sum_carbon_carbon/sum_invoke}, Carbon Optimal AVG Service Time is: {sum_st_carbon/sum_invoke}")
    
    #read the eco-life results:
    eco_carbon = read_json_file("./results/eco_life/carbon.json")
    eco_st = read_json_file("./results/eco_life/st.json")
    
    sum_carbon_eco = 0
    sum_st_eco =0
    
    for i in range(len(traces)):
        for _,value in eco_carbon[i].items():
            sum_carbon_eco += value["carbon"]
        for _,value in eco_st[i].items():
            sum_st_eco += value["st"]
        
    print(f"Eco-life AVG Carbon is:{sum_carbon_eco/sum_invoke}, Eco-life AVG Service Time is: {sum_st_eco/sum_invoke}")
    
    #plot
    fig, axs = plt.subplots(nrows=1, ncols=1, gridspec_kw={'hspace': 0.4, 'wspace': 0.1, 'bottom': 0.2, 
                    'top': 0.8, 'right':0.995, 'left':0.17}, figsize=(6.5,3), sharey=True)
    FONTSIZE =13
    XLABEL = "CO$_2$ Footprint \n(% increase w.r.t.Carbon-Opt)"
    YLABEL = "Service Time (%\n increase w.r.t.\nService-Time-Opt)"
    x_move = 0
    y_move =0
    min_st = min(sum_st_carbon/sum_invoke, sum_st_oracle/sum_invoke, sum_st_perf/sum_invoke, sum_st_eco/sum_invoke)
    min_carbon = min(sum_carbon_carbon/sum_invoke, sum_carbon_oracle/sum_invoke, sum_carbon_perf/sum_invoke, sum_carbon_eco/sum_invoke)

    carbon_opt_percent = [100*((sum_st_carbon/sum_invoke)-min_st)/min_st+y_move,100*(sum_carbon_carbon/sum_invoke-min_carbon)/min_carbon]
    oracle_percent = [100*(sum_st_oracle/sum_invoke-min_st)/min_st+y_move,100*(sum_carbon_oracle/sum_invoke-min_carbon)/min_carbon+x_move]
    perf_opt_percent =[100*(sum_st_perf/sum_invoke-min_st)/min_st+3.3,100*(sum_carbon_perf/sum_invoke-min_carbon)/min_carbon+x_move]
    eco_percent = [100*(sum_st_eco/sum_invoke-min_st)/min_st,100*(sum_carbon_eco/sum_invoke-min_carbon)/min_carbon+x_move]

    x = [carbon_opt_percent[1],oracle_percent[1],perf_opt_percent[1],eco_percent[1]]
    y = [carbon_opt_percent[0],oracle_percent[0],perf_opt_percent[0],eco_percent[0]]

    axs.set_xlabel(XLABEL,fontsize=FONTSIZE)
    axs.set_ylabel(YLABEL,fontsize=FONTSIZE)
    axs.tick_params(axis='both', which='major', pad=1, labelsize=FONTSIZE)
    axs.grid(which='both', color='lightgrey', ls='dashed', zorder=0)
    colors = ['#7fc97f','#DAA520','#beaed4','#17becf']

    markers = ['v', 'X', 's','P']
    LABELS = ['CO$_2$-Opt','Oracle','Service-Time-Opt','Eco-Life']
    for i in range(len(x)):
        axs.scatter(x=x[i], y=y[i], color=colors[i], label=LABELS[i], s=200, zorder=3, alpha=1, edgecolors="black", marker=markers[i])

    axs.legend(loc=(-0.18,1.03), frameon = False ,ncol=5,labels=LABELS,fontsize=13,columnspacing=0.4,handletextpad =0.2)
    axs.yaxis.set_major_formatter(mtick.FormatStrFormatter('%i'))
    axs.set_ylim(ymin=0,ymax=55)
    axs.set_xlim(xmin=0,xmax=50)
    plt.savefig("result.pdf",bbox_inches='tight')
    

if __name__ == "__main__":
    fire.Fire(verify)
