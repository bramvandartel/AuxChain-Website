from django.urls import path, include

from auxchain.views import MainView, CreateView, RequestNonce, Logout, ContractView, LoadContract, GetBids, MyView

app_name = 'auxchain'

api = ([
           path('nonce/<str:public_address>', RequestNonce.as_view(), name='requestnonce'),
           path('contract/add/<str:address>', LoadContract.as_view(), name='add_contract'),
           path('contract/bids/<str:address>', GetBids.as_view(), name='get_bids'),
       ],
       'api')

urlpatterns = [
    path('', MainView.as_view(), name='overview'),
    path('create', CreateView.as_view(), name='create'),
    path('auction/<str:address>', ContractView.as_view(), name='view'),
    path('my', MyView.as_view(), name='my'),
    path('logout', Logout.as_view(), name='logout'),
    path('api/', include(api)),
]
