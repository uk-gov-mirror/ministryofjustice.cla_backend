COPY (SELECT
id,
created,
modified,
category_id,
code,
description,
level
FROM legalaid_mattertype
WHERE modified >= %s::timestamp AND modified <= %s::timestamp)
TO STDOUT CSV HEADER;