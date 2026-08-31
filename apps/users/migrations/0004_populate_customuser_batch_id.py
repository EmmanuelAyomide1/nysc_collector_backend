from django.db import migrations


def populate_batch_id(apps, schema_editor):
    Batch = apps.get_model("members", "Batch")
    CustomUser = apps.get_model("users", "CustomUser")

    batch_by_name = {batch.name: batch for batch in Batch.objects.all()}

    for user in CustomUser.objects.exclude(batch__in=batch_by_name):
        raise RuntimeError(
            f"No seeded batch matches CustomUser(id={user.id}).batch={user.batch!r}"
        )

    for name, batch in batch_by_name.items():
        CustomUser.objects.filter(batch=name).update(batch_id=batch.id)


def reverse_populate_batch_id(apps, schema_editor):
    CustomUser = apps.get_model("users", "CustomUser")
    CustomUser.objects.update(batch_id=None)


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0002_seed_batches"),
        ("users", "0003_customuser_batch_id"),
    ]

    operations = [
        migrations.RunPython(populate_batch_id, reverse_populate_batch_id),
    ]