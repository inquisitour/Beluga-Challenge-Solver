def heuristic(state, instance_data, variant="standard"):
    """
    Calculate a heuristic estimate of steps needed to reach the goal.
    Supports multiple heuristic variants for comparison.
    
    Args:
        state: Current BelugaState
        instance_data: Problem instance data
        variant: Heuristic variant to use ("standard", "weighted", "production_focus")
        
    Returns:
        Estimated cost to goal
    """
    if variant == "weighted":
        return weighted_heuristic(state, instance_data)
    elif variant == "production_focus":
        return production_focus_heuristic(state, instance_data)
    else:  # standard
        return standard_heuristic(state, instance_data)

def standard_heuristic(state, instance_data):
    """
    Standard heuristic with equal weighting of components.
    This is our baseline heuristic.
    """
    # Count how many steps needed at minimum to reach the goal
    cost = 0
    
    # Get flights and production schedule info
    flights = instance_data.get('flights', [])
    flights_remaining = max(0, len(flights) - state.current_flight_idx - 1)
    
    # Collect production schedule
    production_schedule = []
    for line in instance_data.get('production_lines', []):
        production_schedule.extend(line.get('schedule', []))
    
    # 1. Estimate cost for unloading incoming jigs from current flight
    if state.current_flight_idx < len(flights):
        current_flight = flights[state.current_flight_idx]
        incoming_jigs = current_flight.get('incoming', [])
        # Each incoming jig needs to be unloaded (1 action)
        cost += len(incoming_jigs)
    
    # 2. Estimate cost for required production
    parts_to_produce = []
    for jig_id in production_schedule:
        # Only count parts that haven't been produced yet
        loaded, part_id = state.jig_status.get(jig_id, (False, ""))
        if loaded and part_id and part_id not in state.produced_parts:
            parts_to_produce.append(part_id)
    
    # Each part needs at least 1 step to send to production
    cost += len(parts_to_produce)
    
    # 3. Estimate cost for loading outgoing jigs to remaining flights
    total_outgoing_jigs = 0
    for i in range(state.current_flight_idx, len(flights)):
        total_outgoing_jigs += len(flights[i].get('outgoing', []))
    
    # Each outgoing jig requires at least 1 step to load
    cost += total_outgoing_jigs
    
    # 4. Estimate for remaining flight processing
    cost += flights_remaining
    
    # 5. Add estimate for jig swaps needed (very simplified)
    # For each part in the production schedule that's blocked by another jig
    # add a cost of 2 (1 for the swap, 1 for the move to production)
    blocked_jigs_estimate = 0
    for rack_id, jigs in state.rack_jigs.items():
        for i, jig_id in enumerate(jigs):
            # If jig is not at an edge and it's in the production schedule
            if i > 0 and i < len(jigs) - 1 and jig_id in production_schedule:
                blocked_jigs_estimate += 2
    
    cost += blocked_jigs_estimate
    
    return cost

def weighted_heuristic(state, instance_data):
    """
    Weighted heuristic that prioritizes different aspects of the problem.
    - Higher weight on production requirements
    - Lower weight on flight processing
    """
    # Get basic components like in standard heuristic
    flights = instance_data.get('flights', [])
    flights_remaining = max(0, len(flights) - state.current_flight_idx - 1)
    
    # Collect production schedule
    production_schedule = []
    for line in instance_data.get('production_lines', []):
        production_schedule.extend(line.get('schedule', []))
    
    # Count parts to produce
    parts_to_produce = []
    for jig_id in production_schedule:
        # Only count parts that haven't been produced yet
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
    
    # Apply weights to different components
    # Higher weight (2.0) for production and blocked jigs
    # Lower weight (0.5) for flight processing
    cost = (
        len(parts_to_produce) * 2.0 +  # Higher weight on production
        total_outgoing_jigs * 1.0 +
        flights_remaining * 0.5 +       # Lower weight on flight processing
        blocked_jigs * 2.0              # Higher weight on blocked jigs
    )
    
    return cost

def production_focus_heuristic(state, instance_data):
    """
    Production-focused heuristic that prioritizes completing the production schedule 
    in the correct order. Considers ordering constraints in the production lines.
    """
    cost = 0
    
    # Get flights
    flights = instance_data.get('flights', [])
    flights_remaining = max(0, len(flights) - state.current_flight_idx - 1)
    
    # Process production lines - this time considering ordering
    production_lines = instance_data.get('production_lines', [])
    for line in production_lines:
        schedule = line.get('schedule', [])
        
        # Check each jig in the production line schedule
        for idx, jig_id in enumerate(schedule):
            loaded, part_id = state.jig_status.get(jig_id, (False, ""))
            
            # If part hasn't been produced yet
            if loaded and part_id and part_id not in state.produced_parts:
                # Base cost for producing this part
                part_cost = 1
                
                # Add cost for any prerequisite parts in the same line
                # that haven't been produced yet
                for prev_idx in range(idx):
                    prev_jig_id = schedule[prev_idx]
                    prev_loaded, prev_part_id = state.jig_status.get(prev_jig_id, (False, ""))
                    if prev_loaded and prev_part_id and prev_part_id not in state.produced_parts:
                        # Higher cost for out-of-order production
                        part_cost += 3
                
                # Add distance from edge if jig is in a rack
                jig_location = state.get_jig_location(jig_id)
                if jig_location not in ["beluga", "factory", None]:
                    # It's in a rack - calculate its position from edge
                    rack_jigs = state.rack_jigs.get(jig_location, ())
                    if jig_id in rack_jigs:
                        jig_index = rack_jigs.index(jig_id)
                        distance_from_edge = min(jig_index, len(rack_jigs) - 1 - jig_index)
                        # Each position from edge requires at least one swap
                        part_cost += distance_from_edge * 2
                
                cost += part_cost
    
    # Add flight processing cost
    cost += flights_remaining
    
    # Add incoming/outgoing jig costs
    if state.current_flight_idx < len(flights):
        current_flight = flights[state.current_flight_idx]
        cost += len(current_flight.get('incoming', []))
    
    # Count outgoing jigs for remaining flights
    total_outgoing_jigs = 0
    for i in range(state.current_flight_idx, len(flights)):
        total_outgoing_jigs += len(flights[i].get('outgoing', []))
    cost += total_outgoing_jigs
    
    return cost