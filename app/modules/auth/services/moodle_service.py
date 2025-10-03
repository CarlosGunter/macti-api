"""
Service for interacting with Moodle LMS API
"""

import os
import httpx
from dotenv import load_dotenv
load_dotenv()

class MoodleService:
    MOODLE_URL = os.getenv("http://13.58.33.203/moodle")
    MOODLE_TOKEN = os.getenv("980782459f25a0263c4bc0b8f486f41c ")
    #supongo tengo que meter los datos que nos paso fer, entrar a mi cuenta y sacar mi token jaja como en kayklok
    #Adecuaré esta parte de la url y token en core/config, para tenerlo más ordenado
    #me sale un error de httpx pero ya lo reviso mañana
    @staticmethod
    async def create_user(user_data):
        """
        Create a user in Moodle using the REST API.
        """
        print({
            "MoodleService.MOODLE_TOKEN": MoodleService.MOODLE_TOKEN,
            "MoodleService.MOODLE_URL": MoodleService.MOODLE_URL
        })
        endpoint = f"{MoodleService.MOODLE_URL}/webservice/rest/server.php"
        params = {
            "wstoken": MoodleService.MOODLE_TOKEN,
            "wsfunction": "core_user_create_users",
            "moodlewsrestformat": "json",
        }

        print("DEBUG user_data sent to Moodle:", user_data)

        data = {
            "users[0][username]": user_data["email"].split("@")[0],
            "users[0][password]": user_data.get("password", "Password123!"),
            "users[0][firstname]": user_data.get("name", "User"),
            "users[0][lastname]": user_data.get("last_name", "NA"),
            "users[0][email]": user_data["email"],
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, params=params, data=data)
            response.raise_for_status()
            result = response.json()

        print("DEBUG Moodle response (create_user):", result)

        if isinstance(result, dict) and "exception" in result:
            raise Exception(f"Error creating user in Moodle: {result}")

        return {**result[0], "created": True}

    @staticmethod
    async def enroll_user(user_id, course_id):
        """
        Enroll a user in a Moodle course using the REST API.
        """
        endpoint = f"{MoodleService.MOODLE_URL}/webservice/rest/server.php"
        params = {
            "wstoken": MoodleService.MOODLE_TOKEN,
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

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, params=params, data=data)
            response.raise_for_status()
            result = response.json()

        print("DEBUG Moodle response (enroll_user):", result)

        if isinstance(result, dict) and "exception" in result:
            if result.get("message") == "error/Message was not sent.":
                print("Moodle could not send email, but the user was enrolled anyway")
                return {"user_id": user_id, "course_id": course_id, "enrolled": True, "warning": result}
            raise Exception(f"Error enrolling user in Moodle: {result}")

        return {"user_id": user_id, "course_id": course_id, "enrolled": True}
