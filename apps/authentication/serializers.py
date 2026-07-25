from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password

from rest_framework import serializers

from apps.users.models import CustomUser

from .utils import validate_phone_number


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, validators=[validate_password])
    phone_number = serializers.CharField(validators=[validate_phone_number])
    code_no = serializers.IntegerField(min_value=1, max_value=9999)

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
            email=attrs["email"],
            password=attrs["password"],
        )
        if user is None:
            raise serializers.ValidationError("Invalid email or password.")

        attrs["user"] = user
        return attrs
