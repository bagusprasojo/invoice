import json
from decimal import Decimal, InvalidOperation

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import ProtectedError, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from weasyprint import CSS, HTML

from .forms import CompanyForm, CustomerForm
from .models import Company, Customer, Invoice, InvoiceItem


def _money(value):
    if value in (None, ''):
        return Decimal('0')
    try:
        return Decimal(str(value).replace('.', '').replace(',', '.'))
    except (InvalidOperation, ValueError):
        return Decimal('0')


def _int(value, default=1):
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        return default
    return max(parsed, 1)


def _invoice_items_from_post(request):
    products = request.POST.getlist('product_name')
    prices = request.POST.getlist('price')
    discounts = request.POST.getlist('discount')
    quantities = request.POST.getlist('quantity')

    items = []
    for index, product in enumerate(products):
        name = product.strip()
        if not name:
            continue
        items.append({
            'product_name': name,
            'price': _money(prices[index] if index < len(prices) else 0),
            'discount': _money(discounts[index] if index < len(discounts) else 0),
            'quantity': _int(quantities[index] if index < len(quantities) else 1),
        })
    return items


def _invoice_initial_state(invoice=None):
    if invoice is None:
        return json.dumps({
            'company': '',
            'customer': '',
            'customers': [],
            'cashDiscount': 0,
            'notes': '',
            'items': [{'product_name': '', 'price': 0, 'discount': 0, 'quantity': 1}],
        })

    return json.dumps({
        'company': str(invoice.company_id),
        'customer': str(invoice.customer_id),
        'customers': list(invoice.company.customers.values('id', 'name', 'address', 'phone')),
        'cashDiscount': int(invoice.cash_discount),
        'notes': invoice.notes,
        'items': [
            {
                'product_name': item.product_name,
                'price': int(item.price),
                'discount': int(item.discount),
                'quantity': item.quantity,
            }
            for item in invoice.items.all()
        ] or [{'product_name': '', 'price': 0, 'discount': 0, 'quantity': 1}],
    })


@login_required
def invoice_list(request):
    invoices = Invoice.objects.select_related('company', 'customer').all()
    return render(request, 'billing/invoice_list.html', {'invoices': invoices})


@login_required
def company_list(request):
    query = request.GET.get('q', '').strip()
    companies = Company.objects.all()
    if query:
        companies = companies.filter(
            Q(code__icontains=query) |
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(phone__icontains=query)
        )
    page_obj = Paginator(companies, 10).get_page(request.GET.get('page'))
    return render(request, 'billing/company_list.html', {'page_obj': page_obj, 'query': query})


@login_required
def company_create(request):
    form = CompanyForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        company = form.save(commit=False)
        company.code = company.code.upper().strip()
        company.save()
        messages.success(request, 'Perusahaan berhasil disimpan.')
        return redirect('company_detail', pk=company.pk)
    return render(request, 'billing/form_page.html', {
        'form': form,
        'title': 'Tambah Perusahaan',
        'back_url': reverse('company_list'),
        'submit_label': 'Simpan Perusahaan',
    })


@login_required
def company_detail(request, pk):
    company = get_object_or_404(Company.objects.prefetch_related('customers'), pk=pk)
    invoices = Invoice.objects.filter(company=company).select_related('customer')[:10]
    return render(request, 'billing/company_detail.html', {'company': company, 'invoices': invoices})


@login_required
def company_update(request, pk):
    company = get_object_or_404(Company, pk=pk)
    form = CompanyForm(request.POST or None, instance=company)
    if request.method == 'POST' and form.is_valid():
        company = form.save(commit=False)
        company.code = company.code.upper().strip()
        company.save()
        messages.success(request, 'Perusahaan berhasil diperbarui.')
        return redirect('company_detail', pk=company.pk)
    return render(request, 'billing/form_page.html', {
        'form': form,
        'title': f'Edit Perusahaan {company.code}',
        'back_url': reverse('company_detail', args=[company.pk]),
        'submit_label': 'Simpan Perubahan',
    })


@login_required
def company_delete(request, pk):
    company = get_object_or_404(Company, pk=pk)
    if request.method == 'POST':
        name = company.name
        try:
            company.delete()
        except ProtectedError:
            messages.error(request, 'Perusahaan tidak bisa dihapus karena sudah dipakai pada invoice.')
            return redirect('company_detail', pk=company.pk)
        messages.success(request, f'Perusahaan {name} berhasil dihapus.')
        return redirect('company_list')
    return render(request, 'billing/company_confirm_delete.html', {'company': company})


@login_required
def customer_list(request):
    query = request.GET.get('q', '').strip()
    customers = Customer.objects.select_related('company').all()
    if query:
        customers = customers.filter(
            Q(name__icontains=query) |
            Q(address__icontains=query) |
            Q(phone__icontains=query) |
            Q(company__name__icontains=query) |
            Q(company__code__icontains=query)
        )
    page_obj = Paginator(customers, 10).get_page(request.GET.get('page'))
    return render(request, 'billing/customer_list.html', {'page_obj': page_obj, 'query': query})


@login_required
def customer_create(request):
    form = CustomerForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        customer = form.save()
        messages.success(request, 'Customer berhasil disimpan.')
        return redirect('customer_detail', pk=customer.pk)
    return render(request, 'billing/form_page.html', {
        'form': form,
        'title': 'Tambah Customer',
        'back_url': reverse('customer_list'),
        'submit_label': 'Simpan Customer',
    })


