# Real photos (optional upgrade)

The landing page currently uses original SVG illustrations (src/components/illustrations/People.tsx).
Real photos of real learners and teachers build even more trust. To use them:

1. Only use photos you own or have written permission for (students under 18 need guardian consent).
2. Save them here as WebP/JPEG, ~800px wide, e.g. `student.webp`, `teacher.webp`.
3. In `src/app/page.tsx` replace `<StudentScene />` / `<TeacherScene />` with
   `<Image src="/people/student.webp" alt="A student using LightEd" width={800} height={640} priority />`.
4. Never show made-up testimonials or fake user numbers.
