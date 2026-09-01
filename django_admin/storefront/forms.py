"""
storefront/forms.py
-----------------------
ProductAdminForm adds one field, `upload_image`, that isn't part of the
Product model at all — Product.images is a JSON array of URL strings
(matching fastapi_backend/models/product.py exactly, since this is an
unmanaged mirror of that table). This form lets an admin attach an actual
image file instead of hand-typing a URL; ProductAdmin.save_model (see
admin.py) is what actually saves the file to disk and appends its URL to
`images` — this form only handles picking the file and basic validation.
"""

import os

from django import forms

from .models import Product

ALLOWED_IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


class ProductAdminForm(forms.ModelForm):
    upload_image = forms.FileField(
        required=False,
        help_text="Upload a new product image (jpg/png/gif/webp). It's added to the Images list below on save — existing images aren't replaced.",
    )

    class Meta:
        model = Product
        fields = "__all__"

    def clean_upload_image(self):
        file = self.cleaned_data.get("upload_image")
        if file:
            ext = os.path.splitext(file.name)[1].lower()
            if ext not in ALLOWED_IMAGE_EXTENSIONS:
                raise forms.ValidationError(f"Unsupported file type '{ext}'. Use one of: {', '.join(sorted(ALLOWED_IMAGE_EXTENSIONS))}")
        return file