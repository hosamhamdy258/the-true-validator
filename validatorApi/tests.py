import random
from datetime import date, timedelta

from django.contrib.auth.models import User
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.tokens import RefreshToken

from .constants import get_validation_cache_key
from .id_validator import NationalIDValidator
from .models import APICallLog


class EgyptianIDValidatorTestCase(TestCase):

    def setUp(self):
        self.validator = NationalIDValidator()

    def test_valid_century(self):
        national_ids = ["21801011401891", "31801011401891"]
        for national_id in national_ids:
            result = self.validator.validate(national_id)
            self.assertTrue(result["is_valid"])
            info = self.validator.extract_info(national_id)
            self.assertIsNotNone(info)
            if national_id[0] == "2":
                self.assertEqual(info["century"], "20th century (1900-1999)")
            elif national_id[0] == "3":
                self.assertEqual(info["century"], "21st century (2000+)")

    def test_invalid_century(self):
        national_id = "19801011401891"
        result = self.validator.validate(national_id)
        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid century digit", str(result["errors"]))

    def test_valid_date(self):
        national_id = "31811211401891"
        result = self.validator.validate(national_id)
        self.assertTrue(result["is_valid"])
        info = self.validator.extract_info(national_id)
        self.assertIsNotNone(info)
        self.assertEqual(info["birth_year"], 2018)
        self.assertEqual(info["birth_month"], 11)
        self.assertEqual(info["birth_day"], 21)

    def test_invalid_date(self):
        national_ids = ["29813321401891", "29812321401891"]
        for national_id in national_ids:
            result = self.validator.validate(national_id)
            self.assertFalse(result["is_valid"])
            self.assertIn("Invalid date", str(result["errors"]))

    def test_valid_governorate(self):
        national_id = "29801011401891"
        result = self.validator.validate(national_id)
        self.assertTrue(result["is_valid"])
        info = self.validator.extract_info(national_id)
        self.assertEqual(info["governorate"]["code"], "14")
        self.assertEqual(info["governorate"]["name_english"], "Qalyubia")

    def test_invalid_governorate(self):
        national_id = "29801019901891"
        result = self.validator.validate(national_id)
        self.assertFalse(result["is_valid"])
        self.assertIn("Invalid governorate code", str(result["errors"]))

    def test_gender_extraction(self):
        national_ids = ["21801011401881", "31801011401891"]
        for national_id in national_ids:
            result = self.validator.validate(national_id)
            self.assertTrue(result["is_valid"])
            info = self.validator.extract_info(national_id)
            self.assertIsNotNone(info)
            if int(national_id[12]) % 2 == 1:
                self.assertEqual(info["gender"], "Male")
            elif int(national_id[12]) % 2 == 1:
                self.assertEqual(info["gender"], "Female")

    def test_generation_extraction(self):
        test_cases = [
            ("29001011401891", "Millennials (Gen Y)", "1981-1996"),
            ("29801011401891", "Generation Z", "1997-2012"),
            ("30001011401891", "Generation Z", "1997-2012"),
            ("31501011401891", "Generation Alpha", "2013-2025"),
        ]
        for national_id, expected_name, expected_range in test_cases:
            result = self.validator.validate(national_id)
            self.assertTrue(result["is_valid"])
            info = self.validator.extract_info(national_id)
            self.assertIsNotNone(info)
            self.assertIn("generation", info)
            self.assertEqual(info["generation"]["name"], expected_name)
            self.assertEqual(info["generation"]["year_range"], expected_range)

    def test_valid_id_male_20th_century(self):
        national_id = "29801011401891"
        result = self.validator.validate(national_id)
        self.assertTrue(result["is_valid"])

        info = self.validator.extract_info(national_id)
        self.assertIsNotNone(info)
        self.assertEqual(info["birth_year"], 1998)
        self.assertEqual(info["birth_month"], 1)
        self.assertEqual(info["birth_day"], 1)
        self.assertEqual(info["gender"], "Male")
        self.assertEqual(info["governorate"]["code"], "14")
        self.assertEqual(info["governorate"]["name_english"], "Qalyubia")
        self.assertIn("generation", info)
        self.assertEqual(info["generation"]["name"], "Generation Z")

    def test_invalid_length(self):
        national_id = "123456789"
        result = self.validator.validate(national_id)
        self.assertFalse(result["is_valid"])
        self.assertIn("must be exactly 14 digits", str(result["errors"]))

    def test_non_numeric_id(self):
        national_id = "2980101140189A"
        result = self.validator.validate(national_id)
        self.assertFalse(result["is_valid"])
        self.assertIn("only digits", str(result["errors"]))

    def make_id(self, year, month, day, suffix="1401891"):
        century_prefix = "2" if year < 2000 else "3"
        year_short = str(year % 100).zfill(2)
        month = str(month).zfill(2)
        day = str(day).zfill(2)
        return f"{century_prefix}{year_short}{month}{day}{suffix}"

    def test_age_calculation(self):
        today = date.today()
        birth_date = today.replace(year=today.year - 30)
        national_id = self.make_id(year=birth_date.year, month=birth_date.month, day=birth_date.day)
        result = self.validator.validate(national_id)
        self.assertTrue(result["is_valid"])
        info = self.validator.extract_info(national_id)
        self.assertIsNotNone(info)
        self.assertEqual(info["age"], 30)

    def test_future_birth_date(self):
        tomorrow = date.today() + timedelta(days=1)
        national_id = self.make_id(year=tomorrow.year, month=tomorrow.month, day=tomorrow.day)
        result = self.validator.validate(national_id)
        self.assertFalse(result["is_valid"])
        info = self.validator.extract_info(national_id)
        self.assertIsNone(info)
        self.assertIn("cannot be in the future", str(result["errors"]))

    def id_generator(self, century_prefix=None, year=None, month=None, day=None, governorate=None, serial=None, male=True, check_digit=None):
        today = date.today()

        if century_prefix is None:
            if year is not None:
                century_prefix = 2 if int(year) < 2000 else 3
            else:
                century_prefix = random.choice([2, 3])

        if year is None:
            year = random.randint(0, today.year % 100)
        else:
            year = int(str(year)[-2:])

        full_year = (1900 if century_prefix == 2 else 2000) + year

        if full_year > today.year:
            full_year = today.year
            year = full_year % 100

        if month is None:
            max_month = today.month if full_year == today.year else 12
            month = random.randint(1, max_month)
        else:
            month = int(month)
            if full_year == today.year and month > today.month:
                month = today.month

        if day is None:
            if month in {1, 3, 5, 7, 8, 10, 12}:
                max_range = 31
            elif month == 2:
                is_leap = (full_year % 4 == 0 and full_year % 100 != 0) or (full_year % 400 == 0)
                max_range = 29 if is_leap else 28
            else:
                max_range = 30

            if full_year == today.year and month == today.month:
                max_range = min(max_range, today.day)

            day = random.randint(1, max_range)
        else:
            day = int(day)
            if full_year == today.year and month == today.month and day > today.day:
                day = today.day

        if governorate is None:
            governorate = random.choice(list(self.validator.governorates.keys()))

        if serial is None:
            serial = random.randint(0, 999)

        gender = random.choice([1, 3, 5, 7, 9]) if male else random.choice([2, 4, 6, 8])

        if check_digit is None:
            check_digit = random.randint(0, 9)

        return f"{century_prefix}" f"{year:02d}" f"{month:02d}" f"{day:02d}" f"{int(governorate):02d}" f"{serial:03d}" f"{gender}" f"{check_digit}"

    def test_random_id(self):
        generated_ids = [next(self.random_id()) for _ in range(5000)]
        for national_id in generated_ids:
            result = self.validator.validate(national_id)
            self.assertTrue(result["is_valid"])

    def random_id(self):
        while True:
            yield self.id_generator()


