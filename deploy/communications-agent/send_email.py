import os
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY")

def send_email(to_email, subject, content):
    # Accepts a list of emails or a single email
    if isinstance(to_email, str):
        to_emails = [to_email]
    else:
        to_emails = to_email
    message = Mail(
        from_email='ucabpes@ucl.ac.uk',
        to_emails=to_emails,
        subject=subject,
        plain_text_content=content
    )
    try:
        sg = SendGridAPIClient(SENDGRID_API_KEY)
        response = sg.send(message)
        print(f"Email sent! Status code: {response.status_code}")
        return response.status_code
    except Exception as e:
        print(f"Error sending email: {e}")
        return None


if __name__ == "__main__":
    send_email("peaceselem@gmail.com", "Test Subject", "Test email body")