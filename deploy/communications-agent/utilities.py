from pathlib import Path
import os
import httpx

from azure.ai.projects.aio import AIProjectClient
from azure.ai.projects.models import ThreadMessage

from terminal_colors import TerminalColors as tc


class Utilities:
    # propert to get the relative path of shared files
    @property
    def shared_files_path(self) -> Path:
        """Get the path to the shared files directory."""
        return Path(__file__).parent.parent.parent.resolve() / "shared"

    def load_instructions(self, instructions_file: str) -> str:
        """Load instructions from a file."""
        file_path = self.shared_files_path / instructions_file
        with file_path.open("r", encoding="utf-8", errors="ignore") as file:
            return file.read()

    def log_msg_green(self, msg: str) -> None:
        """Print a message in green."""
        print(f"{tc.GREEN}{msg}{tc.RESET}")

    def log_msg_purple(self, msg: str) -> None:
        """Print a message in purple."""
        print(f"{tc.PURPLE}{msg}{tc.RESET}")

    def log_token_blue(self, msg: str) -> None:
        """Print a token in blue."""
        print(f"{tc.BLUE}{msg}{tc.RESET}", end="", flush=True)

    async def get_file(self, project_client: AIProjectClient, file_id: str, attachment_name: str) -> None:
        """Retrieve the file and save it to the local disk."""
        self.log_msg_green(f"Getting file with ID: {file_id}")

        attachment_part = attachment_name.split(":")[-1]
        file_name = Path(attachment_part).stem
        file_extension = Path(attachment_part).suffix
        if not file_extension:
            file_extension = ".png"
        file_name = f"{file_name}.{file_id}{file_extension}"

        folder_path = Path(self.shared_files_path) / "files"
        folder_path.mkdir(parents=True, exist_ok=True)
        file_path = folder_path / file_name

        # Save the file using a synchronous context manager
        with file_path.open("wb") as file:
            async for chunk in await project_client.agents.get_file_content(file_id):
                file.write(chunk)

        self.log_msg_green(f"File saved to {file_path}")

    async def get_files(self, message: ThreadMessage, project_client: AIProjectClient) -> None:
        """Get the image files from the message and kickoff download."""
        if message.image_contents:
            for index, image in enumerate(message.image_contents, start=0):
                attachment_name = (
                    "unknown" if not message.file_path_annotations else message.file_path_annotations[index].text + ".png"
                )
                await self.get_file(project_client, image.image_file.file_id, attachment_name)
        elif message.attachments:
            for index, attachment in enumerate(message.attachments, start=0):
                attachment_name = (
                    "unknown" if not message.file_path_annotations else message.file_path_annotations[index].text
                )
                await self.get_file(project_client, attachment.file_id, attachment_name)

    async def upload_file(self, project_client: AIProjectClient, file_path: Path, purpose: str = "assistants") -> None:
        """Upload a file to the project."""
        self.log_msg_purple(f"Uploading file: {file_path}")
        file_info = await project_client.agents.upload_file(file_path=file_path, purpose=purpose)
        self.log_msg_purple(f"File uploaded with ID: {file_info.id}")
        return file_info

    async def create_vector_store(
        self, project_client: AIProjectClient, files: list[str], vector_store_name: str
    ) -> None:
        """Upload a file to the project."""

        file_ids = []
        prefix = self.shared_files_path

        # Upload the files
        for file in files:
            file_path = prefix / file
            file_info = await self.upload_file(project_client, file_path=file_path, purpose="assistants")
            file_ids.append(file_info.id)

        self.log_msg_purple("Creating the vector store")

        # Create a vector store
        vector_store = await project_client.agents.create_vector_store_and_poll(
            file_ids=file_ids, name=vector_store_name
        )

        self.log_msg_purple(f"Vector store created and files added.")
        return vector_store

    async def display_thread_messages(self, project_client: AIProjectClient, thread_id: str, limit: int = 10):
        """Display recent messages from a thread."""
        try:
            messages = await project_client.agents.list_messages(thread_id=thread_id, limit=limit)

            if not messages.data:
                self.log_msg_purple("No messages found in the thread.")
                return

            self.log_msg_green(f"Found {len(messages.data)} message(s) in thread {thread_id}")
            self.log_msg_green("=" * 50)

            # Display messages in chronological order (reverse the list since API returns newest first)
            for i, message in enumerate(reversed(messages.data)):
                self.log_msg_purple(f"Message {i + 1}:")
                self.log_msg_purple(f"  ID: {message.id}")
                self.log_msg_purple(f"  Role: {message.role}")
                self.log_msg_purple(f"  Created: {message.created_at}")

                if message.content:
                    for content_item in message.content:
                        if hasattr(content_item, 'text') and content_item.text:
                            self.log_msg_green(f"  Content: {content_item.text.value}")
                        elif hasattr(content_item, 'type'):
                            self.log_msg_purple(f"  Content type: {content_item.type}")

                # Handle file attachments if present
                if hasattr(message, 'attachments') and message.attachments:
                    self.log_msg_purple(f"  Attachments: {len(message.attachments)} file(s)")

                print("-" * 30)

        except Exception as e:
            self.log_msg_purple(f"Error displaying messages: {str(e)}")

    async def check_for_new_messages(self, project_client: AIProjectClient, thread_id: str, last_known_message_id: str = None):
        """Check if there are new messages since the last known message ID."""
        try:
            # Get all messages (or recent ones)
            messages = await project_client.agents.list_messages(thread_id=thread_id, limit=50)

            if not messages.data:
                return []

            # If no last known message ID, return the most recent message
            if not last_known_message_id:
                return [messages.data[0]]

            # Find new messages since the last known message
            new_messages = []
            for message in messages.data:
                if message.id == last_known_message_id:
                    break
                new_messages.append(message)

            return new_messages

        except Exception as e:
            self.log_msg_purple(f"Error checking for new messages: {str(e)}")
            return []

    def fetch_user_directory(self):
        """Fetch user directory from uploaded Azure resource to verify agent access."""
        url = os.getenv("USER_DIRECTORY_URL")
        if not url:
            self.log_msg_purple("⚠️ USER_DIRECTORY_URL not found in environment variables")
            return {}
        
        try:
            response = httpx.get(url, timeout=10)
            response.raise_for_status()
            self.log_msg_green("Successfully accessed user directory")
            user_data = response.json()
            self.log_msg_green(f"✅ Loaded user directory with {len(user_data.get('users', []))} users")
            return user_data
        except Exception as e:
            self.log_msg_purple(f"Failed to load user directory: {e}")
            return {}

    def find_user_by_id(self, user_id: str, user_directory: dict = None):
        """Find a user by their ID in the user directory."""
        if user_directory is None:
            user_directory = self.fetch_user_directory()
        
        users = user_directory.get('users', [])
        for user in users:
            if user.get('user_id') == user_id:
                return user
        return None

    def find_user_by_email(self, email: str, user_directory: dict = None):
        """Find a user by their email in the user directory."""
        if user_directory is None:
            user_directory = self.fetch_user_directory()
        
        users = user_directory.get('users', [])
        for user in users:
            if user.get('email', '').lower() == email.lower():
                return user
        return None