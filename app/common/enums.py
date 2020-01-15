from enumfields import Enum


class CatalistGender(Enum):
    MALE = "male"
    FEMALE = "female"
    UNKNOWN = "unknown"


class VoterStatus(Enum):
    ACTIVE = "registered"
    INACTIVE = "inactive"
    MULTIPLE_APPEARANCES = "multiple_appearances"
    UNREGISTERED = "unregistered"
    UNMATCHED_MEMBER = "unmatched_member"
