from enumfields import Enum

# NB EnumField default max_length=10 in migrations
# Ensure value lengths are at or below max


class TargetSmartGender(Enum):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown Gender"


class RegistrationGender(Enum):
    MALE = "Male"
    FEMALE = "Female"
    NON_BINARY = "NonBinary"
    OTHER = "Other"

    class Labels:
        NON_BINARY = "Non Binary"


class PoliticalParties(Enum):
    NONE = "None"
    DEMOCRATIC = "Democratic"
    REPUBLICAN = "Republican"
    GREEN = "Green"
    LIBERTARIAN = "Libertarian"
    OTHER = "Other"


class RaceEthnicity(Enum):
    AMERICAN_INDIAN_ALASKA_NATIVE = "Native"
    ASIAN_PACIFIC_ISLANDER = "AAPI"
    BLACK = "Black"
    HISPANIC = "Hispanic"
    MULTI = "Multi"
    WHITE = "White"
    OTHER = "Other"

    class Labels:
        AMERICAN_INDIAN_ALASKA_NATIVE = "American Indian / Alaskan Native"
        ASIAN_PACIFIC_ISLANDER = "Asian / Pacific Islander"
        BLACK = "Black (not Hispanic)"
        MULTI = "Multi Racial"
        WHITE = "White (not Hispanic)"


class PersonTitle(Enum):
    MR = "Mr"
    MRS = "Mrs"
    MISS = "Miss"
    MS = "Ms"

    class Labels:
        MR = "Mr."
        MRS = "Mrs."
        MS = "Ms."


class TurnoutRegistrationStatus(Enum):
    INCOMPLETE = "Incomplete"
    PENDING = "Pending"
    PDF_SENT = "SentPDF"
    OVR_REFERRED = "ReferOVR"

    class Labels:
        INCOMPLETE = "Incomplete"
        PENDING = "Pending"
        PDF_SENT = "PDF Sent"
        OVR_REFERRED = "OVR Referred"


class TurnoutBallotRequestStatus(Enum):
    INCOMPLETE = "Incomplete"
    PENDING = "Pending"


class VoterStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    UNKNOWN = "Unknown"


class StateFieldFormats(Enum):
    MARKDOWN = "Markdown"
    BOOLEAN = "Boolean"
    URL = "URL"
    DATE = "Date"

    class Labels:
        MARKDOWN = "Markdown"
        BOOLEAN = "Boolean"
        URL = "URL"
        DATE = "Date"


class NotificationWebhookTypes(Enum):
    NETLIFY = "Netlify"


class FileType(Enum):
    REGISTRATION_FORM = "RegForm"

    class Labels:
        REGISTRATION_FORM = "Registration Form"


class EventType(Enum):
    OFFICIAL_TOOL_VISIT = "OToolVisit"
