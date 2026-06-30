from django import template

register = template.Library()


@register.filter
def rupiah(value):
    try:
        amount = float(value or 0)
    except (TypeError, ValueError):
        amount = 0
    formatted = f'{amount:,.0f}'.replace(',', '.')
    return f'Rp {formatted}'
