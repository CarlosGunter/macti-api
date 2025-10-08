"""
Service for interacting with Moodle LMS API
"""

import os
import httpx
from dotenv import load_dotenv
load_dotenv()

class MoodleService:
    MOODLE_URL = os.getenv("MOODLE_URL")
    MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")
    #supongo tengo que meter los datos que nos paso fer, entrar a mi cuenta y sacar mi token jaja como en kayklok
    #Adecuaré esta parte de la url y token en core/config, para tenerlo más ordenado
    #me sale un error de httpx pero ya lo reviso mañana
    @staticmethod
    async def create_user(user_data):
        """
        Create a user in Moodle using the REST API (debug version).
        """
        print({
            "MoodleService.MOODLE_TOKEN": MoodleService.MOODLE_TOKEN,
            "MoodleService.MOODLE_URL": MoodleService.MOODLE_URL
        })
        
        endpoint = MoodleService.MOODLE_URL  # Ya incluye http://
        params = {
            "wstoken": MoodleService.MOODLE_TOKEN,
            "wsfunction": "core_user_create_users",
            "moodlewsrestformat": "json",
        }

        print("DEBUG user_data sent to Moodle:", user_data)

        data = {
            "users[0][username]": user_data["email"].split("@")[0],
            "users[0][password]": user_data.get("password", "Password1234"),  # más simple para debug
            "users[0][firstname]": user_data.get("name", "User"),
            "users[0][lastname]": user_data.get("last_name", "NA"),
            "users[0][email]": user_data["email"],
            "users[0][auth]": "manual",       # a veces es obligatorio
            "users[0][country]": "MX",        # a veces es obligatorio
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(endpoint, params=params, data=data)
            print("Raw Moodle response:", response.text)  # <--- imprime TODO lo que devuelve Moodle
            response.raise_for_status()
            try:
                result = response.json()
            except Exception as e:
                print(f"ERROR: Respuesta exitosa pero no es JSON: {e}")
                raise RuntimeError(f"Moodle returned success status but non-JSON data: {response.text[:200]}")
        if isinstance(result, dict) and "exception" in result:
            print("Moodle API returned an exception:", result)
            return {"error": result, "created": False}
        return {**result[0], "created": True} if isinstance(result, list) else {"result": result, "created": True}

    @staticmethod
    async def enroll_user(user_id, course_id):
        """
        Enroll a user in a Moodle course using the REST API.
        """
        endpoint = MoodleService.MOODLE_URL
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
