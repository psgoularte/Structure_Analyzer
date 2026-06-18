def calculate_force_magnitude(force_vector):
    """Calculates the magnitude of a force vector."""
    return (force_vector[0]**2 + force_vector[1]**2) ** 0.5


def calculate_reaction_forces(forces, constraints):
    """Calculates the reaction forces at nodes based on applied forces and constraints."""
    reaction_forces = []
    for constraint in constraints:
        # Placeholder for actual calculation logic
        reaction_force = sum(forces) * constraint
        reaction_forces.append(reaction_force)
    return reaction_forces


def format_force_output(forces):
    """Formats the output of forces for display."""
    formatted_forces = []
    for force in forces:
        formatted_forces.append(f"Force: {force:.2f} N")
    return formatted_forces


def validate_input_data(data):
    """Validates input data for nodes and bars."""
    if not isinstance(data, dict):
        raise ValueError("Input data must be a dictionary.")
    if 'nodes' not in data or 'bars' not in data:
        raise ValueError("Input data must contain 'nodes' and 'bars' keys.")
    return True