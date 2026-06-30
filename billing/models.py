from decimal import Decimal

from django.db import models
from django.utils import timezone


class Company(models.Model):
    code = models.CharField(max_length=12, unique=True)
    name = models.CharField(max_length=160)
    address = models.TextField()
    phone = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        verbose_name_plural = 'companies'

    def __str__(self):
        return f'{self.code} - {self.name}'


class Customer(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='customers')
    name = models.CharField(max_length=160)
    address = models.TextField()
    phone = models.CharField(max_length=40)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class Invoice(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name='invoices')
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name='invoices')
    number = models.CharField(max_length=32, unique=True, blank=True)
    issued_at = models.DateField(default=timezone.localdate)
    cash_discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-issued_at', '-id']

    def __str__(self):
        return self.number or 'Draft invoice'

    def save(self, *args, **kwargs):
        if not self.number and self.company_id:
            period = self.issued_at.strftime('%Y%m')
            prefix = f'{self.company.code.upper()}-{period}'
            last = (
                Invoice.objects.filter(company=self.company, number__startswith=prefix)
                .order_by('-number')
                .first()
            )
            sequence = 1
            if last:
                sequence = int(last.number.rsplit('-', 1)[-1]) + 1
            self.number = f'{prefix}-{sequence:03d}'
        super().save(*args, **kwargs)

    def recalculate(self):
        subtotal = sum((item.subtotal for item in self.items.all()), Decimal('0'))
        self.subtotal = subtotal
        self.total = max(subtotal - (self.cash_discount or Decimal('0')), Decimal('0'))
        self.save(update_fields=['subtotal', 'total', 'updated_at'])


class InvoiceItem(models.Model):
    invoice = models.ForeignKey(Invoice, on_delete=models.CASCADE, related_name='items')
    product_name = models.CharField(max_length=220)
    price = models.DecimalField(max_digits=14, decimal_places=2)
    discount = models.DecimalField(max_digits=14, decimal_places=2, default=0)
    quantity = models.PositiveIntegerField(default=1)
    subtotal = models.DecimalField(max_digits=14, decimal_places=2, default=0)

    class Meta:
        ordering = ['id']

    def save(self, *args, **kwargs):
        line_total = (self.price or Decimal('0')) * self.quantity
        self.subtotal = max(line_total - (self.discount or Decimal('0')), Decimal('0'))
        super().save(*args, **kwargs)

    def __str__(self):
        return self.product_name
