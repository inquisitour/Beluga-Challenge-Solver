def debug_action_generation(state, instance_data):
    """Debug the action generation function."""
    from beluga_astar import get_all_possible_actions
    
    print("\nDebugging action generation...")
    print("Current state:")
    from beluga_utils import print_state
    print_state(state, instance_data)
    
    actions = get_all_possible_actions(state, instance_data)
    print(f"\nGenerated {len(actions)} possible actions:")
    
    # Group actions by type
    action_types = {}
    for action in actions:
        action_type = action.__class__.__name__
        if action_type not in action_types:
            action_types[action_type] = []
        action_types[action_type].append(action)
    
    # Print actions by type
    for action_type, type_actions in action_types.items():
        print(f"\n{action_type} ({len(type_actions)} actions):")
        for i, action in enumerate(type_actions[:5]):  # Print first 5 of each type
            from beluga_utils import action_to_string
            print(f"  {i+1}. {action_to_string(action)}")
        
        if len(type_actions) > 5:
            print(f"  ... and {len(type_actions) - 5} more")
    
    return actions

def debug_heuristic(state, instance_data):
    """Debug the heuristic function."""
    from beluga_heuristic import heuristic
    
    print("\nDebugging heuristic function...")
    print("Current state:")
    from beluga_utils import print_state
    print_state(state, instance_data)
    
    h_value = heuristic(state, instance_data)
    print(f"Heuristic value: {h_value}")
    
    # Break down the heuristic calculation
    flights = instance_data.get('flights', [])
    flights_remaining = max(0, len(flights) - state.current_flight_idx - 1)
    
    # Collect production schedule
    production_schedule = []
    for line in instance_data.get('production_lines', []):
        production_schedule.extend(line.get('schedule', []))
    
    # Count parts to produce
    parts_to_produce = []
    for jig_id in production_schedule:
        loaded, part_id = state.jig_status.get(jig_id, (False, ""))
        if loaded and part_id and part_id not in state.produced_parts:
            parts_to_produce.append(part_id)
    
    # Count outgoing jigs
    total_outgoing_jigs = 0
    for i in range(state.current_flight_idx, len(flights)):
        total_outgoing_jigs += len(flights[i].get('outgoing', []))
    
    # Count blocked jigs
    blocked_jigs = 0
    for rack_id, jigs in state.rack_jigs.items():
        for i, jig_id in enumerate(jigs):
            if i > 0 and i < len(jigs) - 1 and jig_id in production_schedule:
                blocked_jigs += 1
    
    print("Heuristic breakdown:")
    print(f"  Flights remaining: {flights_remaining}")
    print(f"  Parts to produce: {len(parts_to_produce)}")
    print(f"  Outgoing jigs: {total_outgoing_jigs}")
    print(f"  Blocked jigs: {blocked_jigs}")
    
    return h_value

def run_debug_session(instance_file):
    """Run a debugging session on the given instance."""
    from beluga_loader import load_instance
    from beluga_state import create_initial_state
    
    print(f"Running debug session on instance: {instance_file}")
    
    # Load instance
    instance_data = load_instance(instance_file)
    
    # Create initial state
    initial_state = create_initial_state(instance_data)
    
    # Debug action generation
    actions = debug_action_generation(initial_state, instance_data)
    
    # Debug heuristic
    h_value = debug_heuristic(initial_state, instance_data)
    
    # Test applying some actions
    if actions:
        print("\nTesting action application:")
        for i, action in enumerate(actions[:3]):  # Test first 3 actions
            from beluga_utils import action_to_string
            print(f"\nApplying action: {action_to_string(action)}")
            
            next_state = initial_state.get_next_state(action, instance_data)
            if next_state:
                print("Action applied successfully!")
                from beluga_utils import print_state
                print_state(next_state, instance_data)
                
                # Debug heuristic on new state
                new_h = debug_heuristic(next_state, instance_data)
                print(f"Heuristic change: {h_value} -> {new_h} (diff: {new_h - h_value})")
            else:
                print("Action failed to generate a valid next state!")
    
    print("\nDebug session completed!")

if __name__ == "__main__":
    # Run debug session on the small instance
    run_debug_session("problem_4_s46_j23_r2_oc51_f6.json")