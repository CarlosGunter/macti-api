from dataclasses import dataclass

from app.core.config import Settings

from ..enums.institutes_enum import InstitutesEnum


@dataclass
class DCMoodleConfig:
    moodle_url: str
    moodle_token: str


MOODLE_CONFIG: dict[InstitutesEnum, DCMoodleConfig] = {
    InstitutesEnum.PRINCIPAL: DCMoodleConfig(
        moodle_url="http://13.58.33.203:8080/webservice/rest/server.php",
        moodle_token=Settings.MOODLE_TOKEN_PRINCIPAL,
    ),
    InstitutesEnum.CUANTICO: DCMoodleConfig(
        moodle_url="http://13.58.33.203:8081/webservice/rest/server.php",
        moodle_token=Settings.MOODLE_TOKEN_CUANTICO,
    ),
    InstitutesEnum.CIENCIAS: DCMoodleConfig(
        moodle_url="http://13.58.33.203:8082/webservice/rest/server.php",
        moodle_token=Settings.MOODLE_TOKEN_CIENCIAS,
    ),
    InstitutesEnum.INGENIERIA: DCMoodleConfig(
        moodle_url="http://13.58.33.203:8083/webservice/rest/server.php",
        moodle_token=Settings.MOODLE_TOKEN_INGENIERIA,
    ),
}
