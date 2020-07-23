from django.db import migrations

def create_initial_product(apps, schema_editor):
    Product = apps.get_model('subscription', 'product')
    Product.objects.get_or_create(
        defaults={
            'months': 1,
            'cost': 100,
            'public': True,
        }
    )

class Migration(migrations.Migration):

    dependencies = [
        ('subscription', '0002_interest_reject_reason'),
    ]

    operations = [
        migrations.RunPython(create_initial_product, lambda x,y: None)
    ]
