from django.conf import settings
from rest_framework.test import APITestCase

from apps.profiles import choices

META = "/api/meta/"


class MetaTests(APITestCase):
    def test_is_public_and_has_all_sections(self):
        response = self.client.get(META)  # без входа

        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(
            set(data),
            {
                "countries",
                "fields",
                "statuses",
                "genders",
                "interests",
                "languages",
                "goals",
                "cities",
                "country_cities_default",
                "report_reasons",
                "limits",
            },
        )
        self.assertEqual(data["report_reasons"], [])

    def test_items_are_code_label_pairs_from_choices(self):
        data = self.client.get(META).json()

        for key, options in {
            "countries": choices.COUNTRIES,
            "fields": choices.FIELDS,
            "statuses": choices.STATUSES,
            "genders": choices.GENDERS,
            "interests": choices.INTERESTS,
            "languages": choices.LANGUAGES,
            "goals": choices.GOALS,
        }.items():
            with self.subTest(key):
                self.assertEqual(data[key], [{"code": c, "label": label} for c, label in options])

    def test_limits(self):
        limits = self.client.get(META).json()["limits"]

        self.assertEqual(
            limits,
            {
                "bio_max": 300,
                "min_age": settings.MIN_AGE,
                "adult_age": settings.ADULT_AGE,
                "interests_max": 10,
                "languages_max": 10,
                "goals_max": 8,
                "saved_max": settings.SAVED_MAX,
                "message_max": 4000,
                "request_max": 500,
            },
        )
        self.assertEqual((limits["min_age"], limits["adult_age"]), (13, 18))

    def test_response_is_cacheable_and_supports_etag(self):
        first = self.client.get(META)

        self.assertIn("public", first["Cache-Control"])
        self.assertIn("max-age=3600", first["Cache-Control"])
        etag = first["ETag"]
        second = self.client.get(META, HTTP_IF_NONE_MATCH=etag)
        self.assertEqual(second.status_code, 304)
        self.assertEqual(second["ETag"], etag)
        self.assertEqual(self.client.get(META, HTTP_IF_NONE_MATCH='"old"').status_code, 200)

    def test_only_get_is_allowed(self):
        self.assertEqual(self.client.post(META, {}, format="json").status_code, 405)


class MetaCitiesTests(APITestCase):
    def test_cities_are_uzbekistan_cities_with_unique_lowercase_codes(self):
        data = self.client.get(META).json()

        cities = data["cities"]
        self.assertEqual(len(cities), 24)
        self.assertEqual(cities, [{"code": c, "label": label} for c, label in choices.UZ_CITIES])
        codes = [city["code"] for city in cities]
        self.assertEqual(len(codes), len(set(codes)))
        for city in cities:
            self.assertEqual(city["code"], city["code"].lower())
            self.assertTrue(city["label"])
        self.assertIn({"code": "tashkent", "label": "Tashkent"}, cities)
        self.assertIn({"code": "almalyk", "label": "Almalyk"}, cities)
        self.assertEqual(data["country_cities_default"], "UZ")
        self.assertIn("UZ", [country["code"] for country in data["countries"]])
