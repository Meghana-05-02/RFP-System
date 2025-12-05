from django.contrib import admin
from .models import Vendor, RFP, RFPItem, Proposal


@admin.register(Vendor)
class VendorAdmin(admin.ModelAdmin):
    list_display = ['name', 'email', 'contact_person', 'created_at']
    search_fields = ['name', 'email', 'contact_person']
    list_filter = ['created_at']


class RFPItemInline(admin.TabularInline):
    model = RFPItem
    extra = 1


@admin.register(RFP)
class RFPAdmin(admin.ModelAdmin):
    list_display = ['title', 'status', 'budget', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['title', 'natural_language_input']
    inlines = [RFPItemInline]


@admin.register(RFPItem)
class RFPItemAdmin(admin.ModelAdmin):
    list_display = ['name', 'rfp', 'quantity', 'created_at']
    list_filter = ['created_at']
    search_fields = ['name', 'specifications']


@admin.register(Proposal)
class ProposalAdmin(admin.ModelAdmin):
    list_display = ['vendor', 'rfp', 'price', 'submitted_at']
    list_filter = ['submitted_at', 'vendor']
    search_fields = ['vendor__name', 'rfp__title', 'payment_terms', 'warranty']
    readonly_fields = ['submitted_at', 'updated_at']
