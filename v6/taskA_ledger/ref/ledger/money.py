"""Exact integer-cent money type (no float arithmetic)."""


class Money:
    __slots__ = ("cents",)

    def __init__(self, cents):
        if isinstance(cents, Money):
            cents = cents.cents
        if isinstance(cents, float):
            raise TypeError("Money must be built from integer cents, not float")
        self.cents = int(cents)

    def __add__(self, other):
        return Money(self.cents + _as_money(other).cents)

    def __sub__(self, other):
        return Money(self.cents - _as_money(other).cents)

    def __neg__(self):
        return Money(-self.cents)

    def __eq__(self, other):
        return isinstance(other, Money) and self.cents == other.cents

    def __hash__(self):
        return hash(self.cents)

    def __repr__(self):
        sign = "-" if self.cents < 0 else ""
        c = abs(self.cents)
        return f"Money({sign}{c // 100}.{c % 100:02d})"

    def __str__(self):
        sign = "-" if self.cents < 0 else ""
        c = abs(self.cents)
        return f"{sign}{c // 100}.{c % 100:02d}"


def _as_money(v):
    return v if isinstance(v, Money) else Money(v)
