from django import template

register = template.Library()


def pluralize_age(age):
    forms = ['год', 'года', 'лет']

    if 11 <= age % 100 <= 14:
        return forms[2]

    if age % 10 == 1:
        return forms[0]
    elif age % 10 in (2, 3, 4):
        return forms[1]
    else:
        return forms[2]


@register.filter
def age_word(age):
    if age is None:
        return ''

    return f'{age} {pluralize_age(age)}'