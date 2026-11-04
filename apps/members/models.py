from django.db import models

from apps.common.models import BaseModel


class Batch(BaseModel):
    class BatchName(models.TextChoices):
        A1 = "A1", "Batch A1"
        A2 = "A2", "Batch A2"
        B1 = "B1", "Batch B1"
        B2 = "B2", "Batch B2"
        C1 = "C1", "Batch C1"
        C2 = "C2", "Batch C2"

    year = models.PositiveSmallIntegerField()
    name = models.CharField(max_length=2, choices=BatchName.choices)
    is_active = models.BooleanField(default=True)

    @property
    def code(self):
        year = str(self.year)[-2:]

        batch_resolution = {
            self.BatchName.A1: "A",
            self.BatchName.A2: "A",
            self.BatchName.B1: "B",
            self.BatchName.B2: "B",
            self.BatchName.C1: "C",
            self.BatchName.C2: "C",
        }

        return f"{year}{batch_resolution[self.name]}"

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["year", "name"],
                name="unique_batch_per_year",
            )
        ]
        ordering = ["-year", "name"]

    def __str__(self):
        return f"{self.get_name_display()} ({self.year})"
