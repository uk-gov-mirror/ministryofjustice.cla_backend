import inspect
import datetime
import os
import shutil
import tempfile

from django.test import TestCase
from psycopg2 import InternalError

from cla_common.constants import CONTACT_SAFETY
from core.tests.mommy_utils import make_recipe
from legalaid.utils.diversity import save_diversity_data
import reports.forms
from reports.utils import OBIEEExporter


class ReportsSQLColumnsMatchHeadersTestCase(TestCase):
    def setUp(self):
        super(ReportsSQLColumnsMatchHeadersTestCase, self).setUp()
        make_recipe("cla_provider.Provider")

    def test_headers_count_matches_sql(self):
        for n, i in vars(reports.forms).items():
            if (
                inspect.isclass(i)
                and issubclass(i, reports.forms.SQLFileDateRangeReport)
                and i != reports.forms.SQLFileDateRangeReport
            ):
                inst = i(data={"date_from": datetime.datetime.now(), "date_to": datetime.datetime.now()})
                inst.is_valid()
                inst.get_queryset()
                len_desc = len(inst.description)
                len_headers = len(inst.get_headers())
                if inst.__class__.__name__ == "MICaseExtract":
                    # this is due to getting multiple fields as 1 json field in sql
                    len_headers = len_headers - 3
                self.assertEqual(
                    len_desc,
                    len_headers,
                    "Number of columns in %s.get_headers() doesn't match the number of columns returned by the sql query."
                    % n,
                )

            if (
                inspect.isclass(i)
                and issubclass(i, reports.forms.SQLFileMonthRangeReport)
                and i != reports.forms.SQLFileMonthRangeReport
            ):
                inst = i(data={"date": datetime.datetime.now()})
                inst.is_valid()
                inst.get_queryset()
                self.assertEqual(
                    len(inst.description),
                    len(inst.get_headers()),
                    "Number of columns in %s.get_headers() doesn't match the number of columns returned by the sql query."
                    % n,
                )


class ReportOrganisationColumnTestCase(TestCase):
    def test_mi_survey_dom1_extract_organisation_column(self):
        pd = make_recipe("legalaid.personal_details", safe_to_contact=CONTACT_SAFETY.SAFE, contact_for_research=True)
        foo_org = make_recipe("call_centre.organisation", name="Foo org")
        bar_org = make_recipe("call_centre.organisation", name="Bar org")
        make_recipe("legalaid.case", personal_details=pd, organisation=foo_org)
        make_recipe("legalaid.case", personal_details=pd, organisation=bar_org)
        data = {"date_from": datetime.datetime.now(), "date_to": datetime.datetime.now()}
        instance = reports.forms.MISurveyExtract(data=data)
        instance.is_valid()
        results = instance.get_queryset()
        self.assertEqual(len(results), 1)

        columns = [column.lower() for column in instance.get_headers()]
        index = columns.index("organisation")
        self.assertEqual("Bar org, Foo org", results[0][index])


