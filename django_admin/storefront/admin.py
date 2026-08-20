from django.contrib import admin

from .models import CartItem, Order, OrderItem, Payment, Product, User


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "email", "role", "is_active", "created_at")
    list_filter = ("role", "is_active")
    search_fields = ("name", "email")
    ordering = ("-created_at",)
    # Never let the admin panel touch password hashes or the Auth0 link —
    # those are owned by fastapi_backend's auth logic.
    readonly_fields = ("hashed_password", "auth0_sub", "created_at", "updated_at")


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "category", "price", "stock", "popularity", "created_at")
    list_filter = ("category",)
    list_editable = ("stock",)
    search_fields = ("name", "description", "category")
    ordering = ("-created_at",)
    readonly_fields = ("created_at", "updated_at", "popularity")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "product_id", "quantity", "created_at")
    list_filter = ("created_at",)
    search_fields = ("user_id", "product_id")
    readonly_fields = ("created_at", "updated_at")


class OrderItemInline(admin.TabularInline):
    """
    NOTE: not actually registered as an inline (see OrderItemAdmin below).
    OrderItem has no real Django ForeignKey to Order — both are unmanaged
    models mirroring FastAPI-owned tables, where order_id is a plain
    integer column, not a relation Django's ORM knows about (see the
    module docstring in models.py). Django's inline machinery needs a real
    ForeignKey to auto-wire the "show these rows inside their parent's
    page" behavior, so instead of fighting that, order line items get
    their own list view (OrderItemAdmin), filterable by order_id — just as
    reachable, without pretending there's a relation Django can't see.
    """
    model = OrderItem


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "user_id", "total", "order_status", "payment_status", "created_at")
    list_filter = ("order_status", "payment_status")
    list_editable = ("order_status",)  # admins move pending -> shipped -> delivered (or -> cancelled) here
    search_fields = ("id", "user_id")
    ordering = ("-created_at",)
    # payment_status is Stripe-webhook-driven, not admin-set — see models.py
    readonly_fields = ("user_id", "subtotal", "tax", "total", "payment_status", "created_at", "updated_at")


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    # Every order's line items, filterable/searchable by order_id — see the
    # note on OrderItemInline above for why this is a list view, not a true
    # inline nested under Order.
    list_display = ("id", "order_id", "product_name", "unit_price", "quantity", "line_total")
    list_filter = ("order_id",)
    search_fields = ("order_id", "product_name")


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "order_id", "amount", "payment_method", "transaction_id", "status", "timestamp")
    list_filter = ("status", "payment_method")
    search_fields = ("order_id", "transaction_id")
    # The whole point of this table is to be an audit trail of what Stripe
    # actually reported — nothing here should be hand-edited.
    readonly_fields = ("order_id", "amount", "payment_method", "transaction_id", "status", "timestamp")

    def has_add_permission(self, request):
        return False
