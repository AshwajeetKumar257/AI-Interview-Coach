import streamlit as st
import google.generativeai as genai
import re
from PIL import Image

# ---------------- Gemini API ---------------- #

API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=API_KEY)

model = genai.GenerativeModel("gemini-2.5-flash")

# ---------------- Session State ---------------- #

if "question" not in st.session_state:
    st.session_state.question = ""

if "feedback" not in st.session_state:
    st.session_state.feedback = ""

if "question_count" not in st.session_state:
    st.session_state.question_count = 0

if "scores" not in st.session_state:
    st.session_state.scores = []

if "candidate_name" not in st.session_state:
    st.session_state.candidate_name = ""

if "job_role" not in st.session_state:
    st.session_state.job_role = ""

if "difficulty" not in st.session_state:
    st.session_state.difficulty = ""

if "interview_started" not in st.session_state:
    st.session_state.interview_started = False

if "asked_questions" not in st.session_state:
    st.session_state.asked_questions = []

# ---------------- UI ---------------- #

st.set_page_config(
    page_title="AI Interview Coach",
    page_icon="🎤",
    layout="centered"
)
logo = Image.open("assets/ag_logo.png")

col1, col2 = st.columns([1, 5])

with col1:
    st.image(logo, width=70)

with col2:
    st.title("🎤 AI Interview Coach")


st.write("Practice technical interviews with AI and get instant feedback.")

st.divider()

candidate_name = st.text_input(
    "👤 Enter Your Name",
    value=st.session_state.candidate_name
)

job_role = st.selectbox(
    "Select Job Role",
    [
        "Java Developer",
        "Python Developer",
        "AI/ML Engineer"
    ]
)

difficulty = st.radio(
    "Choose Difficulty",
    [
        "Easy",
        "Medium",
        "Hard"
    ]
)
# ---------------- Start Interview ---------------- #

if st.button("🚀 Start Interview"):

    if candidate_name.strip() == "":
        st.warning("⚠️ Please enter your name.")

    else:

        st.session_state.interview_started = True
        st.session_state.candidate_name = candidate_name
        st.session_state.job_role = job_role
        st.session_state.difficulty = difficulty

        st.session_state.question_count = 1
        st.session_state.feedback = ""
        st.session_state.scores = []
        st.session_state.asked_questions = []

        prompt = f"""
Generate ONE {difficulty} level interview question for a {job_role}.

Rules:
- Ask only ONE technical interview question.
- Do NOT provide the answer.
- Keep the difficulty exactly {difficulty}.
"""

        with st.spinner("🤖 AI is generating your first interview question..."):

            try:

                response = model.generate_content(prompt)

                st.session_state.question = response.text
                st.session_state.asked_questions.append(response.text)

            except Exception:

                st.error(
                    "⚠️ AI service is busy or API quota exceeded.\n\nPlease wait 30-60 seconds and try again."
                )
                st.stop()

# ---------------- Show Question ---------------- #

if st.session_state.interview_started:

    st.success(f"Welcome {st.session_state.candidate_name}")

    st.progress(st.session_state.question_count / 5)

    st.subheader(
        f"Interview Question {st.session_state.question_count}/5"
    )

    st.write(st.session_state.question)

    answer = st.text_area(
        "✍️ Your Answer",
        key=f"answer_{st.session_state.question_count}"
    )
# ---------------- Submit Answer ---------------- #

    if st.button("📤 Submit Answer"):

        if answer.strip() == "":
            st.warning("⚠️ Please enter your answer.")

        else:

            eval_prompt = f"""
You are an expert technical interviewer.

Interview Question:
{st.session_state.question}

Candidate Answer:
{answer}

Evaluate the answer.

Return ONLY in this format:

Score: X/10

Strengths:
- Point 1
- Point 2

Mistakes:
- Point 1
- Point 2

Correct Answer:
(Write the ideal interview answer.)
"""

            with st.spinner("🤖 AI is evaluating your answer..."):

                try:

                    evaluation = model.generate_content(eval_prompt)

                    st.session_state.feedback = evaluation.text

                except Exception:

                    st.error(
                        "⚠️ AI service is busy or API quota exceeded.\n\nPlease wait 30-60 seconds and try again."
                    )
                    st.stop()

            # -------- Extract Score -------- #

            score = 0

            match = re.search(
                r"Score:\s*(\d+)",
                st.session_state.feedback
            )

            if match:
                score = int(match.group(1))

            st.session_state.scores.append(score)
# ---------------- Feedback ---------------- #

if st.session_state.feedback != "":

    st.subheader("📊 AI Feedback")

    st.write(st.session_state.feedback)

    # ---------------- Next Question ---------------- #

    if st.session_state.question_count < 5:

        if st.button("➡️ Next Question"):

            previous_questions = "\n".join(
                st.session_state.asked_questions
            )

            prompt = f"""
Generate ONE {st.session_state.difficulty} level interview question for a {st.session_state.job_role}.

Previously Asked Questions:
{previous_questions}

Rules:
- Do NOT repeat any previous question.
- Generate a completely different interview question.
- Return ONLY the question.
"""

            with st.spinner("🤖 Generating next question..."):

                try:

                    response = model.generate_content(prompt)

                    retry = 0

                    while (
                        response.text in st.session_state.asked_questions
                        and retry < 3
                    ):
                        response = model.generate_content(prompt)
                        retry += 1

                    st.session_state.question = response.text
                    st.session_state.asked_questions.append(response.text)

                    st.session_state.feedback = ""
                    st.session_state.question_count += 1

                    st.rerun()

                except Exception:

                    st.error(
                        "⚠️ AI service is busy or API quota exceeded.\n\nPlease wait 30-60 seconds and try again."
                    )
                    st.stop()

    # ---------------- Final Report ---------------- #

    else:

        total = sum(st.session_state.scores)
        average = total / len(st.session_state.scores)

        st.success("🎉 Interview Completed!")

        st.balloons()

        st.markdown("---")

        st.subheader("📈 Final Interview Report")

        col1, col2 = st.columns(2)

        with col1:
            st.metric(
                "Questions Attempted",
                len(st.session_state.scores)
            )

        with col2:
            st.metric(
                "Total Score",
                f"{total}/50"
            )

        st.metric(
            "Average Score",
            f"{average:.1f}/10"
        )

        if average >= 8:
            st.success("⭐⭐⭐⭐⭐ Excellent Performance!")

        elif average >= 6:
            st.info("⭐⭐⭐⭐ Good Performance!")

        else:
            st.warning("📚 Keep Practicing!")

        st.divider()

        if st.button("🔄 Restart Interview"):

            st.session_state.question = ""
            st.session_state.feedback = ""
            st.session_state.question_count = 0
            st.session_state.scores = []
            st.session_state.asked_questions = []
            st.session_state.interview_started = False

            st.rerun()

st.divider()
st.caption("Developed by GROUP AG||MNNIT~Summer internship Project")