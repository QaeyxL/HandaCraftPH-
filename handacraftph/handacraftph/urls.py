from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static

'''
#Placeholder 
def home_view(request):
   return HttpResponse("Welcome Home!")
'''
urlpatterns = [
    path('admin/', admin.site.urls),
    #path('', home_view, name='home'),
    path('hc_app/', include('hc_app.urls')),
    #path('', include('hc_app.urls')),
    path('', include(('hc_app.urls', 'hc_app'), namespace='hc_app')), 
   
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)


if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)