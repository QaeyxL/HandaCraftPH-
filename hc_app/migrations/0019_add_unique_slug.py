from django.db import migrations, models
import django.db.models.deletion
from django.db.models import Q

class Migration(migrations.Migration):

    dependencies = [
        ('hc_app', '0018_attribute_cartitem_customization_cartitem_item_price_and_more'),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='category',
            constraint=models.UniqueConstraint(fields=['slug'], name='unique_category_slug', condition=~Q(slug=None)),
        ),
    ]
