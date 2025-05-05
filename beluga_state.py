from dataclasses import dataclass, field
from typing import Dict, List, Set, Tuple, FrozenSet, Any

@dataclass(frozen=True)
class BelugaState:
    """Represents the state of the Beluga problem."""
    
    # Rack status - mapping of rack_name to list of jig_names (in order)
    rack_jigs: Dict[str, Tuple[str, ...]]
    
    # Jig status - mapping of jig_name to (loaded status, part_id if loaded)
    jig_status: Dict[str, Tuple[bool, str]]
    
    # Beluga status - set of jig_names currently in Beluga
    beluga_jigs: FrozenSet[str]
    
    # Factory status - set of jig_names currently in factory
    factory_jigs: FrozenSet[str]
    
    # Production status - set of part_ids already sent to production
    produced_parts: FrozenSet[str]
    
    # Current flight index
    current_flight_idx: int
    
    # Optional metadata for tracking
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate the state after initialization."""
        # No validation for now to keep it simple
        pass
    
    def __eq__(self, other):
        """Check if two states are equal."""
        if not isinstance(other, BelugaState):
            return False
        
        # Compare all relevant state components
        return (self.rack_jigs == other.rack_jigs and
                self.jig_status == other.jig_status and
                self.beluga_jigs == other.beluga_jigs and
                self.factory_jigs == other.factory_jigs and
                self.produced_parts == other.produced_parts and
                self.current_flight_idx == other.current_flight_idx)
    
    def __hash__(self):
        """Generate a hash for the state for use in sets and dictionaries."""
        # Combine hashes of all immutable components
        components = (
            hash(tuple(sorted([(k, v) for k, v in self.rack_jigs.items()]))),
            hash(tuple(sorted([(k, v) for k, v in self.jig_status.items()]))),
            hash(self.beluga_jigs),
            hash(self.factory_jigs),
            hash(self.produced_parts),
            hash(self.current_flight_idx)
        )
        return hash(components)
    
    def get_jig_location(self, jig_id):
        """Return the location of a jig (rack_name, beluga, factory, or None)."""
        # Check if in Beluga
        if jig_id in self.beluga_jigs:
            return "beluga"
        
        # Check if in factory
        if jig_id in self.factory_jigs:
            return "factory"
        
        # Check if in a rack
        for rack_id, jigs in self.rack_jigs.items():
            if jig_id in jigs:
                return rack_id
        
        return None
    
    def jig_is_at_rack_edge(self, rack_id, jig_id, instance_data):
        """Check if a jig is at an edge of a rack."""
        jigs = self.rack_jigs.get(rack_id, ())
        
        if not jigs or jig_id not in jigs:
            return False
        
        # In this simplified implementation, we assume jigs can be accessed from both sides
        # So we check if jig is at either end of the rack
        if jigs[0] == jig_id or jigs[-1] == jig_id:
            return True
        
        return False
    
    def is_valid_action(self, action, instance_data):
        """Check if an action is valid in the current state."""
        # Import here to avoid circular imports
        from beluga_actions import MoveJigBetweenRacks, LoadJigToBeluga, UnloadJigFromBeluga, SendJigToProduction, ReturnEmptyJigFromFactory, ProcessNextFlight
        
        # MoveJigBetweenRacks
        if isinstance(action, MoveJigBetweenRacks):
            # Check if jig is in the source rack
            if action.jig_id not in self.rack_jigs.get(action.from_rack_id, ()):
                return False
            
            # Check if jig is at the edge of the source rack
            if not self.jig_is_at_rack_edge(action.from_rack_id, action.jig_id, instance_data):
                return False
            
            # Check if destination rack has space
            # Find rack size
            rack_size = 0
            for rack in instance_data.get('racks', []):
                if rack.get('name') == action.to_rack_id:
                    rack_size = rack.get('size', 0)
                    break
            
            # Calculate current occupancy of the destination rack
            current_occupancy = 0
            for jig_id in self.rack_jigs.get(action.to_rack_id, ()):
                # Get the jig type
                jig_type = instance_data['jigs'][jig_id]['type']
                
                # Determine if jig is loaded or empty
                loaded, _ = self.jig_status.get(jig_id, (False, ""))
                
                # Get the size from jig_types
                if loaded:
                    jig_size = instance_data['jig_types'][jig_type]['size_loaded']
                else:
                    jig_size = instance_data['jig_types'][jig_type]['size_empty']
                
                current_occupancy += jig_size
            
            # Get size of the jig to be moved
            jig_type = instance_data['jigs'][action.jig_id]['type']
            loaded, _ = self.jig_status.get(action.jig_id, (False, ""))
            if loaded:
                moving_jig_size = instance_data['jig_types'][jig_type]['size_loaded']
            else:
                moving_jig_size = instance_data['jig_types'][jig_type]['size_empty']
            
            # Check if there's enough space
            if current_occupancy + moving_jig_size > rack_size:
                return False
            
            return True
        
        # Other action types would be checked similarly
        # For simplicity, we'll assume other actions are valid
        return True
    
    def get_next_state(self, action, instance_data):
        """Apply an action to get the next state."""
        # Import here to avoid circular imports
        from beluga_actions import MoveJigBetweenRacks, LoadJigToBeluga, UnloadJigFromBeluga, SendJigToProduction, ReturnEmptyJigFromFactory, ProcessNextFlight
        
        if not self.is_valid_action(action, instance_data):
            return None
        
        # Create mutable copies of state components
        rack_jigs = {k: list(v) for k, v in self.rack_jigs.items()}
        jig_status = dict(self.jig_status)
        beluga_jigs = set(self.beluga_jigs)
        factory_jigs = set(self.factory_jigs)
        produced_parts = set(self.produced_parts)
        current_flight_idx = self.current_flight_idx
        
        # MoveJigBetweenRacks
        if isinstance(action, MoveJigBetweenRacks):
            # Remove jig from source rack
            rack_jigs[action.from_rack_id].remove(action.jig_id)
            # Add jig to destination rack
            rack_jigs[action.to_rack_id].append(action.jig_id)
        
        # LoadJigToBeluga
        elif isinstance(action, LoadJigToBeluga):
            # Remove jig from source rack
            rack_jigs[action.from_rack_id].remove(action.jig_id)
            # Add jig to Beluga
            beluga_jigs.add(action.jig_id)
        
        # UnloadJigFromBeluga
        elif isinstance(action, UnloadJigFromBeluga):
            # Remove jig from Beluga
            beluga_jigs.remove(action.jig_id)
            # Add jig to destination rack
            rack_jigs[action.to_rack_id].append(action.jig_id)
        
        # SendJigToProduction
        elif isinstance(action, SendJigToProduction):
            # Remove jig from source rack
            rack_jigs[action.from_rack_id].remove(action.jig_id)
            # Add jig to factory
            factory_jigs.add(action.jig_id)
            # Mark part as produced
            loaded, part_id = jig_status[action.jig_id]
            if loaded and part_id:
                produced_parts.add(part_id)
                # Update jig status to empty
                jig_status[action.jig_id] = (False, "")
        
        # ReturnEmptyJigFromFactory
        elif isinstance(action, ReturnEmptyJigFromFactory):
            # Remove jig from factory
            factory_jigs.remove(action.jig_id)
            # Add jig to destination rack
            rack_jigs[action.to_rack_id].append(action.jig_id)
        
        # ProcessNextFlight
        elif isinstance(action, ProcessNextFlight):
            # Increment flight index
            current_flight_idx += 1
            
            # Process incoming jigs from the flight
            if current_flight_idx < len(instance_data.get('flights', [])):
                current_flight = instance_data['flights'][current_flight_idx]
                # Note: In a complete implementation, we would handle the incoming jigs here
                # But for simplicity in this one-day implementation, we'll assume they're handled separately
        
        # Convert mutable collections back to immutable
        rack_jigs = {k: tuple(v) for k, v in rack_jigs.items()}
        beluga_jigs = frozenset(beluga_jigs)
        factory_jigs = frozenset(factory_jigs)
        produced_parts = frozenset(produced_parts)
        
        return BelugaState(
            rack_jigs=rack_jigs,
            jig_status=jig_status,
            beluga_jigs=beluga_jigs,
            factory_jigs=factory_jigs,
            produced_parts=produced_parts,
            current_flight_idx=current_flight_idx
        )
    
def create_initial_state(instance_data):
    """Create the initial state from the problem instance data."""
    
    # Extract rack information
    rack_jigs = {}
    for rack in instance_data.get('racks', []):
        rack_id = rack.get('name')
        jigs = tuple(rack.get('jigs', []))
        rack_jigs[rack_id] = jigs
    
    # Extract jig information
    jig_status = {}
    for jig_id, jig_data in instance_data.get('jigs', {}).items():
        loaded = not jig_data.get('empty', False)
        part_id = jig_id if loaded else ""
        jig_status[jig_id] = (loaded, part_id)
    
    # Initially, no jigs in Beluga or factory
    beluga_jigs = frozenset()
    factory_jigs = frozenset()
    
    # No parts produced initially
    produced_parts = frozenset()
    
    # Start with the first flight
    current_flight_idx = 0
    
    # Create the initial state
    return BelugaState(
        rack_jigs=rack_jigs,
        jig_status=jig_status,
        beluga_jigs=beluga_jigs,
        factory_jigs=factory_jigs,
        produced_parts=produced_parts,
        current_flight_idx=current_flight_idx
    )