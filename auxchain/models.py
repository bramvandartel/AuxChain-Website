import datetime
import json
import random
import string

import django
import pytz
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.db.models.signals import post_save
from web3 import Web3

tz = pytz.UTC


class MetamaskUser(AbstractUser):
    public_address = models.CharField(max_length=64, unique=True)
    nonce = models.CharField(max_length=32, null=True, blank=True)

    def generate_nonce(self):
        alphabet = string.ascii_letters
        self.nonce = ''.join(random.choice(alphabet) for i in range(32))
        self.save()


class Contract(models.Model):
    contract_address = models.CharField(max_length=42, unique=True)
    title = models.CharField(max_length=256, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    seller = models.CharField(max_length=64, blank=True, null=True)
    end_time = models.DateTimeField(blank=True, null=True)
    seller_deposit = models.BigIntegerField(blank=True, null=True)
    buyer_deposit = models.BigIntegerField(blank=True, null=True)
    highest_bidder = models.CharField(max_length=64, blank=True, null=True)
    status = models.CharField(max_length=64, default="open")

    def get_highest_bidder(self):
        w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/9998d159ba924e7aa128fac33d656dee'))
        abi = json.load(open(django.conf.settings.DEFAULT_CONTRACT_ABI))
        checksum_address = Web3.toChecksumAddress(self.contract_address)
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        highest_bidder = contract.functions.highestBidder().call()
        if contract.functions.getStatus().call() == "closed":
            self.highest_bidder = highest_bidder
            self.status = "closed"
            self.save()
        return highest_bidder

    @property
    def highest_bid(self):
        w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/9998d159ba924e7aa128fac33d656dee'))
        abi = json.load(open(django.conf.settings.DEFAULT_CONTRACT_ABI))
        checksum_address = Web3.toChecksumAddress(self.contract_address)
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        return contract.functions.highestBid().call()


    def load_from_blockchain(self):
        w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/9998d159ba924e7aa128fac33d656dee'))
        abi = json.load(open(django.conf.settings.DEFAULT_CONTRACT_ABI))
        checksum_address = Web3.toChecksumAddress(self.contract_address)
        contract = w3.eth.contract(address=checksum_address, abi=abi)
        self.title = contract.functions.title().call()
        self.description = contract.functions.description().call()
        self.seller = contract.functions.seller().call()
        self.end_time = datetime.datetime.fromtimestamp(contract.functions.endTime().call(), tz=tz)
        self.seller_deposit = contract.functions.sellerDeposit().call()
        self.buyer_deposit = contract.functions.buyerDeposit().call()
        self.get_highest_bidder()
        self.save()

    def __str__(self):
        return f"{self.title} ({self.contract_address})"


class Bid(models.Model):
    auction = models.ForeignKey(Contract, on_delete=models.PROTECT)
    bidder = models.CharField(max_length=64)
    amount = models.BigIntegerField()

    def __str__(self):
        return f"{self.amount} by {self.bidder} for {self.auction}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['auction', 'bidder', 'amount'], name='unique bid')
        ]


def load_contract_details(sender, instance, created, **kwargs):
    if created:
        instance.load_from_blockchain()


post_save.connect(load_contract_details, sender=Contract)
