from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('loans/', include('loans.urls')),
    path('payments/', include('payments.urls')),
]
