import time
from beluga_loader import load_instance, extract_initial_state_data
from beluga_state import create_initial_state
from beluga_astar import astar_search
from beluga_verification import simulate_plan
from beluga_utils import print_plan, print_state
from beluga_goal import detailed_goal_check

def run_astar_test(instance_file, max_iterations=10000, time_limit=60):
    """
    Run A* search on the given instance file and test the resulting plan.
    """
    print(f"Testing A* search on instance: {instance_file}")
    
    # Load instance
    start_time = time.time()
    instance_data = load_instance(instance_file)
    print(f"Instance loaded in {time.time() - start_time:.2f} seconds")
    
    # Create initial state
    initial_state = create_initial_state(instance_data)
    print("Initial state created")
    
    # Run A* search
    print(f"Running A* search (max iterations: {max_iterations}, time limit: {time_limit}s)...")
    start_time = time.time()
    plan = astar_search(initial_state, instance_data, max_iterations, time_limit)
    search_time = time.time() - start_time
    print(f"A* search completed in {search_time:.2f} seconds")
    
    # Print plan
    if plan:
        print_plan(plan, instance_data)
        print(f"Plan length: {len(plan)}")
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
    # Run test on the small instance
    run_astar_test("problem_4_s46_j23_r2_oc51_f6.json", max_iterations=1000, time_limit=30)