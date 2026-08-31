import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0002_seed_batches"),
        ("users", "0004_populate_customuser_batch_id"),
    ]

    operations = [
        migrations.AlterField(
            model_name="customuser",
            name="batch_id",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.PROTECT,
                related_name="members",
                to="members.batch",
            ),
        ),
    ]