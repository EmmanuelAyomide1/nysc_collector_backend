from django.contrib.auth import get_user_model

from rest_framework import serializers

from apps.members.serializers import BatchSerializer


class UserSerializer(serializers.ModelSerializer):
    batch = BatchSerializer(read_only=True)

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
        ]
        read_only_fields = fields