@override_settings(TESTING=True)
class ValidateNationalIDAPITestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(username="testuser", password="testpass")
        self.url = "/api/validate/"

        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)

    def test_valid_request_with_auth(self):
        data = {"national_id": "29801011401891"}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(self.url, data, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_valid"])
        self.assertEqual(response.data["birth_year"], 1998)
        self.assertIn("generation", response.data)
        self.assertEqual(response.data["generation"]["name"], "Generation Z")
        self.assertEqual(response.data["generation"]["year_range"], "1997-2012")

    def test_request_without_auth(self):
        data = {"national_id": "29801011401891"}
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_request_with_invalid_token(self):
        data = {"national_id": "29801011401891"}
        self.client.credentials(HTTP_AUTHORIZATION="Bearer invalid-token")
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_invalid_national_id(self):
        data = {"national_id": "123"}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        response = self.client.post(self.url, data, format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_api_call_logging(self):
        cache.clear()  # Clear cache to ensure fresh validation

        initial_count = APICallLog.objects.count()
        data = {"national_id": "29801011401891"}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        # First request - should log
        response1 = self.client.post(self.url, data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        self.assertEqual(APICallLog.objects.count(), initial_count + 1)

        # Second request (cached) - should NOT log again
        response2 = self.client.post(self.url, data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(APICallLog.objects.count(), initial_count + 1)

    def test_cache_hit(self):
        cache.clear()  # Clear cache before test

        data = {"national_id": "29801011401891"}
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response1 = self.client.post(self.url, data, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(self.url, data, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertEqual(response1.data["national_id"], response2.data["national_id"])
        self.assertEqual(response1.data["is_valid"], response2.data["is_valid"])

        cache_key = get_validation_cache_key(data["national_id"])
        cached_result = cache.get(cache_key)
        self.assertIsNotNone(cached_result)

    def test_cache_different_ids(self):
        cache.clear()

        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")

        response1 = self.client.post(self.url, {"national_id": "29801011401891"}, format="json")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)

        response2 = self.client.post(self.url, {"national_id": "30001011401891"}, format="json")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)

        self.assertNotEqual(response1.data["birth_year"], response2.data["birth_year"])
