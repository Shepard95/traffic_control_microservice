import os
import traci
import pickle
import time
import numpy as np
from datetime import datetime

# Ruta de SUMO en tu PC
os.environ['SUMO_HOME'] = r'C:\Program Files (x86)\Eclipse\Sumo'

SUMO_CFG = os.path.join('config', 'grid4x4.sumocfg')
CHECKPOINT_DIR = 'checkpoints'
os.makedirs(CHECKPOINT_DIR, exist_ok=True)


def run_training(steps_total=2400, checkpoint_every=200):
    """
    Demo: corre SUMO y guarda checkpoints periódicos con:
    - vehículos
    - semáforos (fase simulada tipo IA)
    - congestión por dirección (N,S,E,W)
    """
    step = 0
    sumo_bin = os.path.join(os.environ['SUMO_HOME'], 'bin', 'sumo')  # consola

    # <<< AÑADIR ESTA LÍNEA >>>
    print("USANDO CFG:", os.path.abspath(SUMO_CFG))

    traci.start([
        sumo_bin,
        "-c", SUMO_CFG,
        "--no-step-log", "true",
    ])


    print(f"🚀 Entrenamiento demo iniciado con {SUMO_CFG}")
    print(f"💾 Checkpoint cada {checkpoint_every} steps")

    try:
        while step < steps_total:
            traci.simulationStep()
            step += 1

            if step % 50 == 0:
                print(f"Step {step} - vehículos: {len(traci.vehicle.getIDList())}")

            if step % checkpoint_every == 0:
                fname = save_checkpoint(step)
                print(f"💾 Checkpoint guardado: {fname}")

        print("✅ Demo finalizada")
    finally:
        traci.close()


def save_checkpoint(step: int) -> str:
    """Guarda checkpoint con vehículos, semáforos y congestión."""
    vehicles = []
    for vid in traci.vehicle.getIDList():
        x, y = traci.vehicle.getPosition(vid)
        waiting = traci.vehicle.getWaitingTime(vid)
        speed = traci.vehicle.getSpeed(vid)
        co2 = traci.vehicle.getCO2Emission(vid)
        vehicles.append({
            'id': vid,
            'x': float(x),
            'y': float(y),
            'waiting': float(waiting),
            'speed': float(speed),
            'co2': float(co2),
        })

    # Supongamos que cada traffic light controla 4 direcciones (N,S,E,W)
    congestion = {}
    for tl_id in traci.trafficlight.getIDList():
        # cajas simples alrededor del semáforo para estimar colas por dirección
        cx, cy = traci.junction.getPosition(tl_id)
        north = _count_vehicles_in_box(vehicles, cx-10, cy+30, cx+10, cy+80)
        south = _count_vehicles_in_box(vehicles, cx-10, cy-80, cx+10, cy-30)
        east = _count_vehicles_in_box(vehicles, cx+30, cy-10, cx+80, cy+10)
        west = _count_vehicles_in_box(vehicles, cx-80, cy-10, cx-30, cy+10)

        congestion[tl_id] = {
            'north_queue': north,
            'south_queue': south,
            'east_queue': east,
            'west_queue': west,
        }

    # “Política IA” simple: da verde a la dirección con más cola
    traffic_lights = {}
    for tl_id, cong in congestion.items():
        # dirección dominante
        dir_name, max_q = max(cong.items(), key=lambda kv: kv[1])
        # codificamos fase básica por dirección
        if 'north' in dir_name or 'south' in dir_name:
            phase = 'NS_GREEN'   # norte-sur verde, este-oeste rojo
        else:
            phase = 'EW_GREEN'   # este-oeste verde, norte-sur rojo

        traffic_lights[tl_id] = {
            'phase': phase,
            'congestion': cong,
        }

    metrics = {
        'vehicles_count': len(vehicles),
        'avg_waiting': float(np.mean([v['waiting'] for v in vehicles])) if vehicles else 0.0,
        'total_co2': float(sum(v['co2'] for v in vehicles)),
    }

    data = {
        'step': step,
        'time': datetime.now().strftime('%H:%M:%S'),
        'vehicles': vehicles,
        'traffic_lights': traffic_lights,
        'metrics': metrics,
    }

    fname = os.path.join(CHECKPOINT_DIR, f"step_{step:05d}.pkl")
    with open(fname, 'wb') as f:
        pickle.dump(data, f)

    return fname


def _count_vehicles_in_box(vehicles, x_min, y_min, x_max, y_max):
    count = 0
    for v in vehicles:
        if x_min <= v['x'] <= x_max and y_min <= v['y'] <= y_max:
            count += 1
    return count


if __name__ == "__main__":
    run_training(steps_total=2400, checkpoint_every=200)
