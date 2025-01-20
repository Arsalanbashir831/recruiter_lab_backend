from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from django.conf import settings

openai_api_key = str(settings.OPENAI_API_KEY)
if not openai_api_key:
    raise ValueError("OPENAI_API_KEY environment variable is not set.")
# Initialize ChatOpenAI
llm = ChatOpenAI(
    model="gpt-4o",
    temperature=0.7,
    max_tokens=500,
    max_retries=3,
    api_key=openai_api_key
)

def generate_linkedin_hiring_post(details: dict) -> str:
    try:
        """
        Generate a LinkedIn hiring post based on a dynamic JSON input.

        Args:
            details (dict): A JSON object containing job-related information.
                Example:
                {
                    "title": "Senior Backend Developer",
                    "company_name": "Tech Innovators Inc.",
                    "job_description": "We are seeking...",
                    "skills_required": ["Python", "Django"],
                    "location": "Remote",
                    "application_link": "https://apply.here"
                }

        Returns:
            str: The AI-generated LinkedIn hiring post.
        """
        # Define the system message
        system_message = SystemMessage(
            content=(
                "You are a professional content writer specializing in LinkedIn hiring posts. "
                "Your task is to create engaging, concise, and professional job posts that attract qualified candidates."
            )
        )

        # Define the human message
        human_message = HumanMessage(
            content=(
                f"The following is a JSON object containing details for a LinkedIn hiring post:\n\n"
                f"{details}\n\n"
                "Guidelines:\n"
                "1. Start with an attention-grabbing opening line.\n"
                "2. Clearly highlight the job title and company name.\n"
                "3. Provide a brief and compelling job description.\n"
                "4. List the key skills required for the role (if provided).\n"
                "5. Mention the job location (if provided).\n"
                "6. Conclude with a call-to-action and any application link.\n\n"
                "Generate the LinkedIn post based on the provided details."
            )
        )

        # Generate the response
        response = llm.invoke([system_message, human_message])
        print(response.response_metadata)

        return response.content.strip()

    except Exception as e:
        print(e)
        return f"Error generating LinkedIn post: {str(e)}"
