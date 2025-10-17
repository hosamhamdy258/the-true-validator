import json
from datetime import datetime
from pathlib import Path

from django.utils.translation import gettext_lazy as _


class NationalIDValidator:

    def __init__(self):
        self.governorates = self._load_governorates()
        self.generations = self._load_generations()

    def _load_governorates(self):
        base_dir = Path(__file__).resolve().parent.parent
        codes_file = base_dir / "codes.json"

        with open(codes_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return {gov["code"]: gov for gov in data["governorates"]}

    def _load_generations(self):
        base_dir = Path(__file__).resolve().parent.parent
        generations_file = base_dir / "generations.json"

        with open(generations_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        return data["generations"]

    def _normalize_id(self, national_id):
        return str(national_id).strip()

    def _validate_basic_format(self, national_id):
        errors = []

        if not national_id.isdigit():
            errors.append(_("National ID must contain only digits"))

        if len(national_id) != 14:
            errors.append(_(f"National ID must be exactly 14 digits (got {len(national_id)})"))

        return errors

    def _extract_century(self, national_id):
        return national_id[0]

    def _validate_century(self, century):
        if century not in ["2", "3"]:
            return _(f"Invalid century digit: {century} (must be 2 or 3)")
        return None

    def _get_century_text(self, century):
        return _("20th century (1900-1999)") if century == "2" else _("21st century (2000+)")

    def _extract_date_parts(self, national_id):
        year = int(national_id[1:3])
        month = int(national_id[3:5])
        day = int(national_id[5:7])
        return year, month, day

    def _calculate_full_year(self, century, year):
        if century == "2":
            return 1900 + year
        else:
            return 2000 + year

    def _validate_date(self, century, year, month, day):
        try:
            full_year = self._calculate_full_year(century, year)
            birth_date = datetime(full_year, month, day)

            if birth_date > datetime.now():
                return _(f"Birth date cannot be in the future: {birth_date.strftime('%Y-%m-%d')}")

            return None
        except ValueError as e:
            return _(f"Invalid date of birth: {str(e)}")

    def _extract_governorate_code(self, national_id):
        return national_id[7:9]

    def _validate_governorate(self, governorate_code):
        if governorate_code not in self.governorates:
            return _(f"Invalid governorate code: {governorate_code}")
        return None

    def _extract_serial_number(self, national_id):
        return national_id[9:13]

    def _extract_gender_digit(self, national_id):
        return int(national_id[12])

    def _determine_gender(self, gender_digit):
        return _("Male") if gender_digit % 2 == 1 else _("Female")

    def _calculate_age(self, birth_date):
        today = datetime.now()
        return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))

    def _get_generation(self, birth_year):
        for generation in self.generations:
            if generation["start_year"] <= birth_year <= generation["end_year"]:
                return {"name": generation["name"], "year_range": f"{generation['start_year']}-{generation['end_year']}"}
        return {"name": "Unknown", "year_range": "N/A"}

    def validate(self, national_id):
        errors = []

        national_id = self._normalize_id(national_id)
        errors.extend(self._validate_basic_format(national_id))

        if errors:
            return {"is_valid": False, "errors": errors}

        century = self._extract_century(national_id)
        century_error = self._validate_century(century)
        if century_error:
            errors.append(century_error)

        year, month, day = self._extract_date_parts(national_id)
        date_error = self._validate_date(century, year, month, day)
        if date_error:
            errors.append(date_error)

        governorate_code = self._extract_governorate_code(national_id)
        governorate_error = self._validate_governorate(governorate_code)
        if governorate_error:
            errors.append(governorate_error)

        return {"is_valid": len(errors) == 0, "errors": errors if errors else None}

    def extract_info(self, national_id):

        validation_result = self.validate(national_id)

        if not validation_result["is_valid"]:
            return None

        national_id = self._normalize_id(national_id)

        century = self._extract_century(national_id)
        century_text = self._get_century_text(century)
        year, month, day = self._extract_date_parts(national_id)
        full_year = self._calculate_full_year(century, year)
        birth_date = datetime(full_year, month, day)

        age = self._calculate_age(birth_date)

        governorate_code = self._extract_governorate_code(national_id)
        governorate_info = self.governorates.get(governorate_code, {})

        gender_digit = self._extract_gender_digit(national_id)
        gender = self._determine_gender(gender_digit)

        serial_number = self._extract_serial_number(national_id)
        generation = self._get_generation(full_year)

        return {
            "national_id": national_id,
            "is_valid": True,
            "birth_date": birth_date.strftime("%Y-%m-%d"),
            "birth_year": full_year,
            "birth_month": month,
            "birth_day": day,
            "age": age,
            "century": century_text,
            "generation": generation,
            "governorate": {
                "code": governorate_code,
                "name_english": governorate_info.get("english", "Unknown"),
                "name_arabic": governorate_info.get("arabic", "غير معروف"),
            },
            "gender": gender,
            "serial_number": serial_number,
        }
