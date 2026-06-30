from django import forms

from .models import Company, Customer


INPUT_CLASS = 'w-full rounded-lg border border-slate-200 bg-white px-3 py-2.5 text-sm text-slate-900 shadow-sm outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-200'
TEXTAREA_CLASS = INPUT_CLASS + ' min-h-24'


class CompanyForm(forms.ModelForm):
    class Meta:
        model = Company
        fields = ['code', 'name', 'address', 'phone', 'bank_name', 'bank_account_number', 'bank_account_name']
        widgets = {
            'code': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'BP'}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nama perusahaan'}),
            'address': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': 'Alamat lengkap'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nomor telepon'}),
            'bank_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'BCA'}),
            'bank_account_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nomor rekening'}),
            'bank_account_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nama pemilik rekening'}),
        }


class CustomerForm(forms.ModelForm):
    class Meta:
        model = Customer
        fields = ['company', 'name', 'address', 'phone']
        widgets = {
            'company': forms.Select(attrs={'class': INPUT_CLASS}),
            'name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nama customer'}),
            'address': forms.Textarea(attrs={'class': TEXTAREA_CLASS, 'placeholder': 'Alamat lengkap'}),
            'phone': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nomor telepon'}),
            'bank_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'BCA'}),
            'bank_account_number': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nomor rekening'}),
            'bank_account_name': forms.TextInput(attrs={'class': INPUT_CLASS, 'placeholder': 'Nama pemilik rekening'}),
        }
