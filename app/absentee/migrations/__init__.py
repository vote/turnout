DASHBOARD_VIEWS_CREATE_SQL = """
CREATE OR REPLACE VIEW absentee_regionesignmethod AS
SELECT
  region.external_id AS region_id,
  region.state_id,
  absentee_leocontactoverride.region_id IS NOT NULL as has_override,
    CASE
    WHEN override_submission_method = 'self_print' THEN
      'self_print'
    WHEN override_submission_method = 'leo_email' THEN
      CASE WHEN region_data.has_email AND email_allowed.allowed THEN 'leo_email' ELSE 'self_print' END
    WHEN override_submission_method = 'leo_fax' THEN
      CASE WHEN region_data.has_fax AND fax_allowed.allowed THEN 'leo_fax' ELSE 'self_print' END
    ELSE
      -- no override -- fax preferred, then email, based on state law
      CASE
      WHEN email_allowed.allowed AND region_data.has_email THEN
        'leo_email'
      WHEN fax_allowed.allowed AND region_data.has_fax THEN
      	'leo_fax'
      ELSE
      	'self_print'
      END
    END AS submission_method
FROM official_region region

-- region data
LEFT JOIN (
	SELECT
		official_region.external_id,
		MAX(override.submission_method) AS override_submission_method,
		BOOL_OR(
			(COALESCE(official_address.email, '') != '') OR
			(COALESCE(override.email, '') != '')
		) AS has_email,
		BOOL_OR(
			(COALESCE(official_address.fax, '') != '') OR
			(COALESCE(override.fax, '') != '')
		) AS has_fax
	FROM official_region
	LEFT JOIN official_office ON official_office.region_id = official_region.external_id
	LEFT JOIN official_address ON official_address.office_id = official_office.external_id
    LEFT JOIN absentee_leocontactoverride override ON override.region_id = official_region.external_id
	GROUP BY official_region.external_id
) region_data ON region_data.external_id = region.external_id

-- fax_allowed
LEFT JOIN (
  SELECT si.state_id, LOWER(si.text) = 'true' AS allowed
  FROM election_stateinformationfieldtype sift
  JOIN election_stateinformation si ON si.field_type_id = sift.uuid
  WHERE sift.slug = 'vbm_app_submission_fax'
) fax_allowed ON region.state_id =  fax_allowed.state_id

-- email_allowed
LEFT JOIN (
  SELECT si.state_id, LOWER(si.text) = 'true' AS allowed
  FROM election_stateinformationfieldtype sift
  JOIN election_stateinformation si ON si.field_type_id = sift.uuid
  WHERE sift.slug = 'vbm_app_submission_email'
) email_allowed ON region.state_id =  email_allowed.state_id

-- overrides
LEFT JOIN absentee_leocontactoverride
	ON absentee_leocontactoverride.region_id = region.external_id
;



CREATE OR REPLACE VIEW absentee_statedashboarddata AS
SELECT
	state.code AS state_id,
	statewide_links.text != '' AS has_statewide_link,
	region_link_count.count AS num_region_links,
	fax_allowed.allowed AS fax_allowed,
	email_allowed.allowed AS email_allowed,
	region_counts.num_regions AS num_regions,
	region_counts.regions_email AS num_regions_email,
	region_counts.regions_fax AS num_regions_fax,
	region_counts.regions_self_print AS num_regions_self_print,
	region_counts.num_overrides AS num_regions_with_override
FROM election_state state

-- has_statewide_link
LEFT JOIN (
  SELECT si.state_id, si.text
  FROM election_stateinformationfieldtype sift
  JOIN election_stateinformation si ON si.field_type_id = sift.uuid
  WHERE sift.slug = 'external_tool_vbm_application'
) statewide_links ON state.code =  statewide_links.state_id

-- num_region_links
LEFT JOIN (
  SELECT
	state.code,
	COUNT(*) FILTER (WHERE absentee_regionovbmlink.url IS NOT NULL)
  FROM election_state state
  LEFT JOIN official_region ON official_region.state_id = state.code
  LEFT JOIN absentee_regionovbmlink ON absentee_regionovbmlink.region_id = official_region.external_id
  GROUP BY state.code
) region_link_count ON state.code = region_link_count.code

-- fax_allowed
LEFT JOIN (
  SELECT si.state_id, LOWER(si.text) = 'true' AS allowed
  FROM election_stateinformationfieldtype sift
  JOIN election_stateinformation si ON si.field_type_id = sift.uuid
  WHERE sift.slug = 'vbm_app_submission_fax'
) fax_allowed ON state.code =  fax_allowed.state_id

-- email_allowed
LEFT JOIN (
  SELECT si.state_id, LOWER(si.text) = 'true' AS allowed
  FROM election_stateinformationfieldtype sift
  JOIN election_stateinformation si ON si.field_type_id = sift.uuid
  WHERE sift.slug = 'vbm_app_submission_email'
) email_allowed ON state.code =  email_allowed.state_id

-- num_regions, regions_*
LEFT JOIN (
  SELECT
	regions.state_id,
	COUNT(*) AS num_regions,
	COUNT(*) FILTER (WHERE submission_method = 'self_print') AS regions_self_print,
	COUNT(*) FILTER (WHERE submission_method = 'leo_email') AS regions_email,
	COUNT(*) FILTER (WHERE submission_method = 'leo_fax') AS regions_fax,
	COUNT(*) FILTER (WHERE has_override IS TRUE) AS num_overrides
  FROM absentee_regionesignmethod regions
  GROUP BY regions.state_id
) region_counts ON state.code = region_counts.state_id;


CREATE OR REPLACE VIEW absentee_esignsubmitstats AS
SELECT
  region.external_id AS region_id,
  region.state_id,
  COALESCE(stats_7d.emails_sent, 0) AS emails_sent_7d,
  COALESCE(stats_7d.faxes_sent, 0) AS faxes_sent_7d,
  COALESCE(stats_1d.emails_sent, 0) AS emails_sent_1d,
  COALESCE(stats_1d.faxes_sent, 0) AS faxes_sent_1d
FROM official_region region
LEFT JOIN (
	SELECT
	  ballotrequest.region_id AS external_id,
	  COUNT(DISTINCT ballotrequest.action_id) FILTER (WHERE event.event_type = 'FinishLEO') AS emails_sent,
	  COUNT(DISTINCT ballotrequest.action_id) FILTER (WHERE event.event_type = 'FinishLEOFaxPending') AS faxes_sent
	FROM absentee_ballotrequest ballotrequest
	JOIN event_tracking_event event ON event.action_id = ballotrequest.action_id
	WHERE event.created_at > NOW() - interval '7 days'
	AND event.event_type IN ('FinishLEO', 'FinishLEOFaxPending')
	GROUP BY ballotrequest.region_id
) stats_7d USING (external_id)
LEFT JOIN (
	SELECT
	  ballotrequest.region_id AS external_id,
	  COUNT(DISTINCT ballotrequest.action_id) FILTER (WHERE event.event_type = 'FinishLEO') AS emails_sent,
	  COUNT(DISTINCT ballotrequest.action_id) FILTER (WHERE event.event_type = 'FinishLEOFaxPending') AS faxes_sent
	FROM absentee_ballotrequest ballotrequest
	JOIN event_tracking_event event ON event.action_id = ballotrequest.action_id
	WHERE event.created_at > NOW() - interval '1 days'
	AND event.event_type IN ('FinishLEO', 'FinishLEOFaxPending')
	GROUP BY ballotrequest.region_id
) stats_1d USING (external_id);
"""

DASHBOARD_VIEWS_DROP_SQL = """
DROP VIEW absentee_regionesignmethod;

DROP VIEW absentee_statedashboarddata;

DROP VIEW absentee_esignsubmitstats;
"""
