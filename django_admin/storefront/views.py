import json

from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, F, Sum
from django.db.models.functions import TruncDate
from django.shortcuts import render

from .models import CartItem, Order, OrderItem, Payment, Product, User


@staff_member_required
def analytics_dashboard(request):
    """
    A small read-only analytics page, reachable from the Django admin at
    /analytics/ (there's also a link in the admin index — see
    templates/admin/index.html). Everything here is a simple aggregate
    query over the same three tables fastapi_backend writes to.
    """
    total_users = User.objects.count()
    users_by_role = list(User.objects.values("role").annotate(count=Count("id")).order_by("role"))
    active_users = User.objects.filter(is_active=True).count()

    total_products = Product.objects.count()
    out_of_stock = Product.objects.filter(stock=0).count()
    low_stock = Product.objects.filter(stock__gt=0, stock__lte=5).count()
    inventory_value = Product.objects.aggregate(total=Sum(F("price") * F("stock")))["total"] or 0
    products_by_category = list(
        Product.objects.exclude(category__isnull=True)
        .exclude(category="")
        .values("category")
        .annotate(count=Count("id"))
        .order_by("-count")
    )

    total_cart_items = CartItem.objects.count()
    total_units_in_carts = CartItem.objects.aggregate(total=Sum("quantity"))["total"] or 0

    top_products = list(
        CartItem.objects.values("product_id")
        .annotate(times_added=Count("id"), total_qty=Sum("quantity"))
        .order_by("-total_qty")[:5]
    )
    # Attach product names for display (small dataset — fine to loop)
    product_names = {p.id: p.name for p in Product.objects.filter(id__in=[t["product_id"] for t in top_products])}
    for t in top_products:
        t["name"] = product_names.get(t["product_id"], f"Product #{t['product_id']}")

    # ---- Orders & payments (NEW — Checkout & Stripe Payments milestone) ----
    total_orders = Order.objects.count()
    orders_by_status = list(Order.objects.values("order_status").annotate(count=Count("id")).order_by("order_status"))
    revenue_paid = Order.objects.filter(payment_status="PAID").aggregate(total=Sum("total"))["total"] or 0
    pending_payment_value = Order.objects.filter(payment_status="PENDING").aggregate(total=Sum("total"))["total"] or 0

    payments_by_status = list(Payment.objects.values("status").annotate(count=Count("id")).order_by("status"))
    failed_payments = Payment.objects.filter(status="FAILED").count()

    # ---- NEW (Admin Panel — Analytics & Reporting milestone) ----
    # Revenue trend: paid-order revenue per day, most recent 30 days with
    # any paid orders. TruncDate lets us group a DateTimeField by calendar
    # day across MySQL/SQLite alike.
    revenue_trend_qs = (
        Order.objects.filter(payment_status="PAID")
        .annotate(day=TruncDate("created_at"))
        .values("day")
        .annotate(revenue=Sum("total"))
        .order_by("day")[:30]
    )
    revenue_trend = [
        {"day": row["day"].isoformat() if row["day"] else "", "revenue": float(row["revenue"] or 0)}
        for row in revenue_trend_qs
    ]

    # Top-selling products by actual revenue (OrderItem line_total on paid
    # orders) — distinct from `top_products` above, which is "most added
    # to cart" and may include items never actually purchased.
    paid_order_ids = list(Order.objects.filter(payment_status="PAID").values_list("id", flat=True))
    top_selling_qs = (
        OrderItem.objects.filter(order_id__in=paid_order_ids)
        .values("product_name")
        .annotate(units_sold=Sum("quantity"), revenue=Sum("line_total"))
        .order_by("-revenue")[:5]
    )
    top_selling_products = [
        {"name": row["product_name"], "units_sold": row["units_sold"], "revenue": float(row["revenue"] or 0)}
        for row in top_selling_qs
    ]

    # Low stock alerts: the actual product list, not just a count (the
    # existing `low_stock` count above stays as-is for the summary card).
    low_stock_products = list(
        Product.objects.filter(stock__gt=0, stock__lte=5).values("id", "name", "stock").order_by("stock")
    )
    out_of_stock_products = list(Product.objects.filter(stock=0).values("id", "name").order_by("name"))

    context = {
        "total_users": total_users,
        "active_users": active_users,
        "users_by_role": users_by_role,
        "total_products": total_products,
        "out_of_stock": out_of_stock,
        "low_stock": low_stock,
        "inventory_value": inventory_value,
        "products_by_category": products_by_category,
        "total_cart_items": total_cart_items,
        "total_units_in_carts": total_units_in_carts,
        "top_products": top_products,
        "total_orders": total_orders,
        "orders_by_status": orders_by_status,
        "revenue_paid": revenue_paid,
        "pending_payment_value": pending_payment_value,
        "payments_by_status": payments_by_status,
        "failed_payments": failed_payments,
# NEW (Admin Panel — Analytics & Reporting milestone)
"revenue_trend": revenue_trend,
"revenue_trend_json": revenue_trend,
"top_selling_products": top_selling_products,
"top_selling_products_json": top_selling_products,
"low_stock_products": low_stock_products,
"out_of_stock_products": out_of_stock_products,
    }
    return render(request, "storefront/analytics.html", context)


