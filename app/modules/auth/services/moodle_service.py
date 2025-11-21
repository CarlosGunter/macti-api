"""
Service for interacting with Moodle LMS API
"""

from app.shared.config.moodle_configs import MOODLE_CONFIG
from app.shared.enums.institutes_enum import InstitutesEnum
from app.shared.services.moodle_client import make_moodle_request


class MoodleService:
    @staticmethod
    async def create_user(user_data, institute: InstitutesEnum):
        """
        Create a user in Moodle using the REST API.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "core_user_create_users",
            "moodlewsrestformat": "json",
        }

        data = {
            "users[0][username]": user_data["email"],
            "users[0][firstname]": user_data.get("name", "User"),
            "users[0][lastname]": user_data.get("last_name", "NA"),
            "users[0][email]": user_data["email"],
            "users[0][auth]": "oauth2",
        }

        print("DEBUG user_data sent to Moodle:", user_data)

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
            check_moodle_errors=False,
        )

        if not result_response["success"]:
            return {
                "created": False,
                "error": f"Moodle Error de petición: {result_response['error_message']}",
            }

        result = result_response["data"]

        print("DEBUG Moodle response (create_user):", result)

        if isinstance(result, dict) and "exception" in result:
            return {"created": False, "error": result}

        return {**result[0], "created": True}

    @staticmethod
    async def enroll_user(user_id, course_id, institute: InstitutesEnum):
        """
        Enroll a user in a Moodle course using the REST API.
        """
        config = MOODLE_CONFIG[institute]
        endpoint = config.moodle_url
        params = {
            "wstoken": config.moodle_token,
            "wsfunction": "enrol_manual_enrol_users",
            "moodlewsrestformat": "json",
        }

        data = {
            "enrolments[0][roleid]": 5,
            "enrolments[0][userid]": user_id,
            "enrolments[0][courseid]": course_id,
            "enrolments[0][timestart]": 0,
            "enrolments[0][timeend]": 0,
            "enrolments[0][suspend]": 0,
        }

        result_response = await make_moodle_request(
            url=endpoint,
            params=params,
            data=data,
            institute=institute,
            check_moodle_errors=False,
        )

        if not result_response["success"]:
            raise Exception(
                f"Error en petición a Moodle: {result_response['error_message']}"
            )

        result = result_response["data"]

        print("DEBUG Moodle response (enroll_user):", result)

        if isinstance(result, dict) and "exception" in result:
            if result.get("message") == "error/Message was not sent.":
                print("Moodle could not send email, but the user was enrolled anyway")
                return {
                    "user_id": user_id,
                    "course_id": course_id,
                    "enrolled": True,
                    "warning": result,
                }
            raise Exception(f"Error enrolling user in Moodle: {result}")

        return {"user_id": user_id, "course_id": course_id, "enrolled": True}
