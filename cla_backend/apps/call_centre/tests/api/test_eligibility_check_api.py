import random

from rest_framework import status
from rest_framework.test import APITestCase

from legalaid.tests.views.test_base import CLAOperatorAuthBaseApiTestMixin
from legalaid.tests.views.mixins.eligibility_check_api import NestedEligibilityCheckAPIMixin

from core.tests.mommy_utils import make_recipe


class EligibilityCheckTestCase(CLAOperatorAuthBaseApiTestMixin, NestedEligibilityCheckAPIMixin, APITestCase):
    LOOKUP_KEY = "case_reference"

    @property
    def response_keys(self):
        return [
            "reference",
            "category",
            "notes",
            "your_problem_notes",
            "property_set",
            "dependants_young",
            "dependants_old",
            "you",
            "partner",
            "disputed_savings",
            "has_partner",
            "on_passported_benefits",
            "on_nass_benefits",
            "in_category_skip_income_check",
            "is_you_or_your_partner_over_60",
            "state",
            "specific_benefits",
        ]

    def test_notes_are_readonly(self):
        data = {"notes": "just trying...", "your_problem_notes": "ipsum lorem2"}
        response = self.client.patch(
            self.detail_url, data=data, format="json", HTTP_AUTHORIZATION=self.get_http_authorization()
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # checking the changed properties
        self.resource.your_problem_notes = data["your_problem_notes"]
        self.assertEligibilityCheckEqual(response.data, self.resource)
        self.assertTrue(response.data["notes"] != data["notes"])

    def test_empty_fields(self):
        """
        When patching a NullBooleanField setting it to None, DRF saves it
        as None value.
        """
        data = {
            "category": None,
            "dependants_old": None,
            "dependants_young": None,
            "has_partner": None,
            "is_you_or_your_partner_over_60": None,
            "notes": "",
            "on_nass_benefits": None,
            "on_passported_benefits": None,
            "partner": None,
            "property_set": [],
            "state": "unknown",
            "you": None,
            "disputed_savings": None,
            "your_problem_notes": "",
        }
        response = self.client.patch(
            self.detail_url, data=data, format="json", HTTP_AUTHORIZATION=self.get_http_authorization()
        )
        # TODO: needs more checks

        self.assertEqual(response.data["has_partner"], None)
        self.assertEqual(response.data["is_you_or_your_partner_over_60"], None)

    def test_check_validate_api_method_works(self):
        # actual testing of 'validate' is done in model tests.
        response = self.client.get(
            self.detail_url + "validate/", {}, format="json", HTTP_AUTHORIZATION=self.get_http_authorization()
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data, {"warnings": {}})

    def test_in_category_skip_income_check_when_category_is_family_public_law(self):
        data = {
            "current_node_id": "n103",
            "state": "INSCOPE",
            "category": make_recipe(
                "legalaid.category", name="Family, marriage, separation and children", code="family"
            ),
            "nodes": r"""
                [{
                    "data_safety": null,
                    "title": "Family",
                    "id": "n97",
                    "label": "<p>Family</p>",
                    "context": null,
                    "help_text": "",
                    "heading": null,
                    "order": 3
                }, {
                    "data_safety": null,
                    "title": "Public law\n",
                    "label": "",
                    "context": null,
                    "help_text": "",
                    "order": 2,
                    "heading": null,
                    "id": "n102"
                }, {
                    "data_safety": null,
                    "title": "None of the above, a",
                    "id": "n333",
                    "context": null,
                    "help_text": null,
                    "label": "",
                    "heading": null,
                    "order": 9999
                }, {
                    "data_safety": null,
                    "title": "INSCOPE",
                    "id": "n103",
                    "context": {
                        "category": "family"
                    },
                    "help_text": null,
                    "label": "<p>INSCOPE</p>",
                    "heading": null,
                    "order": 9999
                }]
        """,
        }
        diagnosis = make_recipe("diagnosis.diagnosis_yes", **data)
        self.parent_resource.diagnosis = diagnosis
        make_recipe("diagnosis.diagnosis_yes").save()

        data = {
            "category": data["category"].code,
            "your_problem_notes": "lorem",
            "has_partner": random.choice([None, True, False]),
            "is_you_or_your_partner_over_60": random.choice([None, True, False]),
            "on_passported_benefits": random.choice([None, True, False]),
            "specific_benefits": None,
            "case_reference": self.parent_resource.reference,
        }
        response = self._create(data=data)
        self.assertEqual(response.data["in_category_skip_income_check"], True)

    def test_in_category_skip_income_check_category_category_is_not_family_public_law(self):
        data = {
            "state": "INSCOPE",
            "category": make_recipe(
                "legalaid.category", name="Family, marriage, separation and children", code="family"
            ),
            "nodes": """
            [{
                "data_safety": null,
                "title": "Family",
                "id": "n97",
                "label": "<p>Family</p>",
                "context": null,
                "help_text": "",
                "heading": null,
                "order": 3
            }, {
                "data_safety": null,
                "title": "Client wants to prev",
                "label": "",
                "order": 1,
                "heading": null,
                "id": "n307"
            }, {
                "data_safety": null,
                "title": "Client being harassed by partner or ex-partner",
                "id": "n209",
                "context": null,
                "help_text": "",
                "label": "",
                "heading": null,
                "order": 3
            }, {
                "data_safety": null,
                "title": "INSCOPE",
                "id": "n210",
                "context": {
                    "category": "family"
                },
                "help_text": null,
                "label": "<p>INSCOPE</p>",
                "heading": null,
                "order": 9999
            }]
""",
        }
        diagnosis = make_recipe("diagnosis.diagnosis_yes", **data)
        self.parent_resource.diagnosis = diagnosis
        make_recipe("diagnosis.diagnosis_yes").save()

        data = {
            "category": data["category"].code,
            "your_problem_notes": "lorem",
            "has_partner": random.choice([None, True, False]),
            "is_you_or_your_partner_over_60": random.choice([None, True, False]),
            "on_passported_benefits": random.choice([None, True, False]),
            "specific_benefits": None,
        }
        response = self._create(data=data)
        self.assertEqual(response.data["in_category_skip_income_check"], False)
