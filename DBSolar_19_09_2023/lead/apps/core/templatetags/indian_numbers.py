# from django import template
#
# register = template.Library()
#
# @register.filter
# def indian_currency(value):
#     """
#     Convert a number to Indian currency format (lakhs/crores).
#     Example: 2500000 -> ₹25,00,000.00
#     """
#     try:
#         value = float(value)
#         # Format with two decimal places
#         value_str = f"{value:.2f}"
#         parts = value_str.split('.')
#         integer_part = parts[0]
#         decimal_part = parts[1]
#
#         # Reverse the integer part for grouping
#         rev_int = integer_part[::-1]
#         groups = []
#         # First group of 3 digits (for thousands)
#         groups.append(rev_int[:3])
#         # Subsequent groups of 2 digits
#         i = 3
#         while i < len(rev_int):
#             groups.append(rev_int[i:i+2])
#             i += 2
#         # Join reversed groups and reverse back
#         formatted_int = ','.join(groups)[::-1]
#         return f"₹{formatted_int}.{decimal_part}"
#     except (ValueError, TypeError):
#         return "₹0.00"


from django import template

register = template.Library()

@register.filter
def indian_currency(value):
    try:
        value = float(value)
        value_str = f"{value:.2f}"
        parts = value_str.split('.')
        integer_part = parts[0]
        decimal_part = parts[1]

        # Reverse for grouping
        rev_int = integer_part[::-1]
        groups = []
        groups.append(rev_int[:3])
        i = 3
        while i < len(rev_int):
            groups.append(rev_int[i:i+2])
            i += 2
        formatted_int = ','.join(groups)[::-1]
        return f"₹{formatted_int}.{decimal_part}"
    except (ValueError, TypeError):
        return "₹0.00"