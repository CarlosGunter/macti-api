from pydantic import BaseModel, ConfigDict


class CourseResponseSchema(BaseModel):
    id: int
    shortname: str
    fullname: str
    displayname: str
    summary: str
    timecreated: int

    # Para ORM
    model_config = ConfigDict(from_attributes=True)


ListCoursesResponse = list[CourseResponseSchema]
