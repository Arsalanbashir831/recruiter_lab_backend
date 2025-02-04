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
from typing import Literal, Optional, List
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
    

def generate_section(content : str , prompt : str):
    try:
        system_message = SystemMessage(
            content=(
                "You are a professional content rewriter specializing in regenerating LinkedIn hiring posts based on the prompt "
                "Your task is to create engaging, concise, and professional job posts that attract qualified candidates. "
                "You must regenerate without forgetting the original crux of the post. "
            )
        )

        human_message = HumanMessage(
            content=(
                f"Regenerate the following LinkedIn post based on the prompt '{prompt}'\n\n"
                f"{content}\n\n"
                "Generate the response now."
            )
        )

        response = llm.invoke([system_message, human_message])
        print(response)
        # print("Response metadata:", response.response_metadata)

        return response.content.strip()

    except Exception as e:
        print("Error generating LinkedIn post components:", e)
        return None

from enum import Enum
class SectionEnum(str, Enum):
    hook = "hook"
    body = "body"
    call_to_action = "call_to_action"

class DerivedSections(BaseModel):
    sections: List[SectionEnum] = Field(
        description="List of sections: 'hook', 'body', 'call_to_action'"
    )

def derive_section(prompt: str) -> DerivedSections:
    """
    Determines which section(s) the user's prompt is referring to. The LLM is instructed
    to return a JSON object with a key 'sections' containing a list of one or more of the following:
    'hook', 'body', or 'call_to_action'. If the LLM's answer is unclear or invalid,
    the function defaults to returning all three sections.
    
    Args:
        prompt (str): The user prompt indicating which section(s) they are referring to.
    
    Returns:
        DerivedSections: A Pydantic model containing the validated list of sections.
    """
    try:
        # Construct a system message with instructions.
        system_message = SystemMessage(
            content=(
                "You are a professional content analyzer. Your task is to read the user's prompt and determine "
                "which section or sections of a LinkedIn hiring post it refers to. "
                "The only valid section names are 'hook', 'body', and 'call_to_action'. "
                "Return the result as a JSON object with a single key 'sections', whose value is a list of the valid section(s). "
                "If you cannot clearly determine the intended section(s), then return all three sections."
            )
        )

        # Construct a human message with the user's prompt.
        human_message = HumanMessage(
            content=(
                f"User prompt: \"{prompt}\"\n\n"
                "Based on the above prompt, identify which of the following sections the user is referring to: "
                "'hook', 'body', or 'call_to_action'. "
                "Return your answer in JSON format as: {\"sections\": [list of sections]}. "
                "If the answer is unclear, return all sections: "
                "[\"hook\", \"body\", \"call_to_action\"]."
            )
        )

        # Use LangChain's structured output capability if available.
        structured_llm = llm.with_structured_output(DerivedSections)
        response = structured_llm.invoke([system_message, human_message])
        print("LLM structured response:", response)

        # If we successfully get a DerivedSections model, return it.
        if isinstance(response, DerivedSections):
            return response

        # Otherwise, try to parse response.content as JSON.
        try:
            response_json = json.loads(response.content.strip())
            # Validate and build our DerivedSections model.
            derived = DerivedSections(**response_json)
            return derived
        except (json.JSONDecodeError, ValidationError) as parse_err:
            print("Error parsing LLM response:", parse_err)
            # Fallback: return all sections.
            return DerivedSections(
                sections=[SectionEnum.hook, SectionEnum.body, SectionEnum.call_to_action]
            )
    except Exception as e:
        print("Error in derive_section:", e)
        # Fallback: return all sections.
        return DerivedSections(
            sections=[SectionEnum.hook, SectionEnum.body, SectionEnum.call_to_action]
        )
    