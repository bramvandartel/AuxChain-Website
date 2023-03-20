from django.urls import path, include

from auxchain.views import MainView, CreateView, RequestNonce, Logout

app_name = 'auxchain'

api = ([
           path('nonce/<str:public_address>', RequestNonce.as_view(), name='requestnonce'),
       ],
       'api')

urlpatterns = [
    path('', MainView.as_view(), name='overview'),
    path('create', CreateView.as_view(), name='create'),
    path('logout', Logout.as_view(), name='logout'),
    path('api/', include(api)),
]
