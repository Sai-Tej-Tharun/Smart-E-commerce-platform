from django.apps import AppConfig


class StorefrontConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "storefront"
    verbose_name = "Storefront (users, products, cart)"

    def ready(self):
        import storefront.signals  # noqa: F401  # registers the shipped/delivered notification hook