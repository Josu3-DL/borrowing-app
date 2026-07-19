from django.contrib import admin
from django.urls import include, path

admin.site.site_header = "Administración de Borrowing"
admin.site.site_title = "Administración de Borrowing"
admin.site.index_title = "Panel de administración"

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('users.urls')),
    path('loans/', include('loans.urls')),
    path('payments/', include('payments.urls')),
]
