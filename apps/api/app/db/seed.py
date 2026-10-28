"""Seed demo data: `python -m app.db.seed`.

Creates a teacher, an admin, a demo student plus classmates, four courses with
topics/lessons/quizzes, enrolments, progress and quiz attempts. The data is
shaped so the student dashboard shows ~78% progress and varied focus areas.
"""
from sqlalchemy import select

from app.core.security import hash_password
from app.db.session import SessionLocal
from app.models.attempt import Attempt
from app.models.course import Course
from app.models.enrollment import Enrollment
from app.models.lesson import Lesson
from app.models.progress import Progress
from app.models.quiz import Quiz
from app.models.topic import Topic
from app.models.user import User

DEMO_PASSWORD = "password123"


def _course(db, owner, *, title, description, subject, level, accent, curriculum):
    """Create a course from a compact curriculum description.

    curriculum = [
        (topic_title, [(lesson_title, summary, minutes, content, questions), ...]),
        ...
    ]
    """
    course = Course(
        title=title,
        description=description,
        subject=subject,
        level=level,
        accent=accent,
        owner_id=owner.id,
    )
    db.add(course)
    db.flush()

    lessons = []
    for t_idx, (topic_title, lesson_defs) in enumerate(curriculum, start=1):
        topic = Topic(course_id=course.id, title=topic_title, order_index=t_idx)
        db.add(topic)
        db.flush()
        for l_idx, (l_title, summary, minutes, content, questions) in enumerate(lesson_defs, start=1):
            lesson = Lesson(
                topic_id=topic.id,
                title=l_title,
                summary=summary,
                duration_minutes=minutes,
                order_index=l_idx,
                content=content,
            )
            db.add(lesson)
            db.flush()
            if questions:
                db.add(
                    Quiz(
                        lesson_id=lesson.id,
                        title=f"{l_title} — checkpoint",
                        questions=questions,
                    )
                )
            lessons.append(lesson)
    return course, lessons


