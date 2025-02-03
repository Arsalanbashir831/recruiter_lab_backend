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
        print(response)
        print(response.response_metadata)

        return response.content.strip()

    except Exception as e:
        print(e)
        return f"Error generating LinkedIn post: {str(e)}"



import json
from typing import Literal, Optional
from pydantic import BaseModel, ValidationError, Field
from langchain_openai import ChatOpenAI
from langchain_core.messages import SystemMessage, HumanMessage
from django.conf import settings

# Define a Pydantic model for the response components
class LinkedInPostComponents(BaseModel):
    hook: str = Field(description="The hook or introductory part of the LinkedIn post.")
    body: str = Field(description="The main body of the LinkedIn post.")
    call_to_action: str = Field(description="The call-to-action or conclusion of the LinkedIn post.")

# Allowed tone types for clarity and validation
ToneType = Literal["numbered list", "insightful take", "personal experience"]

def generate_linkedin_post_components(details: dict, tone: ToneType) -> Optional[LinkedInPostComponents]:
    """
    Generate a LinkedIn hiring post broken down into three components: hook, body, and call to action.
    The post will be generated in one of three tones: 'numbered list', 'insightful take', or 'personal experience'.

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
        tone (ToneType): The tone in which the post should be written.
            Allowed values: "numbered list", "insightful take", "personal experience"

    Returns:
        LinkedInPostComponents: A Pydantic model with fields 'hook', 'body', and 'call_to_action'.
        Returns None if an error occurs.
    """
    try:
        # Define the system message
        system_message = SystemMessage(
            content=(
                "You are a professional content writer specializing in LinkedIn hiring posts. "
                "Your task is to create engaging, concise, and professional job posts that attract qualified candidates. "
                "You must break down the post into three parts: a hook to grab attention, a body with the job details, "
                "and a clear call-to-action at the end. "
            )
        )

        # Define the human message with guidelines and tone instructions.
        human_message = HumanMessage(
            content=(
                f"Generate a LinkedIn hiring post in the tone of '{tone}'.\n\n"
                "The post should be split into three parts:\n"
                "1. 'hook': an attention-grabbing opening line.\n"
                "2. 'body': a brief and compelling job description that includes the job title, company name, "
                "job description, key skills (if provided), and location (if provided).\n"
                "3. 'call_to_action': a concluding statement that includes a call-to-action and the application link (if provided).\n\n"
                "Ensure the final output is in JSON format with keys exactly as follows: hook, body, call_to_action.\n\n"
                f"Here are the job details:\n{details}\n\n"
                "Generate the response now."
            )
        )

        # Generate the response using the LLM
        structured_llm = llm.with_structured_output(LinkedInPostComponents)
        response = structured_llm.invoke([system_message, human_message])
        print(response)
        # print("Response metadata:", response.response_metadata)

        # Attempt to parse the JSON response using the Pydantic model
        
        try:
            response = response.model_dump_json()
            response_json = json.loads(response)
        except json.JSONDecodeError as json_err:
            raise ValueError(f"Failed to parse JSON from LLM response: {json_err}")

        post_components = LinkedInPostComponents(**response_json)
        post_components = post_components.model_dump_json()
        post_components = json.loads(post_components)
        return post_components

    except Exception as e:
        print("Error generating LinkedIn post components:", e)
        return str(e)
    

