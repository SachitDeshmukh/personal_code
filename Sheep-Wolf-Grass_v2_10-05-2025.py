import pandas as pd
import os
import logging
from datetime import datetime
from itertools import product
from joblib import Parallel, delayed
from pynetlogo import NetLogoLink
import jpype

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Parameter definitions
INPUT_PARAMS = {
    "initial-number-sheep": [50, 100, 200],
    "initial-number-wolves": [50, 100, 200],
    "grass-regrowth-time": [25, 50],
    "sheep-gain-from-food": [10, 25],
    "wolf-gain-from-food": [20, 100],
    "sheep-reproduce": [5, 20],
    "wolf-reproduce": [5, 10],
    "max-sheep": [30000]
}

def generate_param_combinations():
    """Generate all possible parameter combinations."""
    return [dict(zip(INPUT_PARAMS.keys(), values)) for values in product(*INPUT_PARAMS.values())]

def run_simulation(params, iter):
    """Run a single simulation using the pre-initialized NetLogo instance."""
    netlogo_instance = NetLogoLink(gui=False, netlogo_home=r"C:\Users\Sachit Deshmukh\AppData\Local\NetLogo")
    netlogo_instance.load_model(r"C:\Users\Sachit Deshmukh\Documents\Python Scripts\Net-Logo_Wolf-Sheep-Grass.nlogo")

    try:
        for param, value in params.items():
            netlogo_instance.command(f"set {param} {value}")

        netlogo_instance.command("setup")

        while (netlogo_instance.report("ticks") < 300) and (netlogo_instance.report("count sheep") > 0 or netlogo_instance.report("count wolves") > 0):
            netlogo_instance.repeat_command("go", 10)

        results = {
            "Iternation": iter+1,
            "sheep_start": params.get("initial-number-sheep"),
            "wolf_start": params.get("initial-number-wolves"),
            "grass_regrowth": params.get("grass-regrowth-time"),
            "sheep_gain": params.get("sheep-gain-from-food"),
            "wolf_gain": params.get("wolf-gain-from-food"),
            "sheep-reproduce": params.get("sheep-reproduce"),
            "wolf-reproduce": params.get("wolf-reproduce"),
            "sheep_count": netlogo_instance.report("count sheep"),
            "wolves_count": netlogo_instance.report("count wolves"),
            "grass_count": netlogo_instance.report("ifelse-value model-version = \"sheep-wolves-grass\" [count patches with [pcolor = green]] [0]"),
            "run_ticks": netlogo_instance.report("ticks")
        }
        
        logging.info(f"Iter: {iter+1} | Sheep: {results['sheep_count']}, Wolves: {results['wolves_count']}, Grass: {results['grass_count']} | Ticks: {results['run_ticks']}")
    
    except Exception as e:
        logging.error(f"Simulation error with params {params}: {e}")
        return None # Ensure failed runs don’t corrupt output
    
    finally:
        netlogo_instance.kill_workspace()
    
    return results

def main():
    os.chdir(r"C:\Users\Sachit Deshmukh\Documents\Python Scripts")

    """Execute all simulations in parallel."""
    param_combos = list(generate_param_combinations())
    num_runs = 10

    if not jpype.isJVMStarted():
        jpype.startJVM()
        print("JVM started successfully!")

    start_time_temp = datetime.now()
    results = Parallel(n_jobs=6, backend="multiprocessing")(
        delayed(run_simulation)(combo, x) for combo in param_combos for x in range(num_runs)
    )
    end_time_temp = datetime.now()
    
    # Filter out None values (failed runs)
    results = [res for res in results if res is not None]

    # Save results
    output_data = pd.DataFrame(results)
    output_data.to_csv("temp_output.csv")

    xlsx_file_name = f"NETLOGO-Trial_Sheep_{datetime.now().strftime("%Y-%m-%d")}.xlsx"

    if os.path.exists(xlsx_file_name):
    # Append to existing file
        with pd.ExcelWriter(xlsx_file_name, mode='a', engine='openpyxl') as writer:
            output_data.to_excel(writer, sheet_name=datetime.now().strftime("%H-%M-%S"), index=False)
    else:
        # Create a new file
        with pd.ExcelWriter(xlsx_file_name, mode='w', engine='openpyxl') as writer:
            output_data.to_excel(writer, sheet_name=datetime.now().strftime("%H-%M-%S"), index=False)

    logging.info(f"All simulations complete. Results saved to {xlsx_file_name}")

    total_time = (end_time_temp - start_time_temp).total_seconds()
    print(f"Total time taken: {total_time}.")

if __name__ == "__main__":
    main()
