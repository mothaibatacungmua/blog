import enum


class PriceType(enum.Enum):
    Ask = 1
    Bid = 2
    BidOpen = 3
    BidHigh = 4
    BidLow = 5
    BidClose = 6
    AskOpen = 3
    AskHigh = 4
    AskLow = 5
    AskClose = 6

    @staticmethod
    def from_string(s):
        if s == PriceType.Ask.name:
            return PriceType.Ask
        elif s == PriceType.Bid.name:
            return PriceType.Bid
        elif s == PriceType.BidOpen.name:
            return PriceType.BidOpen
        elif s == PriceType.BidHigh.name:
            return PriceType.BidHigh
        elif s == PriceType.BidLow.name:
            return PriceType.BidLow
        elif s == PriceType.BidClose.name:
            return PriceType.BidClose
        elif s == PriceType.AskOpen.name:
            return PriceType.AskOpen
        elif s == PriceType.AskHigh.name:
            return PriceType.AskHigh
        elif s == PriceType.AskLow.name:
            return PriceType.AskLow
        elif s == PriceType.AskClose.name:
            return PriceType.AskClose

