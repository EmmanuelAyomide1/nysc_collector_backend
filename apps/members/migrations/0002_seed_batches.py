from django.db import migrations

BATCHES = [
    (2025, "B2"),
    (2025, "C"),
    (2026, "A1"),
    (2026, "A2"),
    (2026, "B1"),
]


def seed_batches(apps, schema_editor):
    Batch = apps.get_model("members", "Batch")
    last_index = len(BATCHES) - 1

    for index, (year, name) in enumerate(BATCHES):
        Batch.objects.create(year=year, name=name, is_active=index == last_index)


def remove_batches(apps, schema_editor):
    Batch = apps.get_model("members", "Batch")
    Batch.objects.filter(
        year__in={year for year, _ in BATCHES},
        name__in={name for _, name in BATCHES},
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ("members", "0001_initial"),
    ]

    operations = [
        migrations.RunPython(seed_batches, remove_batches),
    ]
