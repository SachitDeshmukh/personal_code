import os  # Importing OS module for file operations
import pandas as pd  # Import Pandas for data processing
import logging  # Logging setup for monitoring execution
import time  # Time module for delays
import jpype  # Interface for Java-Python interactions
from datetime import datetime  # Date/time handling utilities
from itertools import product  # Cartesian product for param combinations
from joblib import Parallel, delayed  # Parallel execution for simulations
from pynetlogo import NetLogoLink  # Interface for NetLogo simulations
import matplotlib.pyplot as plt  # Plotting graphs with Matplotlib
import seaborn as sns  # Enhanced visualization with Seaborn

# Set logging format and level
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Function to introduce a delay
def rest():
    time.sleep(3)

# Generate all possible parameter combinations
def gen_param_combos(all_params):
    return [dict(zip(all_params.keys(), values)) for values in product(*all_params.values())]

# Save simulation data in CSV and Excel formats
def save_data(data, backup_file_name):
    data.to_csv(f"{backup_file_name}.csv")

    xlsx_file_name = f"NETLOGO_Fire-Perc_{datetime.now().strftime('%Y-%m-%d')}.xlsx"

    mode = 'a' if os.path.exists(xlsx_file_name) else 'w'
    with pd.ExcelWriter(xlsx_file_name, mode=mode, engine='openpyxl') as writer:
        data.to_excel(writer, sheet_name=datetime.now().strftime("%H-%M-%S"), index=False)

    logging.info(f"Simulations complete. Results saved to {xlsx_file_name}")

# Generate scatter plot for results visualization
def gen_graph(X_data, Y_data_1, Y_data_2):
    png_file_name = f"NETLOGO_Fire-Perc_{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}.png"
    plt.figure(figsize=(12, 6))
    sns.scatterplot(x=X_data, y=Y_data_1, hue=Y_data_1, marker="o")
    sns.scatterplot(x=X_data, y=Y_data_2, color="black", marker="X")
    plt.xticks(X_data)
    plt.xlabel("DENSITY OF TREES")
    plt.ylabel("PERCENTAGE OF TREES BURNED")
    plt.title("FUNCTION OF DENSITY OVER TREES BURNED")
    plt.legend(title="Percentage Burned")
    plt.savefig(png_file_name, dpi=300, bbox_inches='tight')
    plt.show()
    plt.pause(5)
    plt.close()
    logging.info(f"Scatter Plot generated. Graph file saved to {png_file_name}")

# NetLogo simulation class handling execution
class NetLogoSim:
    def __init__(self, parameters, runs):
        self.params = parameters  # Store parameter combinations
        self.runs = runs  # Define the number of simulation runs

    # Run simulation for a parameter combination
    def params_stability(self, combo, iter):
        netlogo = NetLogoLink(gui=False, netlogo_home=r"C:\Users\Sachit Deshmukh\AppData\Local\NetLogo")
        netlogo.load_model(r"C:\Users\Sachit Deshmukh\Documents\Python Scripts\Net-Logo_Fire_v2.nlogo")

        combo_serial = self.params.index(combo)
        try:
            for param, value in combo.items():
                netlogo.command(f"set {param} {value}")  # Set model parameters

            netlogo.command("setup")  # Initialize simulation

            while not netlogo.report("burned-trees") > 0 or (netlogo.report("count fires") > 0 and netlogo.report("count embers") > 0):
                netlogo.repeat_command("go", 500)  # Run simulation steps

            perc_burned = float((netlogo.report("burned-trees")/netlogo.report("initial-trees"))*100)

            results = {
                "Combo": combo_serial,
                "Iteration": iter+1,
                "Density": value,
                "Output": perc_burned
            }
            
            logging.info(f"Combination {combo_serial} iteration {iter+1}: {perc_burned}% burned")
        
        except Exception as e:
            logging.error(f"Simulation error with params {combo}: {e}")
            return None  # Ensure failed runs don’t corrupt output
        
        finally:
            netlogo.kill_workspace()  # Close NetLogo workspace

        return results

    # Filter valid results and compute averages
    def filter_params(self, results):
        results = [res for res in results if res is not None]
        result_data = pd.DataFrame(results)
        percentages = result_data.groupby("Combo")["Output"].mean().reset_index()
        percentages.rename(columns={"Output": "Avg_Perc_Burned"}, inplace=True)
        result_data = result_data.merge(percentages, on="Combo")
        result_data = result_data.sort_values(by="Density")
        return result_data

# Main execution function
def main():
    os.chdir(r"C:\Users\Sachit Deshmukh\Documents\Python Scripts")  # Change working directory

    if not jpype.isJVMStarted():
        jpype.startJVM()  # Start Java Virtual Machine

    try:
        logging.info(f"Starting iteration...")
        input_params = {
            "density": (list(range(50, 81)))  # Define density parameter range
        }
        param_combinations = gen_param_combos(input_params)
        start_time_temp = datetime.now()
        simulation = NetLogoSim(param_combinations, runs=20)  # Initialize simulation object
        iter_data = Parallel(n_jobs=6, backend="multiprocessing")(
            delayed(simulation.params_stability)(combo, x) for combo in simulation.params for x in range(simulation.runs)
        )  # Run simulations in parallel
        end_time_temp = datetime.now()
        time.sleep(3)
        total_time = (end_time_temp - start_time_temp).total_seconds()
        logging.info(f"Time taken: {total_time}.")

    finally:
        logging.info("CLEANING UP RESOURCES...")
        jpype.shutdownJVM()  # Shut down Java Virtual Machine

    logging.info("ALL SIMULATIONS COMPLETE.")

    perc_results = simulation.filter_params(iter_data)
    save_data(perc_results, backup_file_name="Iteration_output")
    density_data = perc_results["Density"]
    percentage_data = perc_results["Output"]
    avg_perc_data = perc_results["Avg_Perc_Burned"]
    gen_graph(density_data, percentage_data, avg_perc_data)  # Generate result graph

if __name__ == "__main__":
    main()  # Execute main function