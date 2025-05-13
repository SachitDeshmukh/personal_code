import pandas as pd
import os
import logging
import time
import jpype
from datetime import datetime
from itertools import product
from joblib import Parallel, delayed
from joblib.externals.loky import get_reusable_executor
from pynetlogo import NetLogoLink

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Parameter definitions
INPUT_PARAMS = {
    "initial-number-sheep": [50, 75, 150, 200],
    "initial-number-wolves": [100, 150],
    "grass-regrowth-time": [50,75],
    "sheep-gain-from-food": [10, 15],
    "wolf-gain-from-food": [20, 25, 50],
    "sheep-reproduce": [5, 10, 20],
    "wolf-reproduce": [5, 10, 15],
    "max-sheep": [30000]
}

def rest():
    time.sleep(3)

def gen_param_combos():
    return [dict(zip(INPUT_PARAMS.keys(), values)) for values in product(*INPUT_PARAMS.values())]

def save_data(data, backup_file_name):
    #data = pd.DataFrame(data)
    data.to_csv(f"{backup_file_name}.csv")

    xlsx_file_name = f"NETLOGO_Sheep-Stable_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    mode = 'a' if os.path.exists(xlsx_file_name) else 'w'
    with pd.ExcelWriter(xlsx_file_name, mode=mode, engine='openpyxl') as writer:
        data.to_excel(writer, sheet_name=datetime.now().strftime("%H-%M-%S"), index=False)

    logging.info(f"A round of simulations complete. Results saved to {xlsx_file_name}")

class NetLogoSim:
    def __init__(self, parameters, runs, ticks, stable_min=0.70):
        self.params = parameters
        #self.param_count = len(parameters)
        self.runs = runs
        self.ticks = ticks
        self.stable_min = stable_min

    def params_stability(self, combo, iter):
        netlogo = NetLogoLink(gui=False, netlogo_home=r"C:\Users\Sachit Deshmukh\AppData\Local\NetLogo")
        netlogo.load_model(r"C:\Users\Sachit Deshmukh\Documents\Python Scripts\Net-Logo_Wolf-Sheep-Grass.nlogo")

        try:
            for param, value in combo.items():
                netlogo.command(f"set {param} {value}")

            netlogo.command("setup")

            while netlogo.report("ticks") < self.ticks and netlogo.report("count sheep") > 0 and netlogo.report("count wolves") > 0:
                netlogo.repeat_command("go", self.ticks)

            stability = netlogo.report("count sheep") > 0 and netlogo.report("count wolves") > 0
            results = {
                "Combo": self.params.index(combo),
                "Iternation": iter+1,
                "Params": combo,
                "Stability": stability,
            }
            
            logging.info(f"Combination {self.params.index(combo)} iteration {iter+1}: {stability}")
        
        except Exception as e:
            logging.error(f"Simulation error with params {combo}: {e}")
            return None # Ensure failed runs don’t corrupt output
        
        finally:
            netlogo.kill_workspace()

        return results

    def filter_params(self, results):
        results = [res for res in results if res is not None]
        result_data = pd.DataFrame(results)
        probabilities = result_data.groupby("Combo")["Stability"].mean().reset_index()
        probabilities.rename(columns={"Stability": "Stability_Prob"}, inplace=True)
        result_data = result_data.merge(probabilities, on="Combo")
        result_data = result_data.groupby("Combo").first().reset_index()
        filtered_data = result_data[result_data["Stability_Prob"] > self.stable_min]
        filtered_params = list(filtered_data["Params"])
        return filtered_params, result_data
    
def main():
    os.chdir(r"C:\Users\Sachit Deshmukh\Documents\Python Scripts")

    if not jpype.isJVMStarted():
        jpype.startJVM()    

    param_combinations = gen_param_combos()

    try:
        for round_num, ticks in enumerate([1500, 3000, 10000], start=1):
            logging.info(f"Starting iteration round {round_num}...")
            start_time_temp = datetime.now()
            simulation = NetLogoSim(param_combinations, runs=5, ticks=ticks)
            iter_data = Parallel(n_jobs=6, backend="multiprocessing")(
                delayed(simulation.params_stability)(combo, x) for combo in simulation.params for x in range(simulation.runs)
            )
            filtered_params, prob_results = simulation.filter_params(iter_data)
            end_time_temp = datetime.now()
            total_time = (end_time_temp - start_time_temp).total_seconds()
            logging.info(f"Time taken for round {round_num}: {total_time}.")
            
            save_data(prob_results, backup_file_name=f"Round_{round_num}_output")
            logging.info(f"Round {round_num} complete.")

            if not filtered_params:
                logging.warning(f"All parameter sets unstable after round {round_num}, stopping further iterations.")
                break

            param_combinations = filtered_params  # Feed filtered params into next round
            time.sleep(3)

    finally:
        logging.info("CLEANING UP RESOURCES...")
        jpype.shutdownJVM()

    logging.info("ALL SIMULATIONS COMPLETE.")

if __name__ == "__main__":
    main()
