from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.authentication.utils import validate_phone_number


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = get_user_model()
        fields = [
            "id",
            "email",
            "batch",
            "code_no",
            "first_name",
            "last_name",
            "phone_number",
            "role",
            "is_active",
        ]
        read_only_fields = fields


class MemberUpdateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(
        validators=[validate_phone_number], required=False
    )

    class Meta:
        model = get_user_model()
        fields = [
            "batch",
            "code_no",
            "first_name",
            "last_name",
            "phone_number",
        ]
