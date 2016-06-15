from django import template

register = template.Library()

LEADING_PAGE_RANGE_DISPLAYED = TRAILING_PAGE_RANGE_DISPLAYED = 2
LEADING_PAGE_RANGE = TRAILING_PAGE_RANGE = 2
NUM_PAGES_OUTSIDE_RANGE = 2
ADJACENT_PAGES = 3


@register.inclusion_tag('tags/thumb_cart.html')
def thumb_cart(cart):
    return {
        'cart': cart
    }


@register.inclusion_tag('tags/meal_info.html')
def meal_info(meal, subsec=False):
    return {
        'meal': meal,
        'subsection': subsec
    }


@register.inclusion_tag('tags/pagination.html')
def pagination(page_obj):
    paginator = page_obj.paginator
    # if not page_obj.has_other_pages():
    #     return {'paginator': page_obj}
    pages = paginator.num_pages
    page = page_obj.number
    in_leading_range = in_trailing_range = False
    pages_outside_leading_range = pages_outside_trailing_range = range(0)
    if pages <= LEADING_PAGE_RANGE_DISPLAYED + NUM_PAGES_OUTSIDE_RANGE + 1:
        in_leading_range = in_trailing_range = True
        page_range = [n for n in range(1, pages + 1)]
    elif page <= LEADING_PAGE_RANGE:
        in_leading_range = True
        page_range = [n for n in range(1, LEADING_PAGE_RANGE_DISPLAYED + 1)]
        pages_outside_leading_range = [n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
    elif page > pages - TRAILING_PAGE_RANGE:
        in_trailing_range = True
        page_range = [n for n in range(pages - TRAILING_PAGE_RANGE_DISPLAYED + 1, pages + 1) if 0 < n <= pages]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    else:
        page_range = [n for n in range(page - ADJACENT_PAGES, page + ADJACENT_PAGES + 1) if 0 < n <= pages]
        pages_outside_leading_range = [n + pages for n in range(0, -NUM_PAGES_OUTSIDE_RANGE, -1)]
        pages_outside_trailing_range = [n + 1 for n in range(0, NUM_PAGES_OUTSIDE_RANGE)]
    next_p = previous = page
    if page_obj.has_previous():
        previous = page_obj.previous_page_number()
    if page_obj.has_next():
        next_p = page_obj.next_page_number()
    return {
        'pages': pages,
        'page': page,
        'previous': previous,
        'next': next_p,
        'has_previous': page_obj.has_previous(),
        'has_next': page_obj.has_next(),
        'page_range': page_range,
        'in_leading_range': in_leading_range,
        'in_trailing_range': in_trailing_range,
        'pages_outside_leading_range': pages_outside_leading_range,
        'pages_outside_trailing_range': pages_outside_trailing_range,
        'paginator': page_obj,
    }
