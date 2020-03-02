from enumfields import Enum


class TargetSmartGender(Enum):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown Gender"


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
