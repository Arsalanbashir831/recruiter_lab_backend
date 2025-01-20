from django.core.mail import EmailMessage
from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.conf import settings

def send_contact_email_to_admin(name, email, message):
    # Validate user's email
    try:
        validate_email(email)
    except ValidationError:
        raise ValueError("Invalid email address")

    # Construct email details
    subject = 'Contact Form Submission'
    email_body = f"""
    You have a new contact form submission:

    Name: {name}
    Email: {email}

    Message:
    {message}
    """
    from_email = email  # User's email as the sender
    to_email = [settings.DEFAULT_FROM_EMAIL]  # Admin/support email from settings

    # Create the email message
    email_message = EmailMessage(
        subject=subject,
        body=email_body,
        from_email=from_email,
        to=to_email,
    )

    try:
        # Send the email
        email_message.send(fail_silently=False)
    except Exception as e:
        # Handle exceptions, e.g., log or re-raise
        raise RuntimeError(f"Error sending contact email: {e}")


def send_confirmation_email_to_user(name, email, id):
    # Construct email details
    subject = 'Email Confirmation'
    email_body = f"""
    Dear {name}\n\n, Your Query has been submitted successfully. Your Query ID is: {id}
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [email]

    # Create the email message
    email_message = EmailMessage(
        subject=subject,
        body=email_body,
        from_email=from_email,
        to=to_email,
    )

    try:
        # Send the email
        email_message.send(fail_silently=False)
    except Exception as e:
        # Handle exceptions, e.g., log or re-raise
        raise RuntimeError(f"Error sending contact email: {e}")
    


def send_query_response_email_to_user(email, response):
    # Construct email details
    subject = 'Query Response'
    email_body = f"""
    Your Query has been responded successfully. Your Query Response is: {response}
    """
    from_email = settings.DEFAULT_FROM_EMAIL
    to_email = [email]

    # Create the email message
    email_message = EmailMessage(
        subject=subject,
        body=email_body,
        from_email=from_email,
        to=to_email,
    )

    try:
        # Send the email
        email_message.send(fail_silently=False)
    except Exception as e:
        # Handle exceptions, e.g., log or re-raise
        raise RuntimeError(f"Error sending contact email: {e}")
    
