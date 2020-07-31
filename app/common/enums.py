# We explicitly mark the metaclass as EnumMeta for mypy
from enum import EnumMeta

from enumfields import Enum


class TargetSmartGender(Enum, metaclass=EnumMeta):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown Gender"


class RegistrationGender(Enum, metaclass=EnumMeta):
    MALE = "Male"
    FEMALE = "Female"
    NON_BINARY = "NonBinary"
    OTHER = "Other"

    class Labels:
        NON_BINARY = "Non-binary"


class PoliticalParties(Enum, metaclass=EnumMeta):
    NONE = "None"
    DEMOCRATIC = "Democratic"
    REPUBLICAN = "Republican"
    GREEN = "Green"
    LIBERTARIAN = "Libertarian"
    OTHER = "Other"


class RaceEthnicity(Enum, metaclass=EnumMeta):
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


class PersonTitle(Enum, metaclass=EnumMeta):
    MR = "Mr"
    MRS = "Mrs"
    MISS = "Miss"
    MS = "Ms"
    MX = "Mx"

    def guess_registration_gender(self):
        if self == PersonTitle.MR:
            return RegistrationGender.MALE
        elif self in [PersonTitle.MRS, PersonTitle.MISS, PersonTitle.MS]:
            return RegistrationGender.FEMALE
        else:
            return None

    class Labels:
        MR = "Mr."
        MRS = "Mrs."
        MS = "Ms."
        MISS = "Miss"
        MX = "Mx."


class TurnoutActionStatus(Enum, metaclass=EnumMeta):
    INCOMPLETE = "Incomplete"
    PENDING = "Pending"
    PDF_SENT = "SentPDF"
    OVR_REFERRED = "ReferOVR"

    class Labels:
        INCOMPLETE = "Incomplete"
        PENDING = "Pending"
        PDF_SENT = "PDF Sent"
        OVR_REFERRED = "OVR Referred"


class VoterStatus(Enum, metaclass=EnumMeta):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    UNKNOWN = "Unknown"


class StateFieldFormats(Enum, metaclass=EnumMeta):
    MARKDOWN = "Markdown"
    BOOLEAN = "Boolean"
    URL = "URL"
    DATE = "Date"

    class Labels:
        MARKDOWN = "Markdown"
        BOOLEAN = "Boolean"
        URL = "URL"
        DATE = "Date"


class NotificationWebhookTypes(Enum, metaclass=EnumMeta):
    NETLIFY = "Netlify"


class FileType(Enum, metaclass=EnumMeta):
    REGISTRATION_FORM = "RegForm"
    ABSENTEE_REQUEST_FORM = "AbsForm"
    REPORT = "Report"

    class Labels:
        REGISTRATION_FORM = "Registration Form"
        ABSENTEE_REQUEST_FORM = "Absentee Request Form"


class EventType(Enum, metaclass=EnumMeta):
    START = "Start"
    FINISH_SELF_PRINT = "FinishPrint"
    FINISH_EXTERNAL = "FinishExternal"
    FINISH_EXTERNAL_CONFIRMED = "FinishExternalConfirmed"
    FINISH_LEO = "FinishLEO"
    FINISH_LEO_FAX_PENDING = "FinishLEOFaxPending"
    FINISH_LEO_FAX_SENT = "FinishLEOFaxSent"
    FINISH_LEO_FAX_FAILED = "FinishLEOFaxFailed"
    FINISH = "Finish"
    DOWNLOAD = "Download"
    DONATE = "Donate"
    RESTART = "Restart"

    class Labels:
        START = "Started Form"
        FINISH_SELF_PRINT = "Finished via Print and Mail"
        FINISH_EXTERNAL = "Finished with External Tool"
        FINISH_EXTERNAL_CONFIRMED = (
            "Finished with External Tool And Confirmed Completion"
        )
        FINISH_LEO = "Finish via direct LEO email submission"
        FINISH_LEO_FAX_PENDING = "Finish via direct LEO fax submission (fax pending)"
        FINISH_LEO_FAX_SENT = "Finish via direct LEO fax submission (fax sent)"
        FINISH_LEO_FAX_FAILED = "LEO fax submission failed"
        FINISH = "Completed Action"
        DOWNLOAD_PDF = "Downloaded File"
        DONATE_CLICK = "Donate Click"
        RESTART = "Restarted Flow"


class SecureUploadType(Enum, metaclass=EnumMeta):
    SIGNATURE = "Signature"


class MessageDirectionType(Enum, metaclass=EnumMeta):
    IN = "in"
    OUT = "out"


class ToolName(Enum, metaclass=EnumMeta):
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


class ReportType(Enum, metaclass=EnumMeta):
    VERIFY = "verify"
    REGISTER = "register"
    ABSENTEE = "absentee"

    class Labels:
        VERIFY = "Verify Tool Export"
        REGISTER = "Register Tool Export"
        ABSENTEE = "Absentee Tool Export"


class ReportStatus(Enum, metaclass=EnumMeta):
    PENDING = "Pending"
    COMPLETE = "Complete"


class FaxStatus(Enum, metaclass=EnumMeta):
    PENDING = "pending"
    SENT = "sent"
    TEMPORARY_FAILURE = "tmp_fail"
    PERMANENT_FAILURE = "perm_fail"


class SubmissionType(Enum, metaclass=EnumMeta):
    LEO_EMAIL = "leo_email"
    LEO_FAX = "leo_fax"
    SELF_PRINT = "self_print"

    class Labels:
        LEO_EMAIL = "Email to LEO"
        LEO_FAX = "Fax to LEO"
        SELF_PRINT = "Print at Home"


class ExternalToolType(Enum, metaclass=EnumMeta):
    ACTIONNETWORK = "actionnetwork"


class SubscriptionInterestStatus(Enum, metaclass=EnumMeta):
    PENDING = "pending"
    SUBSCRIBED = "subscribed"
    AWAITING_PAYMENT = "awaiting_payment"
    REJECTED = "rejected"

    class Labels:
        PENDING = "Pending Review"
        SUBSCRIBED = "Subscribed"
        AWAITING_PAYMENT = "Awaiting Payment"
        REJECTED = "Rejected"


class SubscriberStatus(Enum, metaclass=EnumMeta):
    ACTIVE = "active"
    DISABLED = "disabled"


class ProxyStatus(Enum, metaclass=EnumMeta):
    CREATING = "creating"
    PREPARING = "preparing"
    UP = "up"
    BURNED = "burned"
    DOWN = "down"


class RegistrationFlowType(Enum, metaclass=EnumMeta):
    OVR_OR_PRINT = "ovr_or_print"
    PRINT_ONLY = "print_only"
    INELIGIBLE = "ineligible"
