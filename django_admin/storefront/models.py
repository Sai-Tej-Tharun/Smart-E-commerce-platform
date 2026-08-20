"""
storefront/models.py
----------------------
These models point at the SAME tables that fastapi_backend's Alembic
migration created (users, products, cart_items) — they do not create or
own that schema. `managed = False` on every Meta tells Django's migration
system "look, don't touch": `manage.py migrate` will never try to
create/alter/drop these tables, only Django's own internal ones.

Field-for-field, this mirrors fastapi_backend/models/*.py. One detail
worth flagging: the `role` column is a MySQL ENUM('ADMIN','STAFF','CUSTOMER')
(see the Alembic migration) — SQLAlchemy stores the Python Enum *member
name* (uppercase), not its lowercase `.value` that route code compares
against. So the CHOICES below are uppercase to match what's actually in
the database.
"""

from django.db import models


class User(models.Model):
    ROLE_CHOICES = [
        ("ADMIN", "Admin"),
        ("STAFF", "Staff"),
        ("CUSTOMER", "Customer"),
    ]

    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=150)
    email = models.CharField(max_length=150, unique=True)
    hashed_password = models.CharField(max_length=255, null=True, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="CUSTOMER")
    is_active = models.BooleanField(default=True)
    auth0_sub = models.CharField(max_length=255, null=True, blank=True, unique=True)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "users"
        verbose_name = "User"
        verbose_name_plural = "Users"

    def __str__(self):
        return f"{self.name} <{self.email}> ({self.role})"


class Product(models.Model):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200)
    description = models.TextField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
    images = models.JSONField(default=list, blank=True)
    category = models.CharField(max_length=100, null=True, blank=True)
    # How many times this product has been added to a cart — see
    # fastapi_backend/routes/cart.py, incremented on every POST /cart/add.
    popularity = models.IntegerField(default=0)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "products"
        verbose_name = "Product"
        verbose_name_plural = "Products"

    def __str__(self):
        return f"{self.name} (₹{self.price})"


class CartItem(models.Model):
    id = models.AutoField(primary_key=True)
    # Plain integer FKs (not models.ForeignKey) — the underlying columns are
    # already FastAPI-managed FKs with CASCADE deletes; declaring Django
    # ForeignKey objects here as well is unnecessary and, on an unmanaged
    # model, more likely to fight Django's migration checks than help.
    user_id = models.IntegerField()
    product_id = models.IntegerField()
    quantity = models.IntegerField(default=1)
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "cart_items"
        verbose_name = "Cart Item"
        verbose_name_plural = "Cart Items"

    def __str__(self):
        return f"user={self.user_id} product={self.product_id} qty={self.quantity}"


class Order(models.Model):
    # Same uppercase-name convention as User.role — see the module
    # docstring. Matches fastapi_backend/models/order.py's OrderStatus /
    # PaymentStatus enums exactly.
    ORDER_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("SHIPPED", "Shipped"),
        ("DELIVERED", "Delivered"),
        ("CANCELLED", "Cancelled"),
    ]
    PAYMENT_STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("PAID", "Paid"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    ]

    id = models.AutoField(primary_key=True)
    user_id = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    # Admins move this forward here in the admin panel as an order is
    # physically fulfilled — see the ADMIN NOTE in views.py / this file's
    # docstring reference in the report.
    order_status = models.CharField(max_length=20, choices=ORDER_STATUS_CHOICES, default="PENDING")
    # Read-only in the admin (see admin.py) — this is driven by the Stripe
    # webhook (fastapi_backend/routes/checkout.py), not set by hand.
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default="PENDING")
    created_at = models.DateTimeField(null=True, blank=True)
    updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "orders"
        verbose_name = "Order"
        verbose_name_plural = "Orders"

    def __str__(self):
        return f"Order #{self.id} — user={self.user_id} — ₹{self.total} ({self.order_status})"


class OrderItem(models.Model):
    id = models.AutoField(primary_key=True)
    order_id = models.IntegerField()
    product_id = models.IntegerField(null=True, blank=True)
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.IntegerField()
    line_total = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        managed = False
        db_table = "order_items"
        verbose_name = "Order Item"
        verbose_name_plural = "Order Items"

    def __str__(self):
        return f"order={self.order_id} — {self.product_name} x{self.quantity}"


class Payment(models.Model):
    STATUS_CHOICES = [
        ("PENDING", "Pending"),
        ("SUCCEEDED", "Succeeded"),
        ("FAILED", "Failed"),
        ("REFUNDED", "Refunded"),
    ]

    id = models.AutoField(primary_key=True)
    order_id = models.IntegerField(unique=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, default="stripe")
    # Stripe Checkout Session id until the webhook fires, then the Stripe
    # PaymentIntent id — see fastapi_backend/routes/checkout.py.
    transaction_id = models.CharField(max_length=255, null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="PENDING")
    timestamp = models.DateTimeField(null=True, blank=True)

    class Meta:
        managed = False
        db_table = "payments"
        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return f"order={self.order_id} — ₹{self.amount} ({self.status})"
