# IMPORTING ALL NECESSARY LIBRARIES
import pynetlogo as sim
import pandas as pd
#import numpy as np
import os
from datetime import datetime
from itertools import product

os.chdir(r"C:\Users\Sachit Deshmukh\Documents\Python Scripts")
# INITIALIZE AND LOADING NETLOGO MODEL IN HEADLESS MODE (WITHOUT THE GRAPHICAL INTERFACE)
simulation = sim.NetLogoLink(gui=False, netlogo_home=r"C:\Users\Sachit Deshmukh\AppData\Local\NetLogo", jvmargs = ["-Xmx2048m"])

input_params_grid = {
    "initial-number-sheep": [50, 100, 200],             # Initial number of sheep
    "initial-number-wolves": [50, 100, 200],             # Initial number of wolves
    "grass-regrowth-time": [25, 50],               # Grass regrowth time
    "sheep-gain-from-food": [10, 25],               # Sheep gain from food
    "wolf-gain-from-food": [20, 100],               # Wolf gain from food
    "sheep-reproduce": [5,20],                    # Sheep reproduction rate
    "wolf-reproduce": [5, 10],                     # Wolf reproduction rate
    "max-sheep": [30000]                       # Maximum sheep population
}

param_combinations = list(product(*input_params_grid.values()))
total_combos = len(param_combinations)
input_keys = list(input_params_grid.keys())

# RUNNING THE MODEL
output_values_long = []
num_runs = 10
combination = 1
num_ticks = 100 # number of ticks to run each time before collecting data

for param_combo in param_combinations:
    simulation.load_model(r"Net-Logo_Wolf-Sheep-Grass.nlogo")
    current_param = dict(zip(input_keys, param_combo))

    for run in range(num_runs):
        start_time_temp = datetime.now()
        # SET PARAMETERS IN THE MODEL
        for param, value in current_param.items():
            simulation.command(f"set {param} {value}")
        simulation.command("setup")

        while (simulation.report("ticks") < num_ticks) and (simulation.report("count sheep") > 0 or simulation.report("count wolves") > 0):
            try:
                simulation.repeat_command("go", total_combos)
            except Exception as e:
                print(f"Run failed at Serial {combination} Iter {run + 1} Tick {simulation.report("ticks")}: {e}")
        
        # EXTRACT OUTPUT VALUES
        sheep_count = simulation.report("count sheep")
        wolves_count = simulation.report("count wolves")
        grass_count = simulation.report("ifelse-value model-version = \"sheep-wolves-grass\" [ count patches with [pcolor = green] ] [ 0 ]")

        end_time_temp = datetime.now()
        time_taken = (end_time_temp - start_time_temp).total_seconds()
        
        # STORING OUTPUT VALUES
        output_values_long.append({
            "combination": combination,
            "sheep_start": current_param.get("initial-number-sheep"),
            "wolf_start": current_param.get("initial-number-wolves"),
            "grass_regrowth": current_param.get("grass-regrowth-time"),
            "sheep_gain": current_param.get("sheep-gain-from-food"),
            "wolf_gain": current_param.get("wolf-gain-from-food"),
            "sheep-reproduce": current_param.get("sheep-reproduce"),
            "wolf-reproduce": current_param.get("wolf-reproduce"),
            "run_ticks": simulation.report("ticks"),
            "iteration": run + 1,
            "time_taken": time_taken,
            "sheep_count": sheep_count,
            "wolves_count": wolves_count,
            "grass_count": grass_count
        })
        print(f"Combo: {combination} - Iter {run + 1} data: Sheep: {sheep_count}, Wolves: {wolves_count}, Grass: {grass_count}; Time taken:{time_taken}")
        simulation.command("clear-all")
    combination +=1
    simulation.kill_workspace()

# CONVERTING DATA INTO DATAFRAME
output_data = pd.DataFrame(output_values_long)
output_data.to_csv("temp_output.csv")

# SAVE DATA TO A EXCEL FILE
today_w_time = datetime.now()
current_date = str(datetime.date(today_w_time))
current_time = f"{today_w_time.hour}Hr_{today_w_time.minute}Mn_{today_w_time.second}Se"

xlsx_file_name = f"NETLOGO-Trial_Sheep_{current_date}_v2.xlsx"

if os.path.exists(xlsx_file_name):
    # Append to existing file
    with pd.ExcelWriter(xlsx_file_name, mode='a', engine='openpyxl') as writer:
        output_data.to_excel(writer, sheet_name=current_time, index=False)
else:
    # Create a new file
    with pd.ExcelWriter(xlsx_file_name, mode='w', engine='openpyxl') as writer:
        output_data.to_excel(writer, sheet_name=current_time, index=False)

print("Simulation complete. Results saved.")