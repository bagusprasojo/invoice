from datetime import date
from decimal import Decimal

from django.test import TestCase

from .models import Company, Customer, Invoice, InvoiceItem


class InvoiceModelTests(TestCase):
    def test_invoice_number_resets_by_company_month(self):
        company = Company.objects.create(code='ACM', name='Acme', address='Jakarta', phone='021')
        customer = Customer.objects.create(company=company, name='Client', address='Bandung', phone='022')

        first = Invoice.objects.create(company=company, customer=customer, issued_at=date(2026, 6, 1))
        second = Invoice.objects.create(company=company, customer=customer, issued_at=date(2026, 6, 15))
        next_month = Invoice.objects.create(company=company, customer=customer, issued_at=date(2026, 7, 1))

        self.assertEqual(first.number, 'ACM-202606-001')
        self.assertEqual(second.number, 'ACM-202606-002')
        self.assertEqual(next_month.number, 'ACM-202607-001')

    def test_invoice_totals_include_item_discount_and_cash_discount(self):
        company = Company.objects.create(code='BP', name='Bintang Prima', address='Jakarta', phone='021')
        customer = Customer.objects.create(company=company, name='Client', address='Bandung', phone='022')
        invoice = Invoice.objects.create(company=company, customer=customer, cash_discount=Decimal('25000'))
        InvoiceItem.objects.create(invoice=invoice, product_name='Produk A', price=Decimal('100000'), discount=Decimal('10000'), quantity=2)
        InvoiceItem.objects.create(invoice=invoice, product_name='Produk B', price=Decimal('50000'), discount=Decimal('0'), quantity=1)

        invoice.recalculate()

        self.assertEqual(invoice.subtotal, Decimal('240000'))
        self.assertEqual(invoice.total, Decimal('215000'))
