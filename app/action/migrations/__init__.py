"""
The code to drop/recreate the view is in a separate file to allow usage elsewhere
"""

ACTIONDETAIL_VIEW_CREATION_SQL = """
CREATE OR REPLACE VIEW action_actiondetails AS
SELECT
  a.uuid AS action_id,
  COALESCE( bool_or(generic_finish.event_exists), bool_or(finish_external.event_exists), bool_or(finish_leo.event_exists), bool_or(download.event_exists) ) IS NOT NULL AS finished,
  bool_or(finish_self_print.event_exists) IS NOT NULL AS self_print,
  bool_or(finish_external.event_exists) IS NOT NULL AS finish_external,
  bool_or(finish_leo.event_exists) IS NOT NULL AS finish_leo,
  CASE
    WHEN
      bool_or(finish_self_print.event_exists)
    THEN
      COUNT(download.action_id)
    ELSE
      NULL
  END
  AS download_count
FROM
  action_action a
  LEFT JOIN
    (
      SELECT
        action_id,
        TRUE AS event_exists
      FROM
        event_tracking_event e
      WHERE
        e.event_type = 'FinishPrint'
    )
    finish_self_print
    ON finish_self_print.action_id = a.uuid
  LEFT JOIN
    (
      SELECT
        action_id,
        TRUE AS event_exists
      FROM
        event_tracking_event e
      WHERE
        e.event_type = 'FinishExternal'
    )
    finish_external
    ON finish_external.action_id = a.uuid
  LEFT JOIN
    (
      SELECT
        action_id,
        TRUE AS event_exists
      FROM
        event_tracking_event e
      WHERE
        e.event_type IN ('FinishLEO', 'FinishLEOFaxPending', 'FinishLEOFaxSent', 'FinishLEOFaxFailed')
    )
    finish_leo
    ON finish_leo.action_id = a.uuid
  LEFT JOIN
    (
      SELECT
        action_id,
        TRUE AS event_exists
      FROM
        event_tracking_event e
      WHERE
        e.event_type = 'Finish'
    )
    generic_finish
    ON generic_finish.action_id = a.uuid
  LEFT JOIN
    (
      SELECT
        action_id,
        TRUE AS event_exists
      FROM
        event_tracking_event e
      WHERE
        e.event_type = 'Download'
    )
    download
    ON download.action_id = a.uuid
GROUP BY
  a.uuid;
"""

ACTIONDETAIL_VIEW_REVERSE_SQL = """
DROP VIEW IF EXISTS action_actiondetails;
"""
