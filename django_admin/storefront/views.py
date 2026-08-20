from django.contrib.admin.views.decorators import staff_member_required
from django.db.models import Count, F, Sum
from django.shortcuts import render

from .models import CartItem, Order, Payment, Product, User


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
    }
    return render(request, "storefront/analytics.html", context)
