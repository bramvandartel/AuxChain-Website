from django.contrib.auth import login, logout
from django.http import JsonResponse, HttpResponse, HttpResponseNotFound, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django.views import View
from django.views.generic import TemplateView
from eth_account.messages import encode_defunct
from rest_framework.views import APIView
from web3 import Web3

from auxchain.models import MetamaskUser


# Create your views here.
class MainView(TemplateView):
    template_name = "home.html"


class CreateView(TemplateView):
    template_name = "create.html"


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
