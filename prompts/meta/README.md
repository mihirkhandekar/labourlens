# Meta prompts

Prompts for the project's author, not for the running system. The runtime prompts (planner, answer, judge, rerank, repair) are the files in `prompts/` itself and are hashed into experiment records; nothing in this folder is read by the application.

- `understand-project/PROMPT.md`: a tutor session that teaches the whole project module by module and drills interview questions.
- `prepare-submission/PROMPT.md`: a plan-first audit and clean-up that turns this repository into a submission-ready package.
