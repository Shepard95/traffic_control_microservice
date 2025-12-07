import os
import traci
import redis
import pymongo
import numpy as np
import pandas as pd
from datetime import datetime
from dotenv import load_dotenv
import json
import time
import threading

load_dotenv()

class SUMOSimulator:
    def __init__(self):
        self.redis_client = redis.Redis.from_url(os.getenv('REDIS_URL'))
        self.mongo_client = pymongo.MongoClient(os.getenv('MONGO_URI'))
        self.db = self.mongo_client['traffic_logs']
        self.sumocfg = 'config/copiap.sumocfg'  # Configurar con tus archivos SUMO
        
        # Métricas
        self.metrics = {
            'vehicles_count': 0,
            'waiting_time': 0,
            'co2_emissions': 0,
            'peak_hour': '00:00',
            'timestamp': None
        }
        
    def start_simulation(self, checkpoint_id=None):
        """Inicia simulación SUMO y guarda checkpoint en Redis"""
        sumoBinary = "sumo-gui"  # o "sumo" para headless
        traci.start([sumoBinary, "-c", self.sumocfg, "--no-step-log", "true"])
        
        step = 0
        while step < 3600:  # 1 hora de simulación
            traci.simulationStep()
            
            # Recolectar métricas
            self.collect_metrics()
            
            # Guardar estado en Redis (checkpoint)
            checkpoint_data = {
                'step': step,
                'vehicles': traci.vehicle.getIDList(),
                'traffic_lights': traci.trafficlight.getAllProgramLogics(),
                **self.metrics
            }
            
            # Guardar checkpoint en Redis (expira en 1h)
            self.redis_client.setex(f"checkpoint:{checkpoint_id}:{step}", 3600, json.dumps(checkpoint_data))
            
            # Log detallado en MongoDB
            self.db.simulation_logs.insert_one({
                'checkpoint_id': checkpoint_id,
                'step': step,
                'metrics': self.metrics,
                'timestamp': datetime.now()
            })
            
            step += 1
            
        traci.close()
        return self.metrics
    
    def collect_metrics(self):
        """Recolecta métricas clave: vehículos, esperas, CO2"""
        vehicles = traci.vehicle.getIDList()
        self.metrics['vehicles_count'] = len(vehicles)
        
        total_wait = 0
        total_co2 = 0
        for veh_id in vehicles:
            total_wait += traci.vehicle.getWaitingTime(veh_id)
            total_co2 += traci.vehicle.getCO2Emission(veh_id)
        
        self.metrics['waiting_time'] = total_wait / max(1, len(vehicles))
        self.metrics['co2_emissions'] = total_co2
        self.metrics['timestamp'] = datetime.now().strftime('%H:%M:%S')

    def get_checkpoint(self, checkpoint_id, step):
        """Recupera checkpoint desde Redis para reproducción web"""
        data = self.redis_client.get(f"checkpoint:{checkpoint_id}:{step}")
        return json.loads(data) if data else None
