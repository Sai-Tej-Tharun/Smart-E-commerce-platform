from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path

from storefront.views import (
    analytics_dashboard,
    export_orders_csv,
    export_orders_pdf,
    export_sales_csv,
    export_sales_pdf,
    export_users_csv,
    export_users_pdf,
)

urlpatterns = [
    path("admin/", admin.site.urls),
    path("analytics/", analytics_dashboard, name="analytics"),
    # ---- Export Reports (NEW — Admin Panel Analytics & Reporting milestone) ----
    path("export/orders/csv/", export_orders_csv, name="export_orders_csv"),
    path("export/orders/pdf/", export_orders_pdf, name="export_orders_pdf"),
    path("export/sales/csv/", export_sales_csv, name="export_sales_csv"),
    path("export/sales/pdf/", export_sales_pdf, name="export_sales_pdf"),
    path("export/users/csv/", export_users_csv, name="export_users_csv"),
    path("export/users/pdf/", export_users_pdf, name="export_users_pdf"),
]

# Serve uploaded product images locally in development. In production this
# would be handled by the web server / a cloud storage backend instead.
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)