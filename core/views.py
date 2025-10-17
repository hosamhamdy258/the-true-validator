# views.py
from django.shortcuts import render

from validatorApi.id_validator import NationalIDValidator


def home(request):
    """Home page with ID validator testing interface"""
    result = None
    national_id = None

    if request.method == "POST":
        national_id = request.POST.get("national_id", "").strip()

        if national_id:
            # Use validator directly (no authentication needed for testing)
            validator = NationalIDValidator()
            validation_result = validator.validate(national_id)

            if validation_result["is_valid"]:
                result = validator.extract_info(national_id)
            else:
                result = {"national_id": national_id, "is_valid": False, "errors": validation_result["errors"]}

    context = {
        "result": result,
        "national_id": national_id,
    }

    return render(request, "home.html", context)
