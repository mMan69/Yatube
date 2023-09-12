import datetime as dt


def year(request):
    year_now = dt.datetime.now().year
    return {"year": year_now}
