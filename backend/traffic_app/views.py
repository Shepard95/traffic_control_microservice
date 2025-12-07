import os
import glob
import pickle
from django.http import JsonResponse
from django.shortcuts import render
from django.conf import settings


def home(request):
    return render(request, 'index.html')


def _checkpoints_dir():
    base = settings.BASE_DIR  # backend/
    return os.path.abspath(os.path.join(base, '..', 'sumo_microservice', 'checkpoints'))


def api_checkpoints(request):
    checkpoints_dir = _checkpoints_dir()
    os.makedirs(checkpoints_dir, exist_ok=True)

    checkpoints = []
    pattern = os.path.join(checkpoints_dir, 'step_*.pkl')

    for pkl_file in sorted(glob.glob(pattern)):
        try:
            with open(pkl_file, 'rb') as f:
                data = pickle.load(f)
            checkpoints.append({
                'filename': os.path.basename(pkl_file),
                'step': data['step'],
                'time': data.get('time', ''),
                'vehicles_count': data['metrics']['vehicles_count'],
                'avg_waiting': data['metrics']['avg_waiting'],
                'total_co2': data['metrics']['total_co2'],
            })
        except Exception:
            continue

    return JsonResponse({'checkpoints': checkpoints})


def api_checkpoint(request, filename):
    checkpoints_dir = _checkpoints_dir()
    filepath = os.path.join(checkpoints_dir, filename)

    if not os.path.exists(filepath):
        return JsonResponse({'error': 'Checkpoint no encontrado'}, status=404)

    with open(filepath, 'rb') as f:
        data = pickle.load(f)

    return JsonResponse(data)