@login_required
def customer_detail(request, pk):
    customer = get_object_or_404(Customer.objects.select_related('company'), pk=pk)
    invoices = Invoice.objects.filter(customer=customer).select_related('company')[:10]
    return render(request, 'billing/customer_detail.html', {'customer': customer, 'invoices': invoices})


@login_required
def customer_update(request, pk):
    customer = get_object_or_404(Customer.objects.select_related('company'), pk=pk)
    form = CustomerForm(request.POST or None, instance=customer)
    if request.method == 'POST' and form.is_valid():
        customer = form.save()
        messages.success(request, 'Customer berhasil diperbarui.')
        return redirect('customer_detail', pk=customer.pk)
    return render(request, 'billing/form_page.html', {
        'form': form,
        'title': f'Edit Customer {customer.name}',
        'back_url': reverse('customer_detail', args=[customer.pk]),
        'submit_label': 'Simpan Perubahan',
    })


@login_required
def customer_delete(request, pk):
    customer = get_object_or_404(Customer.objects.select_related('company'), pk=pk)
    if request.method == 'POST':
        name = customer.name
        try:
            customer.delete()
        except ProtectedError:
            messages.error(request, 'Customer tidak bisa dihapus karena sudah dipakai pada invoice.')
            return redirect('customer_detail', pk=customer.pk)
        messages.success(request, f'Customer {name} berhasil dihapus.')
        return redirect('customer_list')
    return render(request, 'billing/customer_confirm_delete.html', {'customer': customer})


@login_required
def invoice_create(request):
    companies = Company.objects.prefetch_related('customers')
    if request.method == 'POST':
        company = get_object_or_404(Company, pk=request.POST.get('company'))
        customer = get_object_or_404(Customer, pk=request.POST.get('customer'), company=company)
        valid_items = _invoice_items_from_post(request)

        if not valid_items:
            messages.error(request, 'Tambahkan minimal satu produk.')
        else:
            with transaction.atomic():
                invoice = Invoice.objects.create(
                    company=company,
                    customer=customer,
                    issued_at=timezone.localdate(),
                    cash_discount=_money(request.POST.get('cash_discount')),
                    notes=request.POST.get('notes', '').strip(),
                )
                for item in valid_items:
                    InvoiceItem.objects.create(invoice=invoice, **item)
                invoice.recalculate()
            messages.success(request, f'Invoice {invoice.number} berhasil dibuat.')
            return redirect('invoice_detail', pk=invoice.pk)

    return render(request, 'billing/invoice_form.html', {
        'companies': companies,
        'title': 'Buat Invoice',
        'subtitle': 'Invoice baru',
        'submit_label': 'Simpan Invoice',
        'initial_state_json': _invoice_initial_state(),
    })


@login_required
def invoice_update(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('company', 'customer').prefetch_related('items'), pk=pk)
    companies = Company.objects.prefetch_related('customers')

    if request.method == 'POST':
        company = get_object_or_404(Company, pk=request.POST.get('company'))
        customer = get_object_or_404(Customer, pk=request.POST.get('customer'), company=company)
        valid_items = _invoice_items_from_post(request)

        if not valid_items:
            messages.error(request, 'Tambahkan minimal satu produk.')
        else:
            with transaction.atomic():
                company_changed = invoice.company_id != company.id
                invoice.company = company
                invoice.customer = customer
                invoice.cash_discount = _money(request.POST.get('cash_discount'))
                invoice.notes = request.POST.get('notes', '').strip()
                if company_changed:
                    invoice.number = ''
                invoice.save()
                invoice.items.all().delete()
                for item in valid_items:
                    InvoiceItem.objects.create(invoice=invoice, **item)
                invoice.recalculate()
            messages.success(request, f'Invoice {invoice.number} berhasil diperbarui.')
            return redirect('invoice_detail', pk=invoice.pk)

    return render(request, 'billing/invoice_form.html', {
        'companies': companies,
        'invoice': invoice,
        'title': f'Edit Invoice {invoice.number}',
        'subtitle': 'Ubah invoice',
        'submit_label': 'Simpan Perubahan',
        'initial_state_json': _invoice_initial_state(invoice),
    })


@login_required
def invoice_delete(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('company', 'customer'), pk=pk)
    if request.method == 'POST':
        number = invoice.number
        invoice.delete()
        messages.success(request, f'Invoice {number} berhasil dihapus.')
        return redirect('invoice_list')
    return render(request, 'billing/invoice_confirm_delete.html', {'invoice': invoice})


@login_required
def invoice_detail(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('company', 'customer').prefetch_related('items'), pk=pk)
    return render(request, 'billing/invoice_detail.html', {'invoice': invoice})


@login_required
def invoice_print(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('company', 'customer').prefetch_related('items'), pk=pk)
    return render(request, 'billing/invoice_print.html', {'invoice': invoice})


@login_required
def invoice_pdf(request, pk):
    invoice = get_object_or_404(Invoice.objects.select_related('company', 'customer').prefetch_related('items'), pk=pk)
    html = render_to_string('billing/invoice_pdf.html', {'invoice': invoice}, request=request)
    stylesheet = CSS(filename=str(settings.BASE_DIR / 'static' / 'css' / 'app.css'))
    pdf = HTML(string=html, base_url=request.build_absolute_uri('/')).write_pdf(stylesheets=[stylesheet])
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="{invoice.number}.pdf"'
    return response


@login_required
def company_customers(request, company_id):
    customers = Customer.objects.filter(company_id=company_id).values('id', 'name', 'address', 'phone')
    return JsonResponse({'customers': list(customers)})
