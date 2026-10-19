from pydantic import BaseModel


class CourseBase(BaseModel):
    title: str
    description: str = ""


class CourseCreate(CourseBase):
    pass


class CourseOut(CourseBase):
    id: int
    owner_id: int

    model_config = {"from_attributes": True}


class TopicBase(BaseModel):
    title: str
    order_index: int = 0


class TopicCreate(TopicBase):
    course_id: int


class TopicOut(TopicBase):
    id: int
    course_id: int

    model_config = {"from_attributes": True}


class LessonBase(BaseModel):
    title: str
    content: str = ""


class LessonCreate(LessonBase):
    topic_id: int


class LessonOut(LessonBase):
    id: int
    topic_id: int

    model_config = {"from_attributes": True}


class EnrollmentCreate(BaseModel):
    course_id: int


class EnrollmentOut(BaseModel):
    id: int
    user_id: int
    course_id: int
    status: str

    model_config = {"from_attributes": True}


class QuizCreate(BaseModel):
    lesson_id: int
    num_questions: int = 5


class QuizOut(BaseModel):
    id: int
    lesson_id: int
    questions: list

    model_config = {"from_attributes": True}


class AttemptCreate(BaseModel):
    quiz_id: int
    answers: list[int]


class AttemptOut(BaseModel):
    id: int
    quiz_id: int
    user_id: int
    score: float

    model_config = {"from_attributes": True}
