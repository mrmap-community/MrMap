from django.urls import path
from service.views import *

app_name='service'
urlpatterns = [
    path('', index, name='index'),
    path('session', session, name='session'),
    path('new/', new_service, name='wms'),
    path('new/register-form', register_form, name='wms'),
    path('wms/', wms, name='wms'),
    path('detail/wms/<int:id>', detail, name='detail-wms'),
    path('wfs/', wfs, name='wfs'),
    path('detail/wfs/<int:id>', detail, name='detail-wfs'),
]