def seed() -> None:
    # Make sure tables exist first, so `python -m app.db.seed` works on a brand-new DB
    # (previously only the running API created them -> "no such table: users").
    import app.models  # noqa: F401  (registers every model on Base.metadata)
    from app.db.session import Base, engine

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        if db.scalar(select(Course).limit(1)):
            from app.db.catalog_extra import ensure_extra_courses

            n = ensure_extra_courses(db)
            print(f"Courses already present. Added {n} missing starter course(s).")
            return

        teacher = User(
            full_name="Tara Mensah",
            email="teacher@lighted.dev",
            hashed_password=hash_password(DEMO_PASSWORD),
            role="teacher",
        )
        admin = User(
            full_name="Alex Admin",
            email="admin@lighted.dev",
            hashed_password=hash_password(DEMO_PASSWORD),
            role="admin",
        )
        student = User(
            full_name="Sam Rivera",
            email="student@lighted.dev",
            hashed_password=hash_password(DEMO_PASSWORD),
            role="student",
        )
        classmates = [
            User(full_name="Amina Yusuf", email="amina@lighted.dev",
                 hashed_password=hash_password(DEMO_PASSWORD), role="student"),
            User(full_name="Noah Chen", email="noah@lighted.dev",
                 hashed_password=hash_password(DEMO_PASSWORD), role="student"),
            User(full_name="Priya Patel", email="priya@lighted.dev",
                 hashed_password=hash_password(DEMO_PASSWORD), role="student"),
            User(full_name="Leo Okafor", email="leo@lighted.dev",
                 hashed_password=hash_password(DEMO_PASSWORD), role="student"),
        ]
        # get-or-create: real sign-ups may already exist (even the same email).
        def _goc(u: User) -> User:
            existing = db.scalar(select(User).where(User.email == u.email))
            if existing:
                return existing
            db.add(u)
            db.flush()
            return u

        teacher, admin, student, *classmates = [_goc(u) for u in (teacher, admin, student, *classmates)]

        algebra, algebra_lessons = _course(
            db, teacher,
            title="Algebra Foundations",
            description="Build confidence with variables, equations and functions through short, visual lessons.",
            subject="Mathematics", level="Beginner", accent="blue",
            curriculum=[
                ("Variables & Expressions", [
                    ("What is a variable?",
                     "Meet the letter that stands in for a number.",
                     8,
                     "A variable is a symbol — usually a letter — that represents a value we do not know yet.\n\n"
                     "Think of a locker with a number inside. The letter x is the locker label; the number inside "
                     "is its value. When we write 3x, we mean 3 multiplied by whatever x holds.\n\n"
                     "Expressions combine variables, numbers and operations: 2x + 5, y/3, 4(a - 1). "
                     "An equation adds an equals sign and tells us two expressions balance.\n\n"
                     "**Worked example**\nIf x = 4, then 2x + 5 = 2(4) + 5 = 13.\n\n"
                     "**Try it**\nEvaluate 3n - 2 when n = 6. (Answer: 16.)",
                     [
                         {"prompt": "If x = 5, what is 2x + 3?",
                          "options": ["10", "13", "16", "8"], "answer_index": 1,
                          "explanation": "2(5) + 3 = 10 + 3 = 13."},
                         {"prompt": "Which of these is an expression?",
                          "options": ["3x + 2", "3x + 2 = 8", "x = 2", "8 > 3"], "answer_index": 0,
                          "explanation": "An expression has no equals sign."},
                         {"prompt": "Evaluate 3n - 2 when n = 6.",
                          "options": ["12", "16", "18", "20"], "answer_index": 1,
                          "explanation": "3(6) - 2 = 18 - 2 = 16."},
                     ]),
                    ("Simplifying expressions",
                     "Combine like terms without changing the value.",
                     10,
                     "Like terms have the same variable part. 4x and 7x are like terms; 4x and 7y are not.\n\n"
                     "To simplify 4x + 7x + 2, add the coefficients: 11x + 2. The constant stays separate.\n\n"
                     "**Common mistake**\n3x + 4 becomes 7x — wrong, because 3x and 4 are not like terms.\n\n"
                     "**Try it**\nSimplify 5a + 3b - 2a + b. (Answer: 3a + 4b.)",
                     [
                         {"prompt": "Simplify 5a + 3b - 2a + b.",
                          "options": ["3a + 4b", "7a + 4b", "3a + 2b", "5a + 3b"], "answer_index": 0,
                          "explanation": "5a - 2a = 3a and 3b + b = 4b."},
                         {"prompt": "Which pair are like terms?",
                          "options": ["4x and 4y", "4x and 7x", "4 and 4x", "x² and x"], "answer_index": 1,
                          "explanation": "They share the same variable part, x."},
                     ]),
                ]),
                ("Solving Equations", [
                    ("One-step equations",
                     "Undo one operation to isolate the variable.",
                     9,
                     "Solving an equation means finding the value that makes both sides equal. "
                     "We undo operations using inverses: addition ↔ subtraction, multiplication ↔ division.\n\n"
                     "**Example**\nx + 7 = 12 → subtract 7 from both sides → x = 5.\n\n"
                     "**Example**\n4x = 20 → divide both sides by 4 → x = 5.\n\n"
                     "Always do the same thing to both sides — the equation is a balance.",
                     [
                         {"prompt": "Solve x + 9 = 15.",
                          "options": ["5", "6", "7", "24"], "answer_index": 1,
                          "explanation": "Subtract 9 from both sides: x = 6."},
                         {"prompt": "Solve 6x = 42.",
                          "options": ["6", "7", "8", "36"], "answer_index": 1,
                          "explanation": "Divide both sides by 6: x = 7."},
                     ]),
                    ("Two-step equations",
                     "Use inverse operations in reverse order.",
                     12,
                     "For 3x + 4 = 19, undo the addition first, then the multiplication.\n\n"
                     "3x + 4 = 19\n3x = 15\nx = 5\n\n"
                     "Why this order? Because we are peeling layers: the outermost operation "
                     "is the +4, so it comes off first.\n\n"
                     "**Try it**\nSolve 5y - 3 = 22. (Answer: y = 5.)",
                     [
                         {"prompt": "Solve 3x + 4 = 19.",
                          "options": ["3", "5", "6", "7"], "answer_index": 1,
                          "explanation": "Subtract 4 then divide by 3: x = 5."},
                         {"prompt": "Solve 5y - 3 = 22.",
                          "options": ["4", "5", "6", "25"], "answer_index": 1,
                          "explanation": "Add 3 then divide by 5: y = 5."},
                         {"prompt": "What is the first step for 2x - 7 = 9?",
                          "options": ["Divide by 2", "Add 7", "Subtract 9", "Multiply by 2"],
                          "answer_index": 1, "explanation": "Undo the subtraction first."},
                     ]),
                ]),
            ],
        )

        biology, biology_lessons = _course(
            db, teacher,
            title="Biology: Cells to Systems",
            description="Explore how living things are built, from a single cell to coordinated body systems.",
            subject="Science", level="Beginner", accent="emerald",
            curriculum=[
                ("The Cell", [
                    ("Cell structure",
                     "The shared machinery of every living thing.",
                     11,
                     "Cells are the smallest unit of life. All cells have a membrane, cytoplasm and genetic material.\n\n"
                     "**Eukaryotic cells** (plants, animals, fungi) also have a nucleus and organelles. "
                     "**Prokaryotic cells** (bacteria) do not.\n\n"
                     "Key organelles: mitochondria release energy, ribosomes build proteins, and the nucleus "
                     "stores DNA. Plant cells add a cell wall and chloroplasts for photosynthesis.",
                     [
                         {"prompt": "Which organelle releases energy?",
                          "options": ["Nucleus", "Mitochondrion", "Ribosome", "Cell wall"], "answer_index": 1,
                          "explanation": "Mitochondria are the site of respiration."},
                         {"prompt": "Which structure do plant cells have that animal cells do not?",
                          "options": ["Nucleus", "Cell membrane", "Cell wall", "Cytoplasm"], "answer_index": 2,
                          "explanation": "Plant cells have a rigid cellulose cell wall."},
                     ]),
                    ("Diffusion and osmosis",
                     "How substances move without extra energy.",
                     10,
                     "Diffusion is the net movement of particles from high to low concentration. "
                     "Osmosis is the diffusion of water across a partially permeable membrane.\n\n"
                     "**In cells:** water moves into a cell in a dilute solution and out in a concentrated one. "
                     "This is why plant cells stay firm when watered.\n\n"
                     "Both processes are passive — no energy is required.",
                     [
                         {"prompt": "Osmosis is the movement of…",
                          "options": ["salt", "water", "proteins", "oxygen"], "answer_index": 1,
                          "explanation": "Osmosis specifically refers to water."},
                         {"prompt": "Diffusion moves particles from…",
                          "options": ["low to high concentration", "high to low concentration",
                                      "cold to hot", "inside to outside only"], "answer_index": 1,
                          "explanation": "Particles spread down a concentration gradient."},
                     ]),
                ]),
                ("Body Systems", [
                    ("Circulation",
                     "The transport network of the body.",
                     12,
                     "The circulatory system moves oxygen, nutrients and waste. The heart has four chambers "
                     "and pumps blood through arteries, capillaries and veins.\n\n"
                     "**Double circulation:** blood passes through the heart twice per circuit — once to the "
                     "lungs and once to the body. This keeps oxygenated and deoxygenated blood separate.\n\n"
                     "Capillaries are one cell thick, allowing exchange with tissues.",
                     [
                         {"prompt": "How many chambers does the human heart have?",
                          "options": ["Two", "Three", "Four", "Five"], "answer_index": 2,
                          "explanation": "Two atria and two ventricles."},
                         {"prompt": "Where does gas exchange happen?",
                          "options": ["Arteries", "Veins", "Capillaries", "Heart"], "answer_index": 2,
                          "explanation": "Capillary walls are one cell thick."},
                     ]),
                ]),
            ],
        )

        history, history_lessons = _course(
            db, teacher,
            title="World History: Modern Era",
            description="Key turning points from industrialisation to the digital age, with source-analysis practice.",
            subject="Humanities", level="Intermediate", accent="amber",
            curriculum=[
                ("Revolutions", [
                    ("The Industrial Revolution",
                     "How steam and factories reshaped society.",
                     13,
                     "Beginning in 18th-century Britain, the Industrial Revolution replaced hand production with "
                     "machines and factory systems.\n\n"
                     "Coal and steam power, the textile industry and railways accelerated output and urbanisation. "
                     "It also created new social tensions: long hours, child labour and crowded cities.\n\n"
                     "**Source skill**\nWhen reading a factory report, ask: who wrote it, why, and who is missing?",
                     [
                         {"prompt": "Where did the Industrial Revolution begin?",
                          "options": ["France", "Britain", "Germany", "USA"], "answer_index": 1,
                          "explanation": "It began in Britain in the late 18th century."},
                         {"prompt": "Which power source was central to early industrialisation?",
                          "options": ["Steam", "Nuclear", "Solar", "Electric"], "answer_index": 0,
                          "explanation": "Steam engines powered factories and trains."},
                     ]),
                    ("Decolonisation",
                     "Independence movements after 1945.",
                     12,
                     "After the Second World War, European empires weakened and independence movements "
                     "gained momentum across Asia and Africa.\n\n"
                     "India gained independence in 1947; Ghana in 1957; Nigeria in 1960. "
                     "New nations faced the challenge of building institutions while managing Cold War pressures.\n\n"
                     "**Key idea:** independence was a process, not a single day.",
                     [
                         {"prompt": "India gained independence in…",
                          "options": ["1945", "1947", "1957", "1960"], "answer_index": 1,
                          "explanation": "Partition and independence occurred in 1947."},
                     ]),
                ]),
            ],
        )

        coding, coding_lessons = _course(
            db, teacher,
            title="Intro to Programming",
            description="A friendly first step into code: variables, logic and building something real.",
            subject="Technology", level="Beginner", accent="violet",
            curriculum=[
                ("Thinking in Code", [
                    ("Variables and types",
                     "Store and label information.",
                     10,
                     "A variable is a named container for a value. Common types are numbers, strings and booleans.\n\n"
                     "```python\nname = \"Sam\"\nage = 16\nis_student = True\n```\n\n"
                     "Choose descriptive names. `score` is clearer than `s`.\n\n"
                     "**Try it**\nCreate variables for your favourite subject and the number of hours you study it.",
                     [
                         {"prompt": "Which value is a boolean?",
                          "options": ["\"hello\"", "42", "True", "3.14"], "answer_index": 2,
                          "explanation": "Booleans are True or False."},
                     ]),
                    ("Conditionals",
                     "Let your program make decisions.",
                     11,
                     "Conditionals run code only when a test is true.\n\n"
                     "```python\nif score >= 70:\n    print(\"Pass\")\nelse:\n    print(\"Keep practising\")\n```\n\n"
                     "Use `elif` for multiple branches. Indentation defines the block in Python.",
                     [
                         {"prompt": "Which keyword adds another branch?",
                          "options": ["else", "elif", "then", "case"], "answer_index": 1,
                          "explanation": "`elif` means 'else if'."},
                     ]),
                ]),
            ],
        )

        # Enrolments: Sam in 3 courses, classmates in 2.
        for course in (algebra, biology, history):
            db.add(Enrollment(user_id=student.id, course_id=course.id))
        for mate in classmates:
            db.add(Enrollment(user_id=mate.id, course_id=algebra.id))
            db.add(Enrollment(user_id=mate.id, course_id=biology.id))
        db.flush()

        # Sam completes ~78% of the 7 lessons across enrolled courses.
        # Interleave completions so each course shows a realistic partial bar.
        # 3/4 + 2/3 + 2/2 = 7/9 ≈ 78% overall (matches the Figma dashboard).
        sam_completed = (
            algebra_lessons[:3] + biology_lessons[:2] + history_lessons[:2]
        )
        for lesson in sam_completed:
            db.add(Progress(user_id=student.id, lesson_id=lesson.id, completed=True))

        # Classmates get partial progress so the teacher dashboard is varied.
        for idx, mate in enumerate(classmates):
            for lesson in (algebra_lessons + biology_lessons)[: 3 + idx]:
                db.add(Progress(user_id=mate.id, lesson_id=lesson.id, completed=True))

        # Quiz attempts (Sam + classmates) for analytics.
        quizzes = db.scalars(select(Quiz)).all()
        sam_scores = [85.0, 72.0, 64.0, 91.0]
        for quiz, score in zip(quizzes[:4], sam_scores):
            db.add(Attempt(quiz_id=quiz.id, user_id=student.id, score=score, answers=[]))
        for idx, mate in enumerate(classmates):
            for quiz in quizzes[:2]:
                db.add(
                    Attempt(
                        quiz_id=quiz.id,
                        user_id=mate.id,
                        score=float(48 + idx * 11),
                        answers=[],
                    )
                )

        db.commit()
        print("Seed complete.")
        print("  student@lighted.dev / password123")
        print("  teacher@lighted.dev / password123")
        print("  admin@lighted.dev   / password123")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
    from app.db.catalog_extra import ensure_extra_courses

    _db = SessionLocal()
    print(f"Starter catalogue top-up: {ensure_extra_courses(_db)} added")
    _db.close()
