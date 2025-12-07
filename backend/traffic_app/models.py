from django.db import models
from django.contrib.auth.models import User as DjangoUser

class Simulation(models.Model):
    name = models.CharField(max_length=100)
    checkpoint_id = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(DjangoUser, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, default='pending')  # pending, running, completed
    
    def __str__(self):
        return f"{self.name} - {self.status}"
