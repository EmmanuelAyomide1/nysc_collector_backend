from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from apps.authentication.models import Otp
from apps.members.models import Batch
from apps.users.models import CustomUser
from apps.users.serializers import UserSerializer

from .utils import validate_phone_number


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone_number = serializers.CharField(validators=[validate_phone_number])
    code_no = serializers.IntegerField(min_value=1, max_value=9999)
    batch = serializers.PrimaryKeyRelatedField(
        queryset=Batch.objects.filter(is_active=True)
    )

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "email",
            "password",
            "batch",
            "code_no",
            "first_name",
            "last_name",
            "phone_number",
        ]
        read_only_fields = ["id"]

    def create(self, validated_data):
        return get_user_model().objects.create_user(**validated_data)


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = authenticate(
            request=self.context.get("request"),
            email=attrs["email"].strip().lower(),
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        attrs["user"] = user
        return attrs


class ForgotPasswordRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()


class PasswordResetConfirmSerializer(serializers.Serializer):
    otp = serializers.CharField()
    password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs["password"] != attrs["confirm_password"]:
            raise serializers.ValidationError("Passwords do not match.")

        otp = Otp.objects.select_related("user").filter(otp=attrs["otp"]).first()
        if otp is None or not otp.is_valid():
            raise serializers.ValidationError("Invalid or expired reset code.")

        attrs["otp_instance"] = otp
        return attrs

    def save(self):
        otp = self.validated_data["otp_instance"]
        user = otp.user
        user.set_password(self.validated_data["password"])
        user.save(update_fields=["password"])
        otp.use()
        return user


class PasswordResetRequestSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)

    class Meta:
        model = Otp
        fields = ["id", "user", "otp", "is_used", "expires_at", "created_at"]
        read_only_fields = fields
