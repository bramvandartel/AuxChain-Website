from django.contrib import admin

from auxchain.models import MetamaskUser, Contract

admin.site.register(MetamaskUser)
admin.site.register(Contract)