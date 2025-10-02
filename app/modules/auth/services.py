"""
This module contains services for integrating with external APIs.
"""

import os
import httpx


class KeycloakService:
    """
    Service for interacting with Keycloak Identity Provider API
    """
    @staticmethod
    async def create_user(user_data):
        """
        Create a user in Keycloak
        To be implemented with actual API calls
        """
        # Example implementation to be replaced with actual API calls
        return {"id": "kc-123", "created": True}
    
    @staticmethod
    async def get_user(user_id):
        """
        Get a user from Keycloak by ID
        To be implemented with actual API calls
        """
        # Example implementation to be replaced with actual API calls
        return {"id": user_id, "username": "example", "status": "active"}


class MoodleService:
    """
    Service for interacting with Moodle LMS API
    """
    MOODLE_URL = os.getenv("MOODLE_URL", "http://localhost/moodle")
    MOODLE_TOKEN = os.getenv("MOODLE_TOKEN")

    @staticmethod
    async def create_user(user_data):
        """
        Create a user in Moodle using the REST API.
        """
        endpoint = f"{MoodleService.MOODLE_URL}/webservice/rest/server.php"
        params = {
            "wstoken": MoodleService.MOODLE_TOKEN,
            "wsfunction": "core_user_create_users",
            "moodlewsrestformat": "json",
        }

        print("DEBUG user_data sent to Moodle:", user_data)

        # Required fields for Moodle user creation
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

        # Return the created user object with a "created" flag
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

        # Required fields for manual enrollment (roleid 5 = student)
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
            # Special case: Moodle sometimes fails only when sending email,
            # but the enrollment is still successful
            if result.get("message") == "error/Message was not sent.":
                print("Moodle could not send email, but the user was enrolled anyway")
                return {"user_id": user_id, "course_id": course_id, "enrolled": True, "warning": result}
            raise Exception(f"Error enrolling user in Moodle: {result}")

        return {"user_id": user_id, "course_id": course_id, "enrolled": True}
