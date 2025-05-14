import os
import chainlit as cl
from dotenv import load_dotenv
from agents import Agent, Runner, AsyncOpenAI, OpenAIChatCompletionsModel, set_tracing_disabled
from agents.run import RunConfig
import PyPDF2  # for parsing PDFs
from server import save_resume_to_pdf  # ✅ Import at the top of your file
from chainlit import AskFileMessage





# Load environment variables
load_dotenv()

# ------------------ Gemini configuration -------------------

gemini_api_key = os.getenv("GEMINI_API_KEY")

if not gemini_api_key:
    raise ValueError("GEMINI_API_KEY is not set. Please ensure it is defined in your .env file.")

external_client = AsyncOpenAI(
    api_key=gemini_api_key,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.0-flash",
    openai_client=external_client
)

config = RunConfig(
    model=model,
    model_provider=external_client,
    tracing_disabled=True
)

# ------------------ Agent Definition -------------------

agent = Agent(
    name="Smart Resume Tailor",
    instructions=(
       "You are an AI resume tailoring assistant. "
        "Your job is to take a user's base resume and a job description, and create a customized resume tailored to that job. "
        "Use job keywords to identify relevant experience and skills from the resume. "
        "Generate a personalized summary, core skills, and refined experience section. "
        "Format the output cleanly and clearly for professional use. "
        "You must **only** respond to job-related queries. "
        "You must **not** answer any other type of input or query outside of resume tailoring. "
        "You must **not** add any work experience, skills, or qualifications on your own—only use what the user provides in their resume. "
        "When the user inputs: "
        "**\"Your base resume: Please copy and paste the text of your current resume.\"** "
        "and "
        "**\"The job description: Please copy and paste the text of the job description you want to tailor your resume to.\"** "
        "You will generate a tailored resume **only** based on the content provided in those two inputs. "
        "Once the resume is tailored, you will generate a downloadable **HTML page** containing the formatted resume. "
        "The link to the HTML page will open in a new tab, allowing the user to view and download the resume as a cleanly formatted web page."


    ),
    model=model
)

# -------- Optional: Test Run --------
result = Runner.run_sync(
    agent,
    "Tailor my resume for a Software Engineer role at Google using the job description provided.",
    run_config=config
)

print("\nCALLING AGENT\n")
print("Agent response:", result.final_output)

# ------------------ Chainlit Handlers -------------------


def extract_text_from_pdf(file_path):
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        return "\n".join(page.extract_text() for page in reader.pages if page.extract_text())

@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])
    cl.user_session.set("resume_text", "")
    cl.user_session.set("jd_text", "")
    await cl.Message(content="Hi! Upload your **resume** (PDF) and **job description** (PDF or text), and I’ll customize your resume!").send()


@cl.on_message
async def handle_message(message: cl.Message):
    await cl.Message(content="Please upload your resume and job description as files.").send()




@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])

    # Ask for both files
    files = await cl.AskFileMessage(
        content="📄 Please upload your **resume** and the **job description** (PDF or TXT files).",
        accept=["application/pdf", "text/plain"],
        max_files=2,
        max_size_mb=5
    ).send()

    # Process uploaded files
    resume_text = ""
    jd_text = ""

    for file in files:
        file_name = file.name.lower()
        file_path = file.path

        # Parse PDF or TXT
        if file_name.endswith(".pdf"):
            content = extract_text_from_pdf(file_path)
        else:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

        if "resume" in file_name:
            resume_text = content
        elif "job" in file_name or "jd" in file_name:
            jd_text = content

    if not resume_text or not jd_text:
        await cl.Message(content="❗ Please make sure one file is named with 'resume' and the other with 'job' or 'jd'.").send()
        return

    # Save in session
    cl.user_session.set("resume_text", resume_text)
    cl.user_session.set("jd_text", jd_text)

    # Run the agent
    prompt = (
        "Here is the user's base resume:\n"
        f"{resume_text}\n\n"
        "And here is the job description:\n"
        f"{jd_text}\n\n"
        "Please generate a tailored resume that highlights matching skills and experience."
    )

    result = await Runner.run(agent, input=prompt, run_config=config)

    # Save to PDF
    save_resume_to_pdf(result.final_output)

    download_link = "http://localhost:8000/download"

    await cl.Message(content="🎯 Customized Resume:\n\n" + result.final_output).send()
    await cl.Message(content=f"✅ Your resume is ready as a PDF.\n\n🔗 [Click here to download]({download_link})").send()

#---------------------------------------------------------

@cl.on_chat_start
async def handle_chat_start():
    cl.user_session.set("history", [])
    await cl.Message(
        content="Hi there! I’m your Smart Resume Tailor 🤖. Upload your resume and job description to get a custom-tailored resume. Ready when you are!"
    ).send()


@cl.on_message
async def handle_message(message: cl.Message):
    history = cl.user_session.get("history")
    history.append({"role": "user", "content": message.content})

    result = await Runner.run(
        agent,
        input=history,
        run_config=config,
    )

    history.append({"role": "assistant", "content": result.final_output})
    cl.user_session.set("history", history)
    await cl.Message(content=result.final_output).send()
