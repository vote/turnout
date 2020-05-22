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
        NON_BINARY = "Non-binary"


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
    MX = "Mx"

    class Labels:
        MR = "Mr."
        MRS = "Mrs."
        MS = "Ms."
        MISS = "Miss"
        MX = "Mx."


class TurnoutActionStatus(Enum):
    INCOMPLETE = "Incomplete"
    PENDING = "Pending"
    PDF_SENT = "SentPDF"
    OVR_REFERRED = "ReferOVR"

    class Labels:
        INCOMPLETE = "Incomplete"
        PENDING = "Pending"
        PDF_SENT = "PDF Sent"
        OVR_REFERRED = "OVR Referred"


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
    ABSENTEE_REQUEST_FORM = "AbsForm"
    REPORT = "Report"

    class Labels:
        REGISTRATION_FORM = "Registration Form"
        ABSENTEE_REQUEST_FORM = "Absentee Request Form"


class EventType(Enum):
    START = "Start"
    FINISH_SELF_PRINT = "FinishPrint"
    FINISH_EXTERNAL = "FinishExternal"
    FINISH_LEO = "FinishLEO"
    FINISH = "Finish"
    DOWNLOAD = "Download"
    DONATE = "Donate"

    class Labels:
        START = "Started Form"
        FINISH_SELF_PRINT = "Finished via Print and Mail"
        FINISH_EXTERNAL = "Finished with External Tool"
        FINISH_LEO = "Finish via direct LEO submission"
        FINISH = "Completed Action"
        DOWNLOAD_PDF = "Downloaded File"
        DONATE_CLICK = "Donate Click"


class SecureUploadType(Enum):
    SIGNATURE = "Signature"


class MessageDirectionType(Enum):
    IN = "in"
    OUT = "out"


class ToolName(Enum):
    VERIFY = "verify"
    REGISTER = "register"
    ABSENTEE = "absentee"
    LOCATE = "locate"
    LEO = "leo"

    class Labels:
        VERIFY = "Verify"
        REGISTER = "Register"
        ABSENTEE = "Vote-By-Mail"
        LOCATE = "Locate"
        LEO = "LEO"


class ReportType(Enum):
    VERIFY = "verify"
    REGISTER = "register"
    ABSENTEE = "absentee"

    class Labels:
        VERIFY = "Verify Tool Export"
        REGISTER = "Register Tool Export"
        ABSENTEE = "Absentee Tool Export"


class ReportStatus(Enum):
    PENDING = "Pending"
    COMPLETE = "Complete"
