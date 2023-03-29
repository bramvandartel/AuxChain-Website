import datetime
import json

import django.conf
import requests
from django.contrib.auth import login, logout
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import IntegrityError
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from eth_account.messages import encode_defunct
from rest_framework.views import APIView
from web3 import Web3

from auxchain.models import MetamaskUser, Contract, Bid


# Create your views here.
class MainView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)
        context['auctions'] = Contract.objects.all().filter(end_time__gte=datetime.datetime.now())
        return context


class MyView(LoginRequiredMixin, TemplateView):
    template_name = "my.html"

    def get_context_data(self, **kwargs):
        context = super(MyView, self).get_context_data(**kwargs)
        for bid in Bid.objects.filter(bidder=self.request.user.public_address):
            bid.auction.get_highest_bidder()
        context['seller_auctions'] = Contract.objects.filter(seller=self.request.user.public_address).order_by('-end_time')
        context['won_auctions'] = Contract.objects.filter(highest_bidder=self.request.user.public_address).order_by('-end_time')
        return context


class CreateView(TemplateView):
    template_name = "create.html"


class LoadContract(View):

    def get(self, request, address, *args, **kwargs):
        contract,_ = Contract.objects.get_or_create(contract_address=address)
        try:
            contract.load_from_blockchain()
            return HttpResponse("ok")
        except Exception as e:
            print(e)
            return HttpResponseNotFound()


class ContractView(TemplateView):
    template_name = "view_contract.html"

    def get_context_data(self, address, **kwargs):
        context = super(ContractView, self).get_context_data(**kwargs)
        w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/9998d159ba924e7aa128fac33d656dee'))
        abi = json.load(open(django.conf.settings.DEFAULT_CONTRACT_ABI))
        checksum_address = Web3.toChecksumAddress(address)
        contract_instance = w3.eth.contract(address=checksum_address, abi=abi)
        endtime = contract_instance.functions.endTime().call()
        # TODO: Can be omitted if end time is correctly set in contract.
        if endtime == 0:
            endtime = 1680104043
        context['instance'] = {
            'functions': contract_instance.all_functions(),
            'buyerDeposit': contract_instance.functions.buyerDeposit().call(),
            'description': contract_instance.functions.description().call(),
            'endTime': contract_instance.functions.endTime().call(),
            'endTimeReadable': datetime.datetime.fromtimestamp(endtime),
            'getStatus': contract_instance.functions.getStatus().call(),
            'highestBid': contract_instance.functions.highestBid().call(),
            'highestBidder': contract_instance.functions.highestBidder().call(),
            'seller': contract_instance.functions.seller().call(),
            'sellerDeposit': contract_instance.functions.sellerDeposit().call(),
            'title': contract_instance.functions.title().call(),
        }
        contract = {
            'address': address,
        }
        context['contract'] = contract
        return context


class RequestNonce(APIView):

    def get(self, request, public_address, *args, **kwargs):
        try:
            user = MetamaskUser.objects.get(public_address__iexact=public_address)
            user.generate_nonce()
            return JsonResponse({"success": True, "nonce": user.nonce})
        except MetamaskUser.DoesNotExist:
            return JsonResponse({"success": False, "error": "NoSuchUser"})

    def post(self, request, public_address, *args, **kwargs):
        print(request.POST)
        signature = request.POST.get('signature')
        try:
            print(signature)
            user = MetamaskUser.objects.get(public_address__iexact=public_address)
            nonce = user.nonce
            w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/9998d159ba924e7aa128fac33d656dee'))
            encoded_message = encode_defunct(bytes(nonce, encoding='utf8'))
            recoveredAddress = w3.eth.account.recover_message(encoded_message, signature=signature)
            if recoveredAddress.lower() == public_address.lower():
                login(request, user)
                return JsonResponse({'message': 'ok'})
            else:
                print(f"{recoveredAddress.lower()} == {public_address.lower()}?")
                return JsonResponse({'message': 'error'})
        except MetamaskUser.DoesNotExist:
            return HttpResponseNotFound()


class Logout(View):

    def get(self, request, *args, **kwargs):
        logout(request)
        return HttpResponseRedirect(reverse('auxchain:overview'))


class GetBids(APIView):

    def get(self, request, address, *args, **kwargs):
        result = []
        url = f"https://api-sepolia.etherscan.io/api?module=account&action=txlist&address={address}&sort=desc"
        answer = requests.get(url)
        answer = answer.json()
        try:
            for tx in answer['result']:
                if tx['functionName'] == "bid()" and tx['txreceipt_status'] == '1':
                    bid = int(tx['value']) - int(Contract.objects.get(contract_address=address).buyer_deposit)
                    result.append(
                        {'bid': bid, 'from': tx['from'],
                         'timestamp': datetime.datetime.fromtimestamp(int(tx['timeStamp']))})
                    Bid.objects.get_or_create(amount=bid, bidder=tx['from'],
                                              auction=Contract.objects.get(contract_address=address))

        except TypeError:
            return HttpResponseNotFound()
        return JsonResponse(data={'bids': result})
