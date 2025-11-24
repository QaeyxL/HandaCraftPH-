from django.db.models import Min
from .models import Category


def get_unique_categories():
    """Return a list of Category objects de-duplicated by name (first instance per name),
    ordered by name.

    This is defensive: some environments may contain duplicate Category rows with the
    same name. We pick the smallest id for each name to provide a stable representative.
    Works with SQLite and Postgres.
    """
    qs = Category.objects.values('name').annotate(min_id=Min('id')).order_by('name')
    ids = [item['min_id'] for item in qs]
    if not ids:
        return []
    cats = Category.objects.filter(id__in=ids)
    cat_map = {c.id: c for c in cats}
    ordered = [cat_map[i] for i in ids if i in cat_map]
    return ordered
