from beluga_goal import is_goal_state, check_goal_progress
from beluga_utils import print_state, action_to_string

def simulate_plan(initial_state, plan, instance_data):
    """
    Simulate executing a plan to verify it reaches the goal.
    Returns (success, final_state, failed_action)
    """
    current_state = initial_state
    
    print("Starting plan simulation...")
    print_state(current_state, instance_data)
    
    for i, action in enumerate(plan):
        print(f"\nStep {i+1}: {action_to_string(action)}")
        
        # Check if action is valid
        if not current_state.is_valid_action(action, instance_data):
            print(f"ERROR: Action is not valid in current state!")
            return False, current_state, action
        
        # Apply action
        next_state = current_state.get_next_state(action, instance_data)
        if next_state is None:
            print(f"ERROR: Action failed to produce a valid next state!")
            return False, current_state, action
        
        current_state = next_state
        print_state(current_state, instance_data)
    
    # Check if the final state is a goal state
    if is_goal_state(current_state, instance_data):
        print("\nPlan successfully reaches the goal!")
        return True, current_state, None
    else:
        print("\nPlan does not reach the goal!")
        progress = check_goal_progress(current_state, instance_data)
        print(f"Progress: Flights: {progress['flights_progress']}, Parts: {progress['parts_progress']}")
        return False, current_state, None