# Mission Utilities Technical Specification - Phase 2 (Gravity Assists)
Version 1.0

## 1. Problem Statement

### 1.1 Background
- Gravity assist calculations are essential for deep space missions
- Engineers need tools to optimize multi-planet flyby sequences
- Current tools either lack optimization capabilities or are too complex
- Phase 1 provided basic orbital mechanics; Phase 2 adds gravity assist optimization

### 1.2 Design Principles
0. "LLM - implementable". These principles keep this project implementable by LLMs that exist as of 18Dec2024.
1. KISS: Keep solutions simple and focused
2. YAGNI: Only implement proven necessary features
3. SOLID: Design modular, maintainable components
4. flat: All program files shall be in a single directory
5. Reliability First: Use validated libraries and test against known missions
6. Phase-Based Development: Clear separation of basic orbital mechanics (Phase 1) from gravity assists (Phase 2)

## 2. Technical Requirements

### 2.1 Input Requirements
- Initial orbit parameters (from Phase 1 OrbitCalculator)
- Launch window constraints (start/end dates)
- Available planetary bodies for gravity assists
- Mission constraints (max duration, min final velocity)
- Optimization preferences (maximize delta-v vs minimize time)

### 2.2 Output Format
```python
from mission_utilities import OrbitCalculator, GravityAssistCalculator
from datetime import datetime

# Start with Earth parking orbit (Phase 1 functionality)
initial_orbit = OrbitCalculator.from_orbital_elements(
    semi_major_axis=6678,  # km (LEO)
    eccentricity=0.001,
    inclination=28.5,  # degrees (typical launch latitude)
    reference_body="Earth"
)

# Create gravity assist calculator
assist_calc = GravityAssistCalculator(initial_orbit=initial_orbit)

# Plan sequence for solar system escape
trajectory = assist_calc.optimize_escape_sequence(
    launch_window_start=datetime(2026, 1, 1),
    launch_window_end=datetime(2026, 12, 31),
    available_bodies=['Venus', 'Jupiter', 'Saturn'],
    target_direction='solar_apex',
    optimization_goal='max_delta_v',
    max_mission_duration_years=10
)

# Results include:
print(f"Launch date: {trajectory.launch_date}")
print(f"Sequence: {trajectory.flyby_sequence}")
print(f"Total delta-v gained: {trajectory.total_delta_v} km/s")
print(f"Final velocity: {trajectory.escape_velocity} km/s")

# Phase 1's visualization extended
trajectory.plot()  # Shows complete trajectory with gravity assists
trajectory.plot_delta_v_gains()  # Shows velocity changes at each assist

# Get detailed timing for each encounter
for encounter in trajectory.encounters:
    print(f"Body: {encounter.body}")
    print(f"Date: {encounter.date}")
    print(f"Approach velocity: {encounter.v_approach} km/s")
    print(f"Departure velocity: {encounter.v_departure} km/s")
    print(f"Delta-v gained: {encounter.delta_v} km/s")
```

## 3. System Architecture

### 3.1 Core Components
```
mission_utilities/
    __init__.py
    orbit_calculator.py     # From Phase 1
    visualization.py        # Extended from Phase 1
    gravity_assist/
        calculator.py       # Main gravity assist interface
        sequence_opt.py     # Sequence optimization using ACO
        encounter_opt.py    # Encounter parameter optimization using PyGMO
        constraints.py      # Optimization constraints
        validation.py       # Voyager/Cassini validation
```

### 3.2 Component Specifications

#### 3.2.1 Gravity Assist Calculator
- Framework: PyGMO/pagmo for optimization
- Interfaces with Phase 1's OrbitCalculator
- Manages optimization workflow

