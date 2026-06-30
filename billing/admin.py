from django.contrib import admin

from .models import Company, Customer, Invoice, InvoiceItem


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'phone', 'bank_name')
    search_fields = ('code', 'name', 'phone', 'bank_name', 'bank_account_number', 'bank_account_name')


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ('name', 'company', 'phone')
    list_filter = ('company',)
    search_fields = ('name', 'phone', 'company__name')


class InvoiceItemInline(admin.TabularInline):
    model = InvoiceItem
    extra = 0
    readonly_fields = ('subtotal',)


@admin.register(Invoice)
class InvoiceAdmin(admin.ModelAdmin):
    list_display = ('number', 'company', 'customer', 'issued_at', 'total')
    list_filter = ('company', 'issued_at')
    search_fields = ('number', 'customer__name', 'company__name')
    readonly_fields = ('number', 'subtotal', 'total')
    inlines = [InvoiceItemInline]
