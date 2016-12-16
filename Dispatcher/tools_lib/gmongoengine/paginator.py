MAX_COUNT = 100


def paginator(queryset, page, count, limit=True):
    if count > MAX_COUNT or count < 0:
        count = MAX_COUNT
    if page <= 0:
        page = 1

    amount = queryset.count()
    if count == 0:
        content = []
    elif not limit:
        content = queryset
    else:
        start = (page - 1) * count
        end = start + count
        content = queryset[start:end]

    return amount, content
