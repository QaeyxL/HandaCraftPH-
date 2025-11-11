from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('hc_app', '0006_productimage'),
    ]

    operations = [
        migrations.AlterField(
            model_name='productimage',
            name='image',
            field=models.ImageField(upload_to='products/images/'),
        ),
    ]