# =============================================================================
# Export Reports (NEW — Admin Panel Analytics & Reporting milestone)
# =============================================================================
# Six views: Orders / Sales / Users, each as CSV and PDF. CSV uses Django's
# built-in csv module (no new dependency); PDF uses reportlab (added to
# requirements.txt) — a pure-Python PDF library with no system-level
# dependencies, unlike alternatives such as WeasyPrint.

import csv
from io import BytesIO

from django.http import HttpResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet


def _csv_response(filename, header, rows):
    response = HttpResponse(content_type="text/csv")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(header)
    for row in rows:
        writer.writerow(row)
    return response


def _pdf_response(filename, title, header, rows):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = [Paragraph(title, styles["Title"]), Spacer(1, 0.25 * inch)]

    table_data = [header] + [[str(cell) for cell in row] for row in rows]
    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2f3b2f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f0e8")]),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)

    buffer.seek(0)
    response = HttpResponse(buffer.getvalue(), content_type="application/pdf")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


@staff_member_required
def export_orders_csv(request):
    rows = [
        [o.id, o.user_id, o.subtotal, o.tax, o.total, o.order_status, o.payment_status, o.created_at]
        for o in Order.objects.order_by("-created_at")
    ]
    return _csv_response(
        "orders_report.csv",
        ["Order ID", "User ID", "Subtotal", "Tax", "Total", "Order Status", "Payment Status", "Created At"],
        rows,
    )


@staff_member_required
def export_orders_pdf(request):
    rows = [
        [o.id, o.user_id, f"₹{o.total}", o.order_status, o.payment_status, o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else ""]
        for o in Order.objects.order_by("-created_at")
    ]
    return _pdf_response(
        "orders_report.pdf",
        "Orders Report",
        ["Order ID", "User ID", "Total", "Order Status", "Payment Status", "Created"],
        rows,
    )


@staff_member_required
def export_sales_csv(request):
    """Sales report = paid orders only, i.e. actual recognized revenue."""
    rows = [
        [o.id, o.user_id, o.total, o.created_at]
        for o in Order.objects.filter(payment_status="PAID").order_by("-created_at")
    ]
    return _csv_response("sales_report.csv", ["Order ID", "User ID", "Amount", "Date"], rows)


@staff_member_required
def export_sales_pdf(request):
    paid_orders = Order.objects.filter(payment_status="PAID").order_by("-created_at")
    total_revenue = paid_orders.aggregate(total=Sum("total"))["total"] or 0
    rows = [
        [o.id, o.user_id, f"₹{o.total}", o.created_at.strftime("%Y-%m-%d %H:%M") if o.created_at else ""]
        for o in paid_orders
    ]
    rows.append(["", "", f"Total: ₹{total_revenue}", ""])
    return _pdf_response("sales_report.pdf", "Sales Report", ["Order ID", "User ID", "Amount", "Date"], rows)


@staff_member_required
def export_users_csv(request):
    rows = [[u.id, u.name, u.email, u.role, u.is_active, u.created_at] for u in User.objects.order_by("id")]
    return _csv_response("users_report.csv", ["User ID", "Name", "Email", "Role", "Active", "Created At"], rows)


@staff_member_required
def export_users_pdf(request):
    rows = [
        [u.id, u.name, u.email, u.role, "Yes" if u.is_active else "No"]
        for u in User.objects.order_by("id")
    ]
    return _pdf_response("users_report.pdf", "Users Report", ["User ID", "Name", "Email", "Role", "Active"], rows)