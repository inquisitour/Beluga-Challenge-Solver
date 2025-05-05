"""
Script to run experiments with the hybrid A* + CSP approach.
"""

import subprocess
import time
import os
import json
from datetime import datetime

from beluga_loader import load_instance
from beluga_state import create_initial_state
from beluga_hybrid_solver import hybrid_astar_search
from beluga_verification import simulate_plan
from beluga_utils import print_plan, print_state
from beluga_goal import detailed_goal_check

# Define experiment configurations
hybrid_experiments = [
    {
        "name": "Hybrid_A_with_Forward_Checking",
        "heuristic": "weighted",
        "prioritize_actions": True,
        "use_forward_checking": True,
        "use_random_restarts": False,
        "max_iterations": 20000,
        "time_limit": 240  # 4 minutes
    },
    {
        "name": "Hybrid_A_with_Random_Restarts",
        "heuristic": "weighted",
        "prioritize_actions": True,
        "use_forward_checking": False,
        "use_random_restarts": True,
        "max_iterations": 20000,
        "time_limit": 240
    },
    {
        "name": "Full_Hybrid_A",
        "heuristic": "weighted",
        "prioritize_actions": True,
        "use_forward_checking": True,
        "use_random_restarts": True,
        "max_iterations": 20000,
        "time_limit": 240
    }
]

# Define the instance file to use
instance_file = "problem_4_s46_j23_r2_oc51_f6.json"

def save_plan_to_file(plan, instance_data, filename):
    """Save the plan to a file in a readable format."""
    from beluga_utils import action_to_string
    
    with open(filename, 'w') as f:
        f.write(f"Plan with {len(plan)} steps:\n")
        for i, action in enumerate(plan):
            f.write(f"Step {i+1}: {action_to_string(action)}\n")

