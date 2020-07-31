{% if flow_type == "ovr_or_print" %}
# {{ state_name }} has online voter registration

We recommend this option: it is the absolute fastest way to register to vote.
However, you can also print and mail a paper form if you'd prefer.

{% if has_ovr_id_requirements %}{{state_infos.id_requirements_ovr}}{% endif %}

{% if state_infos.registration_ovr_directions %}
## Online voter registration instructions

{{ state_infos.registration_ovr_directions }}
{% endif %}
{% elif flow_type == "print_only" %}
# {{ state_name }} requires you to print and mail a form

{{ state_name }} does not have an online voter registration system. VoteAmerica
can help you fill out and mail a paper form.
{% elif flow_type == "ineligible" %}
# Sorry, {{ state_name }} doesn't let people register to vote online

{{ state_infos.registration_directions }}
{% endif %}