#### 3.2.2 Sequence Optimization
```python
class SequenceOptimizer:
    def optimize_sequence(
        self, 
        available_bodies: List[str],
        constraints: OptimizationConstraints
    ) -> GravityAssistSequence:
        """
        Uses Ant Colony Optimization (ACO) for sequence determination
        """
        pheromone = self._init_pheromone_matrix(available_bodies)
        best_sequence = None
        best_score = float('-inf')
        
        for iteration in range(MAX_ACO_ITERATIONS):
            sequences = []
            for ant in range(N_ANTS):
                sequence = self._construct_sequence(
                    available_bodies,
                    pheromone,
                    constraints
                )
                optimized = self._optimize_sequence_parameters(sequence)
                sequences.append(optimized)
            
            self._update_pheromones(pheromone, sequences)
            current_best = max(sequences, key=self._evaluate_sequence)
            if self._evaluate_sequence(current_best) > best_score:
                best_sequence = current_best
                best_score = self._evaluate_sequence(current_best)
                
        return best_sequence
```

#### 3.2.3 Encounter Optimization
```python
class EncounterOptimizer:
    def __init__(self):
        self.udp = self._create_pygmo_problem()

    def _create_pygmo_problem(self):
        class GravityAssistProblem:
            def fitness(self, x):
                return [self._compute_objective(x)]
            
            def get_bounds(self):
                return (self._lower_bounds, self._upper_bounds)
            
            def get_ineq_constraints(self):
                return [
                    self._min_periapsis_constraint(x),
                    self._max_duration_constraint(x),
                    self._delta_v_constraint(x)
                ]
        
        return pg.problem(GravityAssistProblem())

    def optimize_encounter_parameters(self, sequence: List[str]) -> GravityAssistSequence:
        algo = pg.algorithm(pg.ipopt())  # Interior Point Optimizer
        pop = pg.population(self.udp, size=1)
        pop = algo.evolve(pop)
        
        return self._convert_solution(pop.champion_x)
```

## 4. Performance Requirements
- Sequence optimization must complete within 5 minutes for up to 4 planetary encounters
- Parameter optimization must converge within 2 minutes per sequence evaluation
- Memory usage should not exceed 4GB

## 5. Monitoring and Logging
- Log optimization progress and convergence metrics
- Record all constraint violations during optimization
- Track computation time for sequence vs parameter optimization

## 6. Testing Requirements

### 6.1 Core Testing
- Unit tests for optimization components
- Integration tests for complete sequences
- Validation against historical missions:
  1. Voyager 1 Jupiter-Saturn gravity assists
     - Match documented encounter dates within 24 hours
     - Match final velocity within 1%
  2. Voyager 2 Jupiter-Saturn-Uranus sequence
     - Match planetary encounter sequence
     - Match gravity assist delta-v gains within 2%
  3. Cassini Venus-Venus-Earth-Jupiter sequence
     - Validate multi-body gravity assist optimization
     - Match encounter parameters within documented margins

## 7. Security Requirements
None required for Phase 2.

## 8. Development Guidelines

### 8.1 Code Quality
- Type hints for all optimization interfaces
- Document optimization parameters and constraints
- Clear separation between sequence and parameter optimization
- PyGMO problem definitions must be self-contained

### 8.2 Documentation
- Mathematical basis for gravity assist calculations
- Optimization strategy and parameter choices
- Constraint definitions and rationale
- Example usage with realistic mission scenarios

## 9. Future Considerations
Features intentionally deferred (DO NOT IMPLEMENT):
1. Real-time trajectory optimization
2. Integration with external ephemeris data
3. Consideration of planetary atmospheres
4. Optimization for multiple spacecraft
5. Advanced propulsion models

## 10. Definition of Done
Mission Utilities Phase 2 is complete when:
1. Gravity assist sequence optimization is implemented and validated
2. Historical mission validation cases pass
3. Integration with Phase 1 components is complete
4. All tests pass with 90% coverage
5. A full system demonstration recreating a Voyager trajectory

## 11. Special Instructions
- Use PyGMO's constrained optimization capabilities
- Implement ACO for sequence optimization
- Document all assumptions about planetary orbits
- Include clear warnings about optimization limitations

## 12. Version History

- Version: 1.0
- Date: [Current Date]
- Previous: None
- Approved By: [Pending]
