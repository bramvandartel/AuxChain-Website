from django.contrib import admin

from auxchain.models import MetamaskUser, Contract, Bid

admin.site.register(MetamaskUser)
admin.site.register(Contract)
admin.site.register(Bid)