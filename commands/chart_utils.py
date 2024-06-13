def parseperiod(period: str) -> str:
    if period == "overall" or period == "alltime" or period == "all" or period == "o" or period == "a":
        period = "overall"
    elif period == "12month" or period == "1year" or period == "year" or period == "yearly" or period == "y":
        period = "12month"
    elif period == "1month" or period == "month" or period == "monthly" or period == "m":
        period = "1month"
    elif period == "3month" or period == "quarter" or period == "quarterly" or period == "3m" or period == "q":
        period = "3month"
    elif period == "6month" or period == "6m" or period == "h" or period == "half" or period == "halfyear":
        period = "6month"
    else:
        period = "7day"  # default to week

    return period

def parsechartsize(size: str) -> [int, int]:
    if "x" in size:
        size = size.split("x")
        return [int(size[0]), int(size[1])]
    else:
        return [3, 3]  # default case in general