def run_experiment(exp, instance_file, results_dir):
    """Run a single experiment and return results."""
    print(f"\n\n{'='*80}")
    print(f"Running hybrid experiment: {exp['name']}")
    print(f"{'='*80}\n")
    
    # Create output directory for this experiment
    exp_dir = os.path.join(results_dir, exp['name'].replace(" ", "_"))
    os.makedirs(exp_dir, exist_ok=True)
    
    # Load instance
    start_time = time.time()
    instance_data = load_instance(instance_file)
    print(f"Instance loaded in {time.time() - start_time:.2f} seconds")
    
    # Create initial state
    initial_state = create_initial_state(instance_data)
    print("Initial state created")
    
    # Run the hybrid A* search
    print(f"Running hybrid A* search with heuristic '{exp['heuristic']}' " + 
          f"(max iterations: {exp['max_iterations']}, time limit: {exp['time_limit']}s)...")
    
    search_start_time = time.time()
    plan = hybrid_astar_search(
        initial_state, instance_data, 
        max_iterations=exp["max_iterations"],
        time_limit=exp["time_limit"],
        heuristic_variant=exp["heuristic"],
        prioritize_actions=exp["prioritize_actions"],
        use_forward_checking=exp["use_forward_checking"],
        use_random_restarts=exp["use_random_restarts"]
    )
    search_time = time.time() - search_start_time
    total_time = time.time() - start_time
    
    print(f"Hybrid A* search completed in {search_time:.2f} seconds")
    
    # Log file
    log_file = os.path.join(exp_dir, "log.txt")
    with open(log_file, "w") as f:
        f.write(f"Experiment: {exp['name']}\n")
        f.write(f"Heuristic: {exp['heuristic']}\n")
        f.write(f"Prioritize Actions: {exp['prioritize_actions']}\n")
        f.write(f"Forward Checking: {exp['use_forward_checking']}\n")
        f.write(f"Random Restarts: {exp['use_random_restarts']}\n")
        f.write(f"Max Iterations: {exp['max_iterations']}\n")
        f.write(f"Time Limit: {exp['time_limit']} seconds\n\n")
        
        f.write(f"Search time: {search_time:.2f} seconds\n")
        f.write(f"Total time: {total_time:.2f} seconds\n\n")
        
        if plan:
            f.write(f"Found plan with {len(plan)} steps.\n")
            for i, action in enumerate(plan):
                from beluga_utils import action_to_string
                f.write(f"Step {i+1}: {action_to_string(action)}\n")
        else:
            f.write("No plan found.\n")
    
    # Print and save plan
    success = False
    max_flights_reached = 0
    max_parts_produced = 0
    plan_length = 0
    
    if plan:
        print_plan(plan, instance_data)
        plan_length = len(plan)
        print(f"Plan length: {plan_length}")
        
        # Save plan to file
        plan_file = os.path.join(exp_dir, "plan.txt")
        save_plan_to_file(plan, instance_data, plan_file)
        print(f"Plan saved to {plan_file}")
        
        # Verify plan
        print("\nVerifying plan...")
        success, final_state, failed_action = simulate_plan(initial_state, plan, instance_data)
        
        if success:
            print("\nPlan verification successful!")
            
            # Perform detailed goal check
            goal_check = detailed_goal_check(final_state, instance_data)
            max_flights_reached = goal_check['current_flight']
            max_parts_produced = goal_check['production_status']['produced_parts']
        else:
            print("\nPlan verification failed!")
            if failed_action:
                print(f"Failed at action: {failed_action}")
            
            # Check current progress
            goal_check = detailed_goal_check(final_state, instance_data)
            max_flights_reached = goal_check['current_flight']
            max_parts_produced = goal_check['production_status']['produced_parts']
    else:
        print("No plan found!")
        
        # Estimate progress from the log file
        with open(log_file, "r") as f:
            log_content = f.read()
            
            # Find maximum flights and parts reached from the log
            for line in log_content.split("\n"):
                if "Flights:" in line and "Parts:" in line:
                    try:
                        flights_str = line.split("Flights:")[1].split(",")[0].strip()
                        flights = int(flights_str.split("/")[0])
                        
                        parts_str = line.split("Parts:")[1].strip()
                        parts = int(parts_str.split("/")[0])
                        
                        max_flights_reached = max(max_flights_reached, flights)
                        max_parts_produced = max(max_parts_produced, parts)
                    except:
                        pass
    
    # Save experiment metadata
    metadata = {
        "name": exp["name"],
        "heuristic": exp["heuristic"],
        "prioritize_actions": exp["prioritize_actions"],
        "use_forward_checking": exp["use_forward_checking"],
        "use_random_restarts": exp["use_random_restarts"],
        "max_iterations": exp["max_iterations"],
        "time_limit": exp["time_limit"],
        "success": success,
        "plan_length": plan_length,
        "search_time": search_time,
        "total_time": total_time,
        "max_flights_reached": max_flights_reached,
        "max_parts_produced": max_parts_produced
    }
    
    with open(os.path.join(exp_dir, "metadata.json"), "w") as f:
        json.dump(metadata, f, indent=2)
    
    return {
        "name": exp["name"],
        "success": success,
        "iterations": exp["max_iterations"] if not success else plan_length,
        "plan_length": plan_length,
        "search_time": search_time,
        "total_time": total_time,
        "max_flights_reached": max_flights_reached,
        "max_parts_produced": max_parts_produced
    }

def main():
    # Create results directory
    results_dir = "hybrid_experiment_results"
    os.makedirs(results_dir, exist_ok=True)
    
    # Create a timestamp for this experiment run
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_dir = os.path.join(results_dir, f"run_{timestamp}")
    os.makedirs(run_dir, exist_ok=True)
    
    # Create a summary file
    summary_file = os.path.join(run_dir, "summary.csv")
    with open(summary_file, "w") as f:
        f.write("Experiment,Heuristic,Prioritize,ForwardChecking,RandomRestarts,Success,Iterations,PlanLength,SearchTime,TotalTime,MaxFlights,MaxParts\n")
    
    # Run each experiment
    results = []
    for exp in hybrid_experiments:
        result = run_experiment(exp, instance_file, run_dir)
        results.append(result)
        
        # Update summary file
        with open(summary_file, "a") as f:
            f.write(f"{exp['name']},{exp['heuristic']},{exp['prioritize_actions']},{exp['use_forward_checking']},{exp['use_random_restarts']},{result['success']},{result['iterations']},{result['plan_length']},{result['search_time']},{result['total_time']},{result['max_flights_reached']},{result['max_parts_produced']}\n")
    
    print("\n\nAll hybrid experiments completed!")
    print(f"Results available in: {run_dir}")

if __name__ == "__main__":
    main()