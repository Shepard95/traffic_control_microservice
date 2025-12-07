from sumo_simulator import SUMOSimulator
import time

def run_simulation(checkpoint_id):
    """Endpoint para ejecutar simulación desde API"""
    simulator = SUMOSimulator()
    metrics = simulator.start_simulation(checkpoint_id)
    print(f"Simulación completada: {metrics}")
    return metrics
