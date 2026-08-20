from django.contrib import admin
from django.urls import path

from storefront.views import analytics_dashboard

urlpatterns = [
    path("admin/", admin.site.urls),
    path("analytics/", analytics_dashboard, name="analytics"),
]
