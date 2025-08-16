import os 
import secrets 
import string
import dotenv
from supabase import create_client
import logging 

logging.basicConfig(level=logging.INFO)

dotenv.load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY")
client = create_client(SUPABASE_URL, SERVICE_ROLE_KEY)

def generate_temp_password(length: int = 16) -> str:
    """
    This function generates a temporary password of a predefined
    length.

    Args: length - the length of the password; defaults to 16 characters long
    Returns: temp_password - temporary password
    """
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*()-_=+"
    temp_password = "".join(secrets.choice(alphabet) for i in range(length))

    return temp_password 

def add_users(emails: list[str]) -> dict[str, str]:
    """
    This function adds a list of users to the authenticated list.
    """
    results = {}

    for email in emails:
        temp_password = generate_temp_password()

        try:
            _ = client.auth.admin.create_user(
                {
                    "email": email, 
                    "password": temp_password,
                    "email_confirm": True
                }
            )

            results[email] = temp_password
            logging.info(f"✅ Created user {email}") 
        except Exception as e:
            results[email] = f"❌ Error: {str(e)}"
            logging.error(f"❌ Failed to create {email}: {e}")

    return results

if __name__ == "__main__":
    emails = ["rmahbub503@proton.me"]
    results = add_users(emails)

    logging.info("\nUser creation results:")
    
    for email, password in results.items():
        logging.info(f"{email}: {password}")