import json
from beluga_loader import load_instance, extract_initial_state_data
from beluga_state import BelugaState, create_initial_state
from beluga_actions import MoveJigBetweenRacks, LoadJigToBeluga, UnloadJigFromBeluga, SendJigToProduction, ReturnEmptyJigFromFactory, ProcessNextFlight

def test_loading():
    """Test loading the instance file."""
    print("Testing instance loading...")
    instance_data = load_instance("problem_4_s46_j23_r2_oc51_f6.json")
    print(f"Instance contains {len(instance_data.get('racks', []))} racks")
    print(f"Instance contains {len(instance_data.get('jigs', {}))} jigs")
    print(f"Instance contains {len(instance_data.get('flights', []))} flights")
    
    initial_data = extract_initial_state_data(instance_data)
    print("Initial data extracted successfully!")
    
    return instance_data, initial_data

def test_state_creation(instance_data):
    """Test creating the initial state."""
    print("\nTesting state creation...")
    initial_state = create_initial_state(instance_data)
    
    print(f"Initial state contains {len(initial_state.rack_jigs)} racks")
    for rack_id, jigs in initial_state.rack_jigs.items():
        print(f"  Rack {rack_id} contains {len(jigs)} jigs: {', '.join(jigs)}")
    
    print(f"Initial state tracks {len(initial_state.jig_status)} jigs")
    loaded_jigs = [jig_id for jig_id, (loaded, _) in initial_state.jig_status.items() if loaded]
    print(f"  {len(loaded_jigs)} jigs are loaded: {', '.join(loaded_jigs[:5])}...")
    
    print(f"Initial state has {len(initial_state.beluga_jigs)} jigs in Beluga")
    print(f"Initial state has {len(initial_state.factory_jigs)} jigs in Factory")
    print(f"Initial state has {len(initial_state.produced_parts)} produced parts")
    print(f"Initial state is at flight index {initial_state.current_flight_idx}")
    
    return initial_state

def test_actions(instance_data, initial_state):
    """Test action validation and state transitions."""
    print("\nTesting actions...")
    
    # Test MoveJigBetweenRacks
    print("\nTesting MoveJigBetweenRacks action...")
    # Try to move jig0005 from rack00 to rack01 (it's at the edge)
    move_action = MoveJigBetweenRacks(
        jig_id="jig0005",
        from_rack_id="rack00",
        to_rack_id="rack01"
    )
    
    # Check if action is valid
    is_valid = initial_state.is_valid_action(move_action, instance_data)
    print(f"  Action valid: {is_valid}")
    
    # Apply action if valid
    if is_valid:
        next_state = initial_state.get_next_state(move_action, instance_data)
        print(f"  Jig moved successfully")
        print(f"  Rack rack00 now contains: {', '.join(next_state.rack_jigs['rack00'])}")
        print(f"  Rack rack01 now contains: {', '.join(next_state.rack_jigs['rack01'])}")
    else:
        print("  Action is not valid, state remains unchanged")
    
    # Try an invalid action (move a jig that's not at the edge)
    invalid_move = MoveJigBetweenRacks(
        jig_id="jig0003",  # This jig is in the middle of rack00
        from_rack_id="rack00",
        to_rack_id="rack01"
    )
    
    is_valid = initial_state.is_valid_action(invalid_move, instance_data)
    print(f"\n  Invalid action valid check: {is_valid} (should be False)")
    
    # Test ProcessNextFlight
    print("\nTesting ProcessNextFlight action...")
    flight_action = ProcessNextFlight()
    
    # Check if action is valid
    is_valid = initial_state.is_valid_action(flight_action, instance_data)
    print(f"  Action valid: {is_valid}")
    
    # Apply action if valid
    if is_valid:
        next_state = initial_state.get_next_state(flight_action, instance_data)
        print(f"  Flight processed successfully")
        print(f"  Current flight index now: {next_state.current_flight_idx}")
    else:
        print("  Action is not valid, state remains unchanged")

def test_state_properties(instance_data, initial_state):
    """Test additional state properties and methods."""
    print("\nTesting state properties...")
    
    # Test get_jig_location
    jig_id = "jig0001"
    location = initial_state.get_jig_location(jig_id)
    print(f"  Location of {jig_id}: {location}")
    
    # Test jig_is_at_rack_edge
    rack_id = "rack00"
    jig_id = "jig0005"  # Should be at the edge
    is_at_edge = initial_state.jig_is_at_rack_edge(rack_id, jig_id, instance_data)
    print(f"  Is {jig_id} at the edge of {rack_id}? {is_at_edge}")
    
    jig_id = "jig0003"  # Should not be at the edge
    is_at_edge = initial_state.jig_is_at_rack_edge(rack_id, jig_id, instance_data)
    print(f"  Is {jig_id} at the edge of {rack_id}? {is_at_edge}")

if __name__ == "__main__":
    print("Starting Beluga Challenge setup test...")
    
    # Test loading
    instance_data, initial_data = test_loading()
    
    # Test state creation
    initial_state = test_state_creation(instance_data)
    
    # Test state properties
    test_state_properties(instance_data, initial_state)
    
    # Test actions
    test_actions(instance_data, initial_state)
    
    print("\nAll tests completed!")