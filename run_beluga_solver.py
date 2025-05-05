import argparse
import time
import os

from beluga_loader import load_instance
from beluga_state import create_initial_state
from beluga_astar import astar_search
from beluga_verification import simulate_plan
from beluga_utils import print_plan, print_state
from beluga_goal import detailed_goal_check
from beluga_debug import run_debug_session

def save_plan_to_file(plan, instance_data, filename):
    """Save the plan to a file in a readable format."""
    from beluga_utils import action_to_string
    
    with open(filename, 'w') as f:
        f.write(f"Plan with {len(plan)} steps:\n")
        for i, action in enumerate(plan):
            f.write(f"Step {i+1}: {action_to_string(action)}\n")

def main():
    parser = argparse.ArgumentParser(description='Beluga Solver using A* Search')
    parser.add_argument('instance_file', help='Path to the instance JSON file')
    parser.add_argument('--max-iterations', type=int, default=10000, help='Maximum iterations for A* search')
    parser.add_argument('--time-limit', type=int, default=60, help='Time limit in seconds for A* search')
    parser.add_argument('--debug', action='store_true', help='Run in debug mode')
    parser.add_argument('--output', help='Output file to save the plan')
    parser.add_argument('--heuristic', choices=['standard', 'weighted', 'production_focus'], 
                      default='standard', help='Heuristic variant to use')
    parser.add_argument('--prioritize-actions', action='store_true', 
                      help='Prioritize goal-relevant actions')
    args = parser.parse_args()
    
    # Check if file exists
    if not os.path.exists(args.instance_file):
        print(f"Error: Instance file '{args.instance_file}' not found!")
        return
    
    # Run in debug mode if requested
    if args.debug:
        run_debug_session(args.instance_file)
        return
    
    # Load instance
    start_time = time.time()
    instance_data = load_instance(args.instance_file)
    print(f"Instance loaded in {time.time() - start_time:.2f} seconds")
    
    # Create initial state
    initial_state = create_initial_state(instance_data)
    print("Initial state created")
    
    # Run A* search
    print(f"Running A* search with heuristic '{args.heuristic}' (max iterations: {args.max_iterations}, time limit: {args.time_limit}s)...")
    start_time = time.time()
    plan = astar_search(initial_state, instance_data, max_iterations=args.max_iterations, 
                       time_limit=args.time_limit, heuristic_variant=args.heuristic, 
                       prioritize_actions=args.prioritize_actions)
    search_time = time.time() - start_time
    print(f"A* search completed in {search_time:.2f} seconds")
    
    # Print and save plan
    if plan:
        print_plan(plan, instance_data)
        print(f"Plan length: {len(plan)}")
        
        if args.output:
            save_plan_to_file(plan, instance_data, args.output)
            print(f"Plan saved to {args.output}")
    else:
        print("No plan found!")
        return
    
    # Verify plan
    print("\nVerifying plan...")
    success, final_state, failed_action = simulate_plan(initial_state, plan, instance_data)
    
    if success:
        print("\nPlan verification successful!")
        
        # Perform detailed goal check
        goal_check = detailed_goal_check(final_state, instance_data)
        print("\nDetailed goal check:")
        print(f"  Flights processed: {goal_check['current_flight']}/{goal_check['total_flights']}")
        print(f"  Parts produced: {goal_check['production_status']['produced_parts']}/{goal_check['production_status']['total_parts']}")
        print(f"  Incoming jigs unloaded: {goal_check['flight_status']['incoming_processed']}/{goal_check['flight_status']['incoming_total']}")
        print(f"  Outgoing jigs loaded: {goal_check['flight_status']['outgoing_processed']}/{goal_check['flight_status']['outgoing_total']}")
        print(f"  Goal reached: {goal_check['goal_reached']}")
    else:
        print("\nPlan verification failed!")
        if failed_action:
            print(f"Failed at action: {failed_action}")
        
        # Check current progress
        goal_check = detailed_goal_check(final_state, instance_data)
        print("\nCurrent progress:")
        print(f"  Flights processed: {goal_check['current_flight']}/{goal_check['total_flights']}")
        print(f"  Parts produced: {goal_check['production_status']['produced_parts']}/{goal_check['production_status']['total_parts']}")
        print(f"  Incoming jigs unloaded: {goal_check['flight_status']['incoming_processed']}/{goal_check['flight_status']['incoming_total']}")
        print(f"  Outgoing jigs loaded: {goal_check['flight_status']['outgoing_processed']}/{goal_check['flight_status']['outgoing_total']}")

if __name__ == "__main__":
    main()