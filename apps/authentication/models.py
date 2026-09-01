import datetime
import secrets

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import BaseModel

# Create your models here.


class Otp(BaseModel):
    otp = models.CharField(max_length=100)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)

    class Meta:
        verbose_name = "OTP"
        verbose_name_plural = "OTPs"
        indexes = [
            models.Index(fields=["user", "is_used"]),
            models.Index(fields=["expires_at"]),
        ]

    def __str__(self):
        return f"{self.otp} - {self.user.email}"

    @classmethod
    def generate_otp(cls, user, expiry_minutes=60):
        """
        Generate a new OTP for the given user
        """
        # Invalidate existing unused OTPs for this user and purpose
        cls.objects.filter(
            user=user, is_used=False, expires_at__gt=timezone.now()
        ).update(is_used=True)

        # Generate a new OTP
        otp_code = secrets.token_urlsafe(16)
        expires_at = timezone.now() + datetime.timedelta(minutes=expiry_minutes)

        # Create and save new OTP
        otp_obj = cls.objects.create(otp=otp_code, user=user, expires_at=expires_at)

        return otp_obj

    def is_valid(self):
        """
        Check if the OTP is valid (not expired and not used)
        """
        return not self.is_used and self.expires_at > timezone.now()

    def use(self):
        """
        Mark the OTP as used
        """
        self.is_used = True
        self.save(update_fields=["is_used", "updated_at"])

    @classmethod
    def verify_otp(cls, user, otp_code):
        """
        Verify an OTP for a user and mark it as used if valid
        """
        try:
            otp_obj = cls.objects.get(
                user=user, otp=otp_code, is_used=False, expires_at__gt=timezone.now()
            )
            otp_obj.use()
            return True
        except cls.DoesNotExist:
            return False
