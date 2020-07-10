"""
The code to drop/recreate the view is in a separate file to allow usage elsewhere
"""

VIEW_CREATE_SQL = """
CREATE OR REPLACE VIEW reporting_ballotrequestreport AS
SELECT
    br.uuid,
    subscriber.name AS subscriber_name,
    subscriber.uuid AS subscriber_id,
    br.created_at,
    CASE
        WHEN action_details.latest_event > br.modified_at THEN action_details.latest_event
        ELSE br.modified_at
    END AS updated_at,
    br.first_name,
    br.middle_name,
    br.last_name,
    br.suffix,
    br.date_of_birth,
    br.email,
    br.phone,
    br.address1,
    br.address2,
    br.city,
    br.zipcode,
    br.state_id,
    br.mailing_address1,
    br.mailing_address2,
    br.mailing_city,
    br.mailing_state_id,
    br.mailing_zipcode,
    br.sms_opt_in,
    br.sms_opt_in_partner AS sms_opt_in_subscriber,
    br.source,
    br.utm_source,
    br.utm_medium,
    br.utm_campaign,
    br.utm_content,
    br.utm_term,
    br.embed_url,
    br.session_id,
    action_details.finished,
    action_details.self_print,
    action_details.finish_external AS finished_external_service,
    action_details.finish_leo AS leo_message_sent,
    action_details.download_count AS total_downloads
FROM
    absentee_ballotrequest br
LEFT JOIN multi_tenant_client subscriber ON br.partner_id = subscriber.uuid
LEFT JOIN action_actiondetails action_details ON br.action_id = action_details.action_id;


CREATE OR REPLACE VIEW reporting_registerreport AS
SELECT
    reg.uuid,
    subscriber.name AS subscriber_name,
    subscriber.uuid AS subscriber_id,
    reg.created_at,
    CASE
        WHEN action_details.latest_event > reg.modified_at THEN action_details.latest_event
        ELSE reg.modified_at
    END AS updated_at,
    reg.previous_title,
    reg.previous_first_name,
    reg.previous_middle_name,
    reg.previous_last_name,
    reg.previous_suffix,
    reg.title,
    reg.first_name,
    reg.middle_name,
    reg.last_name,
    reg.suffix,
    reg.date_of_birth,
    reg.gender,
    reg.race_ethnicity,
    reg.us_citizen,
    reg.party,
    reg.email,
    reg.phone,
    reg.address1,
    reg.address2,
    reg.city,
    reg.zipcode,
    reg.state_id,
    reg.previous_address1,
    reg.previous_address2,
    reg.previous_city,
    reg.previous_state_id,
    reg.previous_zipcode,
    reg.mailing_address1,
    reg.mailing_address2,
    reg.mailing_city,
    reg.mailing_state_id,
    reg.mailing_zipcode,
    reg.sms_opt_in,
    reg.sms_opt_in_partner AS sms_opt_in_subscriber,
    reg.source,
    reg.utm_source,
    reg.utm_medium,
    reg.utm_campaign,
    reg.utm_content,
    reg.utm_term,
    reg.embed_url,
    reg.session_id,
    reg.referring_tool,
    action_details.finished,
    action_details.self_print,
    action_details.finish_external AS finished_external_service,
    action_details.finish_leo AS leo_message_sent,
    action_details.download_count AS total_downloads
FROM
    register_registration reg
LEFT JOIN multi_tenant_client subscriber ON reg.partner_id = subscriber.uuid
LEFT JOIN action_actiondetails action_details ON reg.action_id = action_details.action_id;


CREATE OR REPLACE VIEW reporting_verifyreport AS
SELECT
    ver.uuid,
    subscriber.name AS subscriber_name,
    subscriber.uuid AS subscriber_id,
    ver.created_at,
    ver.modified_at AS updated_at,
    ver.first_name,
    ver.last_name,
    ver.date_of_birth,
    ver.email,
    ver.phone,
    ver.address1,
    ver.address2,
    ver.city,
    ver.zipcode,
    ver.state_id,
    ver.sms_opt_in,
    ver.sms_opt_in_partner AS sms_opt_in_subscriber,
    ver.registered,
    ver.source,
    ver.utm_source,
    ver.utm_medium,
    ver.utm_campaign,
    ver.utm_content,
    ver.utm_term,
    ver.embed_url,
    ver.session_id
FROM
    verifier_lookup ver
LEFT JOIN multi_tenant_client subscriber ON ver.partner_id = subscriber.uuid;
"""

VIEW_DROP_SQL = """
DROP VIEW IF EXISTS reporting_ballotrequestreport;
DROP VIEW IF EXISTS reporting_registerreport;
DROP VIEW IF EXISTS reporting_verifyreport;
"""
