import subprocess
import time
import os
import json
from datetime import datetime

# Define improved experiment configurations
improved_experiments = [
    {
        "name": "Extended Baseline",
        "heuristic": "standard",
        "prioritize_actions": False,
        "max_iterations": 30000,
        "time_limit": 300  # 5 minutes
    },
    {
        "name": "Extended Weighted",
        "heuristic": "weighted",
        "prioritize_actions": False,
        "max_iterations": 30000,
        "time_limit": 300
    },
    {
        "name": "Enhanced Action Priority",
        "heuristic": "weighted",
        "prioritize_actions": True,
        "max_iterations": 30000,
        "time_limit": 300
    }
]

# Define the instance file to use
instance_file = "problem_4_s46_j23_r2_oc51_f6.json"

# Create results directory
results_dir = "improved_experiment_results"
os.makedirs(results_dir, exist_ok=True)

# Create a timestamp for this experiment run
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
run_dir = os.path.join(results_dir, f"run_{timestamp}")
os.makedirs(run_dir, exist_ok=True)

# Create a summary file
summary_file = os.path.join(run_dir, "summary.csv")
with open(summary_file, "w") as f:
    f.write("Experiment,Heuristic,Prioritize,Iterations,Success,PlanLength,SearchTime,TotalTime\n")

# Run each experiment
for exp in improved_experiments:
    print(f"\n\n{'='*80}")
    print(f"Running improved experiment: {exp['name']}")
    print(f"{'='*80}\n")
    
    # Create output directory for this experiment
    exp_dir = os.path.join(run_dir, exp['name'].replace(" ", "_"))
    os.makedirs(exp_dir, exist_ok=True)
    
    # Create command
    cmd = [
        "python", "run_beluga_solver.py",
        instance_file,
        "--max-iterations", str(exp["max_iterations"]),
        "--time-limit", str(exp["time_limit"]),
        "--heuristic", exp["heuristic"],
        "--output", os.path.join(exp_dir, "plan.txt")
    ]
    
    if exp["prioritize_actions"]:
        cmd.append("--prioritize-actions")
    
    # Log file
    log_file = os.path.join(exp_dir, "log.txt")
    
    # Run the experiment
    start_time = time.time()
    with open(log_file, "w") as f:
        process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        
        # Stream output to both console and file
        for line in process.stdout:
            print(line, end="")
            f.write(line)
    
    process.wait()
    total_time = time.time() - start_time
    
    # Extract results
    success = False
    iterations = exp["max_iterations"]  # Default if not found
    plan_length = 0
    search_time = 0.0
    
    with open(log_file, "r") as f:
        log_content = f.read()
        if "Goal reached after" in log_content:
            success = True
            # Extract iterations
            for line in log_content.split("\n"):
                if "Goal reached after" in line:
                    iterations = int(line.split("Goal reached after")[1].split(" iterations")[0].strip())
                if "Plan length:" in line:
                    plan_length = int(line.split("Plan length:")[1].strip())
                if "A* search completed in" in line:
                    search_time = float(line.split("A* search completed in")[1].split(" seconds")[0].strip())
    
    # Track progress differently - extract max flight and part progress
    max_flights = 0
    max_parts = 0
    for line in log_content.split("\n"):
        if "Flights:" in line and "Parts:" in line:
            try:
                flights_str = line.split("Flights:")[1].split(",")[0].strip()
                flights = int(flights_str.split("/")[0])
                
                parts_str = line.split("Parts:")[1].strip()
                parts = int(parts_str.split("/")[0])
                
                max_flights = max(max_flights, flights)
                max_parts = max(max_parts, parts)
            except:
                pass
    
    # Write results to summary
    with open(summary_file, "a") as f:
        f.write(f"{exp['name']},{exp['heuristic']},{exp['prioritize_actions']},{iterations},{success},{plan_length},{search_time},{total_time}\n")
    
    # Save experiment metadata
    with open(os.path.join(exp_dir, "metadata.json"), "w") as f:
        json.dump({
            "name": exp["name"],
            "heuristic": exp["heuristic"],
            "prioritize_actions": exp["prioritize_actions"],
            "max_iterations": exp["max_iterations"],
            "time_limit": exp["time_limit"],
            "success": success,
            "iterations": iterations,
            "plan_length": plan_length,
            "search_time": search_time,
            "total_time": total_time,
            "max_flights_reached": max_flights,
            "max_parts_produced": max_parts
        }, f, indent=2)

    # Track progress over time
    progress_data = []
    current_iteration = 0
    for line in log_content.split("\n"):
        if "Iteration" in line and "Flights:" in line and "Parts:" in line:
            try:
                iteration_str = line.split("Iteration")[1].split(":")[0].strip()
                current_iteration = int(iteration_str)
                
                flights_str = line.split("Flights:")[1].split(",")[0].strip()
                flights = int(flights_str.split("/")[0])
                
                parts_str = line.split("Parts:")[1].strip()
                parts = int(parts_str.split("/")[0])
                
                progress_data.append({
                    "iteration": current_iteration,
                    "flights": flights,
                    "parts": parts
                })
            except:
                pass
    
    # Save progress data
    with open(os.path.join(exp_dir, "progress_data.json"), "w") as f:
        json.dump(progress_data, f, indent=2)

print("\n\nAll improved experiments completed!")
print(f"Results available in: {run_dir}")