class ReportsDateRangeValidationWorks(TestCase):
    def test_valid_date_range(self):
        class T(reports.forms.DateRangeReportForm):
            max_date_range = 5

        now = datetime.datetime.now()
        i = T(data={"date_from": now - datetime.timedelta(days=4), "date_to": now})
        self.assertTrue(i.is_valid())
        self.assertEqual(i.errors.keys(), [])

    def test_invalid_date_range(self):
        class T(reports.forms.DateRangeReportForm):
            max_date_range = 5

        now = datetime.datetime.now()
        i = T(data={"date_from": now - datetime.timedelta(days=5), "date_to": now})
        self.assertFalse(i.is_valid())
        self.assertEqual(i.errors.keys(), ["__all__"])
        self.assertEqual(len(i.errors["__all__"]), 1)
        self.assertIn(
            i.errors[u"__all__"][0],
            [
                u"The date range (6 days, 0:00:00) should span no more than 5 working days",
                u"The date range (6 days, 1:00:00) should span no more than 5 working days",
                u"The date range (5 days, 23:00:00) should span no more than 5 working days",
            ],
        )

    def test_valid_date_range_clocks_going_forward(self):
        class T(reports.forms.DateRangeReportForm):
            max_date_range = 5

        start = datetime.datetime(2019, 3, 29)  # GMT
        end = datetime.datetime(2019, 4, 2)  # BST
        i = T(data={"date_from": start, "date_to": end})
        self.assertTrue(i.is_valid())

    def test_valid_date_range_clocks_going_back(self):
        class T(reports.forms.DateRangeReportForm):
            max_date_range = 5

        start = datetime.datetime(2019, 10, 25)  # BST
        end = datetime.datetime(2019, 10, 29)  # GMT
        i = T(data={"date_from": start, "date_to": end})
        self.assertTrue(i.is_valid())

    def test_invalid_date_range_clocks_going_forward(self):
        class T(reports.forms.DateRangeReportForm):
            max_date_range = 5

        start = datetime.datetime(2019, 3, 29)  # GMT
        end = datetime.datetime(2019, 4, 3)  # BST
        i = T(data={"date_from": start, "date_to": end})
        self.assertFalse(i.is_valid())

    def test_invalid_date_range_clocks_going_back(self):
        class T(reports.forms.DateRangeReportForm):
            max_date_range = 5

        start = datetime.datetime(2019, 10, 25)  # BST
        end = datetime.datetime(2019, 10, 30)  # GMT
        i = T(data={"date_from": start, "date_to": end})
        self.assertFalse(i.is_valid())


class MIDuplicateCasesTestCase(TestCase):
    def test_duplicate_cases(self):
        # random data
        for _ in range(20):
            personal_details = make_recipe(
                "legalaid.personal_details", _fill_optional=["full_name", "date_of_birth", "postcode"]
            )
            make_recipe("legalaid.case", personal_details=personal_details)

        # data with one pair of duplicates
        data = (
            dict(full_name="Mary Smith", date_of_birth=datetime.date(1980, 5, 1), postcode="SW1A 1AA"),
            dict(full_name="Mary Smith", date_of_birth=datetime.date(1975, 4, 10), postcode="SW1A 1AA"),
            dict(full_name="mary smith", date_of_birth=datetime.date(1980, 5, 1), postcode="sw1a1aa"),
        )
        for details in data:
            personal_details = make_recipe("legalaid.personal_details", **details)
            make_recipe("legalaid.case", personal_details=personal_details)

        from legalaid.models import Case

        self.assertEqual(Case.objects.count(), 23)

        form = reports.forms.MIDuplicateCaseExtract(
            data={"date_from": datetime.date.today() - datetime.timedelta(days=1), "date_to": datetime.date.today()}
        )
        self.assertTrue(form.is_valid())
        query_result = form.get_queryset()
        self.assertEqual(len(query_result), 2)
        saved_data = [list(row[-3:]) for row in query_result]
        self.assertListEqual(
            saved_data,
            [
                ["mary smith", datetime.date(1980, 5, 1), "sw1a1aa"],
                ["Mary Smith", datetime.date(1980, 5, 1), "SW1A 1AA"],
            ],
        )


class OBIEEExportOutputsZipTestCase(TestCase):
    def setUp(self):
        self.td = tempfile.mkdtemp()

        # actually test that it works
        self.personal_details = make_recipe("legalaid.personal_details")
        save_diversity_data(self.personal_details.pk, {"test": "test"})
        self.dt_from = datetime.datetime.now() - datetime.timedelta(days=1)
        self.dt_to = datetime.datetime.now() + datetime.timedelta(days=1)

    def test_zip_output(self):
        e = OBIEEExporter(self.td, "cla", dt_from=self.dt_from, dt_to=self.dt_to)
        tmp_path = e.tmp_export_path
        e.export()
        self.assertFalse(os.path.exists(tmp_path))
        self.assertTrue(os.path.isfile(os.path.join("%s/cla_database.zip" % self.td)))

    def test_zip_bad_password(self):
        e = OBIEEExporter(self.td, "wrongpw", dt_from=self.dt_from, dt_to=self.dt_to)
        with self.assertRaises(InternalError):
            e.export()
        self.assertFalse(os.path.isfile(os.path.join("%s/cla_database.zip" % self.td)))

    def tearDown(self):
        if os.path.exists(self.td):
            shutil.rmtree(self.td, ignore_errors=True)
