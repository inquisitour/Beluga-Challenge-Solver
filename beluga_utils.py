def action_to_string(action):
    """Convert an action to a human-readable string."""
    from beluga_actions import MoveJigBetweenRacks, LoadJigToBeluga, UnloadJigFromBeluga, SendJigToProduction, ReturnEmptyJigFromFactory, ProcessNextFlight
    
    if isinstance(action, MoveJigBetweenRacks):
        return f"Move jig {action.jig_id} from rack {action.from_rack_id} to rack {action.to_rack_id}"
    
    elif isinstance(action, LoadJigToBeluga):
        return f"Load jig {action.jig_id} from rack {action.from_rack_id} to Beluga"
    
    elif isinstance(action, UnloadJigFromBeluga):
        return f"Unload jig {action.jig_id} from Beluga to rack {action.to_rack_id}"
    
    elif isinstance(action, SendJigToProduction):
        return f"Send jig {action.jig_id} from rack {action.from_rack_id} to production"
    
    elif isinstance(action, ReturnEmptyJigFromFactory):
        return f"Return empty jig {action.jig_id} from factory to rack {action.to_rack_id}"
    
    elif isinstance(action, ProcessNextFlight):
        return f"Process next flight"
    
    return str(action)

def print_state(state, instance_data):
    """Print a human-readable representation of the state."""
    print("\nState:")
    print(f"Current flight: {state.current_flight_idx}/{len(instance_data.get('flights', []))}")
    
    print("\nRacks:")
    for rack_id, jigs in state.rack_jigs.items():
        rack_info = ""
        for rack in instance_data.get('racks', []):
            if rack.get('name') == rack_id:
                rack_info = f" (size: {rack.get('size')})"
                break
        
        print(f"  {rack_id}{rack_info}: {', '.join(jigs) if jigs else 'empty'}")
    
    print("\nBeluga:")
    if state.beluga_jigs:
        print(f"  Jigs: {', '.join(state.beluga_jigs)}")
    else:
        print("  No jigs in Beluga")
    
    print("\nFactory:")
    if state.factory_jigs:
        print(f"  Jigs: {', '.join(state.factory_jigs)}")
    else:
        print("  No jigs in factory")
    
    print("\nProduced parts:")
    if state.produced_parts:
        print(f"  Parts: {', '.join(state.produced_parts)}")
    else:
        print("  No parts produced yet")

def print_plan(plan, instance_data):
    """Print a human-readable representation of the plan."""
    if not plan:
        print("No plan found!")
        return
    
    print(f"\nPlan with {len(plan)} steps:")
    for i, action in enumerate(plan):
        print(f"Step {i+1}: {action_to_string(action)}")