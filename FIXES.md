# Fix notes: AI tutor + /tutor crash + mobile

## AI not working (backend)
- `gemini-1.5-flash` is retired (404). Default is now `gemini-3.8-flash`; the client falls back to
  `gemini-3.6-flash` on a 404 and remembers the model that works. Set `GEMINI_MODEL` on Render accordingly.
- API key moved from the URL (`?key=`) to the `x-goog-api-key` header. It was leaking into logs: **rotate your key**.
- Tutor: filler words ("explain", "example"...) are ignored, follow-ups reuse the previous question,
  light stemming, 2nd source only if it is nearly as relevant, chat history sent from the frontend.
- Offline fallback now returns a `notice` explaining why the AI model wasn't used.
- New `GET /ai/status` (login required): one live probe, reports configured/model/ok/error, never the key.
- Tests: `apps/api/tests/test_ai_tutor.py` (29 pass in total).

## /tutor "Application error" (frontend)
`useEffect(() => el.scrollIntoView())` returned scrollIntoView's result as the cleanup function. If a browser
extension/polyfill makes that non-undefined, React throws `n is not a function`. All such effects fixed
(tutor, ThemeToggle, SessionsPanel). Error boundaries added (`(app)/error.tsx`, `global-error.tsx`).

## Console warnings
`mobile-web-app-capable` meta added, `favicon.ico` added, service-worker cache bumped to v2.
"Banner not shown" is informational (install prompt is intentionally deferred).

## Mobile / UI
Rebuilt tutor chat (fixed between header and tab bar, markdown rendering, typing indicator, retry, new chat,
source chips, auto-grow composer, session persistence); brand in mobile header; clearer active tab;
compact course filters; inline class-code row; non-wrapping dashboard buttons; 320px fixes; focus rings;
reduced-motion support; select arrows.

# Round 2: friendlier app, teacher tools, certificates
- Tutor never dead-ends: students get how-to-enrol steps, matching course suggestions and Browse/Join buttons;
  teachers get a course-building assistant (Gemini) or a how-to-start guide with free material sources.
- Quiz: "Approve & publish" is now "Publish quiz"; after publishing it becomes a green "Published" badge,
  and "Save changes" only appears after edits.
- AI for teachers: "Suggest topics" (tap to add) and "Draft with AI" for lessons (POST /ai/suggest-topics, /ai/draft-lesson).
- Videos: YouTube, Vimeo and Instagram links play inline; Zoom/Meet/Teams recordings and Drive files show as cards.
- Leaderboard (GET /teacher/leaderboard) on the Students page: 60% quiz average + 40% completion, per course.
- Certificates: unlock at 100% lessons; printable page /certificate/{courseId}; public check at GET /certificates/verify/{id}.
- Teacher home: dismissible getting-started guide and weekly-rotating course ideas (ML/AI, data analysis...) that
  pre-fill the new-course form.
- Tests: 36 passing (test_v7_features.py).
