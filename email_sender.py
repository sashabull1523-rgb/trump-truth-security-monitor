import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from config import (
    EMAIL_ADDRESS,
    EMAIL_PASSWORD,
    EMAIL_TO
)


def send_email(subject, body):

    message = MIMEMultipart()

    message["From"] = EMAIL_ADDRESS

    message["To"] = EMAIL_TO

    message["Subject"] = subject


    message.attach(
        MIMEText(
            body,
            "plain"
        )
    )


    try:

        server = smtplib.SMTP(
            "smtp.gmail.com",
            587
        )

        server.starttls()


        server.login(
            EMAIL_ADDRESS,
            EMAIL_PASSWORD
        )


        server.send_message(
            message
        )


        server.quit()


        print("Email sent successfully")


    except Exception as error:

        print(
            f"Email failed: {error}"
        )
