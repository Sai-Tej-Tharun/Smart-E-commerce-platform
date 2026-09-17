"""
core/invoices.py
---------------------
Generates a simple invoice PDF for a subscription purchase using
ReportLab, saved under media/invoices/. Follows the same "small, focused
core/ helper" pattern as core/email.py and core/media.py.
"""

import uuid
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from core.media import MEDIA_ROOT

INVOICES_SUBDIR = "invoices"


def _invoices_dir() -> Path:
    d = MEDIA_ROOT / INVOICES_SUBDIR
    d.mkdir(parents=True, exist_ok=True)
    return d


def generate_invoice_pdf(
    user_name: str,
    plan_name: str,
    price: str,
    start_date: str,
    end_date: str,
    transaction_id: str,
) -> str:
    """
    Renders a one-page invoice and returns the URL path to store on
    BillingHistory.invoice_path (e.g. "/media/invoices/<uuid>.pdf").
    """
    filename = f"{uuid.uuid4().hex}.pdf"
    dest = _invoices_dir() / filename

    c = canvas.Canvas(str(dest), pagesize=A4)
    width, height = A4

    y = height - 30 * mm
    c.setFont("Helvetica-Bold", 18)
    c.drawString(20 * mm, y, "Subscription Invoice")

    y -= 12 * mm
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, f"Transaction ID: {transaction_id}")

    y -= 15 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Bill To")
    y -= 7 * mm
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, user_name)

    y -= 15 * mm
    c.setFont("Helvetica-Bold", 12)
    c.drawString(20 * mm, y, "Plan Details")
    y -= 7 * mm
    c.setFont("Helvetica", 11)
    c.drawString(20 * mm, y, f"Plan: {plan_name}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Price: {price}")
    y -= 7 * mm
    c.drawString(20 * mm, y, f"Billing period: {start_date} to {end_date}")

    y -= 20 * mm
    c.setFont("Helvetica-Oblique", 9)
    c.drawString(20 * mm, y, "This is a system-generated invoice for demo/testing purposes.")

    c.showPage()
    c.save()

    return f"/media/{INVOICES_SUBDIR}/{filename}"