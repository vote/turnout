from enumfields import Enum


class TargetSmartGender(Enum):
    MALE = "Male"
    FEMALE = "Female"
    UNKNOWN = "Unknown Gender"


class VoterStatus(Enum):
    ACTIVE = "Active"
    INACTIVE = "Inactive"
    UNKNOWN = "Unknown"
