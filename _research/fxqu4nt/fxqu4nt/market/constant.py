import enum


class PriceType(enum.Enum):
    Ask = 1
    Bid = 2
    Open = 3
    High = 4
    Low = 5
    Close = 6

    @staticmethod
    def from_string(s):
        if s == PriceType.Ask.name:
            return PriceType.Ask
        elif s == PriceType.Bid.name:
            return PriceType.Bid
        elif s == PriceType.Open.name:
            return PriceType.Open
        elif s == PriceType.High.name:
            return PriceType.High
        elif s == PriceType.Low.name:
            return PriceType.Low
        elif s == PriceType.Close.name:
            return PriceType.Close

