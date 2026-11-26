# Naukri Mitra

**An AI job-application agent that tailors your resume to a job description without inventing anything, and sends the application only after you approve.**

## Problem
Tailoring a resume and writing an email for every job is slow. LLMs can do it fast, but they tend to invent skills and experience to match the job description, which is risky on a resume.

## How it works
1. **Gap analysis:** compares resume and job description, gives a match score, matching skills and missing skills.
2. **Honesty check:** asks the user about each gap. A skill is added only if the user confirms it with real details. "No" means it is never added.
3. **Resume writer:** rewrites the resume using only the original resume and the confirmed answers.
4. **Fact-checker:** a second LLM call lists every unsupported claim. If any are found, they go back to the writer as feedback (up to 3 attempts).
5. **Email and PDF:** finds the recruiter email in the job description (or asks the user), drafts a short email, and creates a one-page PDF.
6. **Human approval:** the user reviews, edits and approves before anything is sent.

## Key concepts
Agentic workflow (shared state, conditional routing, feedback loop), structured outputs, LLM as a judge, human in the loop.

## Evaluation
Tested manually on real resumes against real job descriptions, including deliberately mismatched ones (for example an AI/ML resume against a full stack job).

**Before the fact-checker**, the model invented a freelance role, inflated wording ("comfortable" became "expertise" and "production-ready"), copied phrases from the job description, and pushed the resume to two pages.

**Fixes:** stricter prompt rules, a separate fact-checking step, a retry loop with feedback, safety decided in code from the claim list (not from the model's yes/no), a hard block on sending when the check fails, and honesty questions that need real details.

**Result:** the final resume no longer contained invented roles or upgraded wording in repeated runs. Unsupported content is caught, removed on retry, or blocks sending.

**Limitations:** small manual evaluation, no formal metrics yet. The fact-checker is also an LLM, so a pass is strong evidence, not proof. The email draft is not fact-checked yet.

## Limitations and future work
- RAG is not implemented yet. Planned: a profile bank (vector database) so the writer uses only retrieved facts.
- Fact-check the email draft and build a labeled test set with real metrics.
- Only text-based PDFs, single user, no login.

## Tech stack
Python, LangGraph, LangChain, Pydantic, FastAPI, PyMuPDF, ReportLab, SMTP (Gmail), HTML/CSS/JavaScript.

## Author
Aehsan Ali Sunasara, AI/ML Engineer
