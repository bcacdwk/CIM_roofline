"""Display-only formatting; exact counting remains integer/Fraction arithmetic."""
from decimal import Decimal, localcontext, ROUND_HALF_UP
from fractions import Fraction


def ri_decimal(value, tex=False):
    if value == 'infinity':
        return r'\infty' if tex else '∞'
    if isinstance(value, dict):
        value = Fraction(value['numerator'], value['denominator'])
    value = Fraction(value)
    with localcontext() as context:
        context.prec = 50
        number = Decimal(value.numerator) / Decimal(value.denominator)
        exponent = -1 if number >= 1 or number == 0 else number.adjusted() - 2
        rounded = number.quantize(Decimal(1).scaleb(exponent), rounding=ROUND_HALF_UP)
        return format(rounded, 'f')


def count_label(value, tex=False):
    if value == 'infinity':
        return r'\infty' if tex else '∞'
    for factor, suffix in ((1048576, 'M'), (1024, 'K')):
        if value >= factor and value % factor == 0:
            return f'{value // factor}' + (rf'\mathrm{{{suffix}}}' if tex else suffix)
    return str(value)
