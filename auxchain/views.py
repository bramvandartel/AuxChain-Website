from django.http import JsonResponse, HttpResponse, HttpResponseNotFound
from django.shortcuts import render
from django.views import View
from django.views.generic import TemplateView
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
        print(public_address)
        try:
            user = MetamaskUser.objects.get(public_address__iexact=public_address)
            user.generate_nonce()
            return JsonResponse({"success": True, "nonce": user.nonce})
        except MetamaskUser.DoesNotExist:
            return JsonResponse({"success": False, "error": "NoSuchUser"})

    def post(self, request, public_address, *args, **kwargs):
        signature = request.POST['signature']
        try:
            user = MetamaskUser.objects.get(public_address__iexact=public_address)
            nonce = user.nonce
            # TODO: Verify that the public_address signed the message
        except MetamaskUser.DoesNotExist:
            return HttpResponseNotFound()
