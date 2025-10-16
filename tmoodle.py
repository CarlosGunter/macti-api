import asyncio
from app.modules.auth.services.moodle_service import MoodleService

async def test_create_moodle_user():
    user_data = {
        "email": "ekemplo@rjrmplo.com",
        "name": "Pedro",
        "last_name": "Ramírez",
        "password": "Kubioevato_!!",
        "course_id": 2 
    }
    result = await MoodleService.create_user(user_data)
    print("Resultado creación usuario Moodle:", result)

    if result.get("created"):
        moodle_user_id = result.get("id") or result.get("userid")
        print(f"Usuario Moodle creado con ID: {moodle_user_id}")
        enroll_result = await MoodleService.enroll_user(user_id=moodle_user_id, course_id=user_data["course_id"])
        print("Resultado inscripción al curso:", enroll_result)
    else:
        print("Error creando usuario:", result.get("error"))
if __name__ == "__main__":
    asyncio.run(test_create_moodle_user())
