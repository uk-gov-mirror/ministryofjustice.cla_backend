import os
from contextlib import closing

from celery import shared_task

from reports.utils import OBIEEExporter, email_obiee_export


@shared_task(bind=True)
def obiee_export(self, diversity_keyphrase, dt_from, dt_to):
    """
    Export a full dump of the db for OBIEE export and email it to
    the address specified in the environment as OBIEE_EMAIL_TO.
    It can be a comma separated list of email addresses

    :param diversity_keyphrase: the paraphrase required to unlock the encrypted
    diversity fields
    :type diversity_keyphrase: str or unicode
    :param dt_from: the date to start the export from
    :type dt_from: datetime.datetime
    :param dt_to: end date for the export
    :type dt_to: datetime.datetime
    """
    temp_path = os.path.join('/tmp/', self.request.id)
    os.mkdir(temp_path)
    with closing(OBIEEExporter(temp_path, diversity_keyphrase,
                  dt_from, dt_to)) as exporter:
        zip_path = exporter.export()

        email_obiee_export(zip_path, dt_from, dt_to)