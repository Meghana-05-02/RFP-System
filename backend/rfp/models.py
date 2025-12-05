from django.db import models
from typing import Optional


class Vendor(models.Model):
    """Vendor model to store vendor information."""
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    contact_person = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']
        verbose_name = 'Vendor'
        verbose_name_plural = 'Vendors'

    def __str__(self) -> str:
        return f"{self.name} ({self.contact_person})"


class RFP(models.Model):
    """RFP (Request for Proposal) model."""
    
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        SENT = 'sent', 'Sent'
        EVALUATING = 'evaluating', 'Evaluating'

    title = models.CharField(max_length=255)
    natural_language_input = models.TextField(
        help_text="Natural language description of the RFP requirements"
    )
    budget = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Budget in currency"
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'RFP'
        verbose_name_plural = 'RFPs'

    def __str__(self) -> str:
        return f"{self.title} ({self.get_status_display()})"


class RFPItem(models.Model):
    """RFP Item model to store individual items in an RFP."""
    rfp = models.ForeignKey(
        RFP,
        on_delete=models.CASCADE,
        related_name='items'
    )
    name = models.CharField(max_length=255)
    quantity = models.PositiveIntegerField(default=1)
    specifications = models.TextField(
        blank=True,
        help_text="Technical specifications or requirements for this item"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['id']
        verbose_name = 'RFP Item'
        verbose_name_plural = 'RFP Items'

    def __str__(self) -> str:
        return f"{self.name} (x{self.quantity}) - {self.rfp.title}"


class Proposal(models.Model):
    """Proposal model to store vendor proposals for RFPs."""
    rfp = models.ForeignKey(
        RFP,
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    vendor = models.ForeignKey(
        Vendor,
        on_delete=models.CASCADE,
        related_name='proposals'
    )
    raw_email_content = models.TextField(
        blank=True,
        help_text="Original email content from vendor"
    )
    price = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Proposal price/quote"
    )
    payment_terms = models.TextField(
        blank=True,
        help_text="Payment terms (e.g., Net 30, 50% upfront)"
    )
    warranty = models.TextField(
        blank=True,
        help_text="Warranty information"
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-submitted_at']
        verbose_name = 'Proposal'
        verbose_name_plural = 'Proposals'
        unique_together = ['rfp', 'vendor']

    def __str__(self) -> str:
        return f"Proposal from {self.vendor.name} for {self.rfp.title}"
