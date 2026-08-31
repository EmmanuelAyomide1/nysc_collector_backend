from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("users", "0005_alter_customuser_batch_id_not_null"),
    ]

    operations = [
        # Drop the constraint referencing the obsolete char field before
        # removing it.
        migrations.AlterUniqueTogether(
            name="customuser",
            unique_together=set(),
        ),
        migrations.RemoveField(
            model_name="customuser",
            name="batch",
        ),
        migrations.RenameField(
            model_name="customuser",
            old_name="batch_id",
            new_name="batch",
        ),
        migrations.AlterUniqueTogether(
            name="customuser",
            unique_together={("batch", "code_no")},
        ),
    ]