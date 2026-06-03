from django import template

register = template.Library()

@register.filter
def market_value_format(value):
    if value is None:
        return ""

    try:
        value = float(value)
    except (TypeError, ValueError):
        return value

    if value >= 1_000_000:
        millions = value / 1_000_000
        formatted = f"{millions:.1f}".rstrip('0').rstrip('.')
        return f"{formatted} млн €"
    elif value >= 1_000:
        return f"{value / 1_000:.0f} тыс €"
    else:
        return f"{int(value)} €"