from concurrent.futures import ThreadPoolExecutor

from django.core.cache import cache
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .constants import get_validation_cache_key
from .id_validator import NationalIDValidator
from .models import APICallLog
from .serializers import NationalIDResponseSerializer, NationalIDSerializer
from django_ratelimit.decorators import ratelimit
from django.utils.decorators import method_decorator

_logging_executor = ThreadPoolExecutor(max_workers=10, thread_name_prefix="api_logger")

CACHE_ON = True

class ValidateNationalIDView(generics.CreateAPIView):

    serializer_class = NationalIDSerializer
    permission_classes = [IsAuthenticated]

    _validator = None

    @classmethod
    def get_validator(cls):
        if cls._validator is None:
            cls._validator = NationalIDValidator()
        return cls._validator
    
    @method_decorator(ratelimit(key='user', rate='30000/h'))
    @method_decorator(ratelimit(key='user', rate='3000/m'))
    @method_decorator(ratelimit(key='user', rate='300/s'))
    def post(self, request, *args, **kwargs):

        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        national_id = serializer.validated_data["national_id"]
        
        if CACHE_ON and national_id:
            cache_key = get_validation_cache_key(national_id)
            cached_result = cache.get(cache_key)

        if CACHE_ON and cached_result != None:
            result = cached_result
        else:
            validator = self.get_validator()
            validation_result = validator.validate(national_id)

            if validation_result["is_valid"]:
                result = validator.extract_info(national_id)
            else:
                result = {
                    "national_id": national_id,
                    "is_valid": False,
                    "errors": validation_result["errors"],
                }
            if CACHE_ON:
                _logging_executor.submit(cache.set(cache_key, result, timeout=3600))

            self._log_api_call(
                request=request,
                national_id=national_id,
                is_valid=result["is_valid"],
            )

        response_serializer = NationalIDResponseSerializer(result)
        return Response(response_serializer.data, status=status.HTTP_200_OK)

    def _log_api_call(self, request, national_id, is_valid):
        from django.conf import settings

        def log_in_background():
            try:
                user = request.user if request.user.is_authenticated else None

                x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
                if x_forwarded_for:
                    ip_address = x_forwarded_for.split(",")[0]
                else:
                    ip_address = request.META.get("REMOTE_ADDR")

                user_agent = request.META.get("HTTP_USER_AGENT", "")

                APICallLog.objects.create(
                    user=user,
                    national_id=national_id,
                    is_valid=is_valid,
                    ip_address=ip_address,
                    user_agent=user_agent,
                )
            except Exception as e:
                print(f"Error logging API call: {e}")

        # just for run  tests
        if settings.TESTING:
            log_in_background()
        else:
            _logging_executor.submit(log_in_background)
