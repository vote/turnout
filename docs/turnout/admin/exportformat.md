# Export File Format

This document contains the column names and descriptions for available exports from the administrative interface of VoteAmerica's toolset.

As not every state has the same field requirements, not every method of completion in every state will collect all columns, and it is possible for users to perform many completions during 1 session, many columns will be blank in live exports.


## Absentee Tool Export Format

|Column Title|Description|
| ---- | ---- |
|ID|The ID we store internally for the ballot request|
|Subscriber|The name of the subscriber|
|Time Started (UTC)|The date and time that the first page of the ballot request was submitted, in UTC|
|First Name|The user's first name|
|Middle Name|The user's middle name|
|Last Name|The user's last name|
|Suffix|The user's name suffix|
|Date of Birth|The user's date of birth|
|Email|The user's email address|
|Phone|The user's phone number|
|Address 1|The user's address1|
|Address 2|The user's address2|
|City|The user's city|
|Zipcode|The user's zipcode|
|State|The user's state|
|Mailing Address 1|The user's mailing address1|
|Mailing Address 2|The user's mailing address2|
|Mailing City|The user's mailing city|
|Mailing State|The user's mailing state|
|Mailing Zipcode|The user's mailing zipcode|
|VoteAmerica SMS Opt In|True/False if the user has selected to opt-in to VoteAmerica's SMS list (always True)|
|Subscriber SMS Opt In|True/False if the user has selected to opt-in to the subscriber's SMS list|
|Completed|If the user has (1) clicked a link to visit their state's online ballot request portal, (2) had their ballot request submitted to their Local Election Official, and/or (3) emailed themselves a ballot request form and downloaded it at least once|
|PDF Emailed to Voter|If the user has emailed themselves a printable customized ballot request form|
|Redirected To State Website|If the user clicked a link to visit their state's ballot request portal|
|PDF submitted to LEO|If VoteAmerica's toolset directly submitted the ballot request to the user's Local Election Official|
|PDF Download Count|For users who have emailed themselves a ballot request form, the number of times they clicked "download" in their email|
|source|The ?source= query param|
|utm_source|The ?utm_source= query param|
|utm_medium|The ?utm_medium= query param|
|utm_campaign|The ?utm_campaign= query param|
|utm_content|The ?utm_content= query param|
|utm_term|The ?utm_term= query param|
|Embed URL|For submissions done inside an embed, the URL of the embed|
|Session ID|The ID of a user's session. For tracking users across multiple tools or visits.|


## Register Tool Export Format

|Column Title|Description|
| ---- | ---- |
|ID|The ID we store internally for the registration|
|Subscriber|The name of the subscriber|
|Time Started (UTC)|The time that the first page of the registration was submitted|
|Previous Title|The previous title the user had|
|Previous First Name|The previous first name the user had|
|Previous Middle Name|The previous middle name the user had|
|Previous Last Name|The previous last name the user had|
|Previous Suffix|The suffix the user previously held|
|Title|The user's title|
|First Name|The user's first name|
|Middle Name|The user's middle name|
|Last Name|The user's last name|
|Suffix|The user's name suffix|
|Date of Birth|The user's date of birth|
|Gender|The user's gender|
|Race-Ethnicity|The user's race-ethnicity|
|US Citizen|True/False if the user indicated they are a US Citizen (should always be True)|
|Party|The user's selected political party|
|Email|The user's email address|
|Phone|The user's phone number|
|Address 1|The user's address1|
|Address 2|The user's address2|
|City|The user's city|
|Zipcode|The user's zipcode|
|State|The user's state|
|Previous Address 1|The user's previous address1|
|Previous Address 2|The user's previous address2|
|Previous City|The user's previous city|
|Previous State|The user's previous state|
|Previous Zipcode|The user's previous zipcode|
|Mailing Address 1|The user's mailing address1|
|Mailing Address 2|The user's mailing address2|
|Mailing City|The user's mailing city|
|Mailing State|The user's mailing state|
|Mailing Zipcode|The user's mailing zipcode|
|VoteAmerica SMS Opt In|True/False if the user has selected to opt-in to VoteAmerica's SMS list (always True)|
|Subscriber SMS Opt In|True/False if the user has selected to opt-in to the subscriber's SMS list|
|Completed|If the user has (1) clicked a link to visit their state's online registration portal, (2) had their registration submitted to their Local Election Official, and/or (3) emailed themselves a registration form and downloaded it at least once|
|PDF Emailed to Voter|If the user has emailed themselves a printable registration form|
|Redirected To State Website|If the user clicked a link to visit their state's online registration portal|
|PDF Submitted to LEO|If VoteAmerica's toolset directly submitted the registration to the user's Local Election Official|
|Total Self Print Downloads|For users who have emailed themselves a registration form, the number of times they clicked "download" in their email|
|source|The ?source= query param|
|utm_source|The ?utm_source= query param|
|utm_medium|The ?utm_medium= query param|
|utm_campaign|The ?utm_campaign= query param|
|utm_content|The ?utm_content= query param|
|utm_term|The ?utm_term= query param|
|Embed URL|For submissions done inside an embed, the URL of the embed|
|Session ID|The ID of a user's session. For tracking users across multiple tools or visits.|
|Referring Tool|For users who were linked to the register tool by another tool, perhaps after they found out they were not registered via the verify tool, the name of the tool|


## Verify Tool Export Format

|Column Title|Description|
| ---- | ---- |
|Current Header Name|Human description of field|
|ID|The ID we store internally for the verification|
|Subscriber|The name of the subscriber|
|Time Started (UTC)|The time that the first page of the verification was done|
|First Name|The user's first name|
|Last Name|The user's last name|
|Date of Birth|The date of birth of the user|
|Email|The email address of the user|
|Phone|The phone number of the user|
|Address 1|The user's Address1|
|Address 2|The user's Address2|
|City|The user's city|
|Zipcode|The user's zipcode|
|State|The user's state|
|VoteAmerica SMS Opt In|True/False if the user opted into VoteAmerica's SMS list (always True)|
|Subscriber SMS Opt In|True/False if the user opted into the subscriber's SMS list|
|Registered|True/False if VoteAmerica's data provider indicated that the user has an active registration|
|source|The ?source= query param|
|utm_source|The ?utm_source= query param|
|utm_medium|The ?utm_medium= query param|
|utm_campaign|The ?utm_campaign= query param|
|utm_content|The ?utm_content= query param|
|utm_term|The ?utm_term= query param|
|Embed URL|For submissions done inside an embed, the URL of the embed|
|Session ID|The ID of a user's session. For tracking users across multiple tools or visits.|
