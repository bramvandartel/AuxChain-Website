import json

import django.conf
from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from eth_account.messages import encode_defunct
from rest_framework.views import APIView
from web3 import Web3

from auxchain.models import MetamaskUser, Contract


# Create your views here.
class MainView(TemplateView):
    template_name = "home.html"

    def get_context_data(self, **kwargs):
        context = super(MainView, self).get_context_data(**kwargs)
        context['auctions'] = Contract.objects.all()
        return context


class CreateView(TemplateView):
    template_name = "create.html"


class LoadContract(View):

    def get(self, request, address, *args, **kwargs):
        contract = Contract.objects.create(contract_address=address)
        try:
            contract.load_from_blockchain()
            return HttpResponse("ok")
        except Exception:
            contract.delete()
            return HttpResponseNotFound()

class ContractView(TemplateView):
    template_name = "view_contract.html"

    def get_context_data(self, address, **kwargs):
        context = super(ContractView, self).get_context_data(**kwargs)
        w3 = Web3(Web3.HTTPProvider('https://sepolia.infura.io/v3/9998d159ba924e7aa128fac33d656dee'))
        abi = json.load(open(django.conf.settings.DEFAULT_CONTRACT_ABI))
        checksum_address = Web3.toChecksumAddress(address)
        contract_instance = w3.eth.contract(address=checksum_address, abi=abi)
        context['instance'] = {
            'functions': contract_instance.all_functions(),
            'buyerDeposit': contract_instance.functions.buyerDeposit().call(),
            'description': contract_instance.functions.description().call(),
            'endTime': contract_instance.functions.endTime().call(),
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
