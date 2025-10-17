CACHE_KEY_NATIONAL_ID_VALIDATION = "national_id_validation:{national_id}"


def get_validation_cache_key(national_id):
    return CACHE_KEY_NATIONAL_ID_VALIDATION.format(national_id=national_id)
