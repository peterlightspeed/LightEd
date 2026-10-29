# TEACHING_GUIDE.md: how a teacher teaches on LightEd, and how to test it

## The model: two ways to teach
| | What it is | Teacher does | Student does |
| --- | --- | --- | --- |
| **Self-paced course** | Lessons + quizzes students do any time | Create course, topics, lessons, quizzes | Read, take quizzes, ask the AI tutor, follow the revision plan |
| **Live class** | A scheduled video call (Google Meet / Zoom / Teams) | Schedule it with a link; students are notified | Tap **Join** when it says *Live now* (opens 10 min early) |

LightEd does **not** host video itself. It schedules, notifies and tracks; the call runs on Meet/Zoom/Teams.
Typical rhythm: teach live (Meet) -> students revise and practise in LightEd -> the teacher watches the Students tab.

## Test it yourself (10 minutes, two browser windows)
Use a normal window for the teacher and an **Incognito** window for the student.

**Teacher (window 1)**
1. Sign up as a **Teacher** (or log in as `teacher@lighted.dev` / `password123`).
2. Courses -> **+ New course** -> title "Chemistry Basics" -> Create.
3. On the course page, **Manage this course**:
   - Add a topic ("Atoms").
   - **+ Lesson**: title, then paste lesson text (or **Import text from a PDF**).
   - Open **Quiz** on that lesson -> **Generate draft** -> read/edit the questions -> **Approve & publish**.
4. Copy the **Class code** (6 characters) shown at the top of "Manage this course".
5. **Live classes** -> Schedule class: title, date/time, paste a meeting link
   (open https://meet.google.com/new, copy the link). Set the time to a few minutes from now to see "Live now".

**Student (window 2, Incognito)**
6. Sign up as a **Student** (or `student@lighted.dev` / `password123`).
7. Courses -> **Join with a class code** -> enter the code -> you land on the course.
8. See **Live classes**: tap **Join** (opens the meeting link). The bell also shows "Live class scheduled".
9. Open the lesson -> **Mark as complete** -> take the **quiz**. Try **AI Tutor**: ask something from the lesson (it answers from the teacher's text and cites the lesson).
10. Open **Planner** -> pick the course, an exam date -> build a revision plan.

**Back to the teacher (window 1)**
11. **Students** tab: the new student appears with progress, average score and a risk reason.
    Score under 50% on a quiz -> the teacher gets a notification (bell).
12. Dashboard shows **Upcoming live classes**.

## Why the Students tab is empty at first
A teacher only sees students enrolled in **their own** courses. Until someone enrols (class code or "Enrol"), the
list is empty. That scoping is deliberate (privacy) and covered by automated tests.
