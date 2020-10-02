"""
The code to drop/recreate the view is in a separate file to allow usage elsewhere
"""

ACTIONDETAIL_VIEW_CREATION_SQL = """
CREATE OR REPLACE VIEW action_actiondetails AS
SELECT
  action.uuid AS action_id,
  action.events && ARRAY['Finish', 'FinishExternal', 'FinishExternalAPI', 'FinishExternalConfirmed', 'FinishLEO', 'FinishLEOFaxPending', 'FinishLEOFaxSent', 'FinishLEOFaxFailed', 'Download', 'FinishLobConfirm'] AS finished,
  action.events && ARRAY['FinishPrint'] AS self_print,
  action.events && ARRAY['FinishExternal', 'FinishExternalConfirmed'] AS finish_external,
  action.events && ARRAY['FinishLEO', 'FinishLEOFaxPending', 'FinishLEOFaxSent', 'FinishLEOFaxFailed'] AS finish_leo,
  CASE
    WHEN action.events && ARRAY['FinishPrint']
    THEN download_count
    ELSE NULL
  END AS download_count,
  action.latest_event,
  action.events && ARRAY['FinishLobConfirm'] AS finish_lob
FROM (
	SELECT
	  a.uuid,
	  COALESCE(array_agg(e.event_type) FILTER (WHERE event_type IS NOT NULL), ARRAY[]::text[]) AS events,
	  COALESCE(COUNT(action_id) FILTER (WHERE event_type = 'Download'), 0) AS download_count,
	  MAX(e.modified_at) AS latest_event
	FROM
	  action_action a
	  LEFT JOIN
	    event_tracking_event e
	    ON e.action_id = a.uuid
	GROUP BY a.uuid
) action
"""

ACTIONDETAIL_VIEW_REVERSE_SQL = """
DROP VIEW IF EXISTS action_actiondetails;
"""
