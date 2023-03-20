import random
import string

from django.contrib.auth.models import AbstractUser
from django.db import models

class MetamaskUser(AbstractUser):
    public_address = models.CharField(max_length=64, unique=True)
    nonce = models.CharField(max_length=32, null=True, blank=True)

    def generate_nonce(self):
        alphabet = string.ascii_letters
        self.nonce = ''.join(random.choice(alphabet) for i in range(32))
        self.save()
