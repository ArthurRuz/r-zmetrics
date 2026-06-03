from django import template
register = template.Library()

@register.filter
def split_filter(value, delimiter=','):
    """
        Divide string by delimiter

        :param str value: string to divide
        :param str delimiter: default ','
        :return: list of substrings or [] if value is not a string.
        """
    if not isinstance(value, str):
        return value
    return value.split(delimiter)