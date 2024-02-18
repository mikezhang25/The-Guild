import os
import requests
import json
import openai
import reflex as rx
import sys

current_path = os.getcwd()
base_path = current_path.split("TreeHacks2024")[0] + "TreeHacks2024"
sys.path.append(base_path)

from rag_src.zephyr_rag import ZephyrRAG

zephyr_rag = ZephyrRAG(model="zephyr-7b-beta")
zephyr_rag.start_rag()


class QA(rx.Base):
    """A question and answer pair."""

    question: str
    answer: str
    answer_only: bool = False


DEFAULT_CHATS = {
    "Intros": [],
}


class State(rx.State):
    """The app state."""

    # A dict from the chat name to the list of questions and answers.
    chats: dict[str, list[QA]] = DEFAULT_CHATS

    # The current chat name.
    current_chat = "Intros"

    # The current question.
    question: str

    # Whether we are processing the question.
    processing: bool = False

    # The name of the new chat.
    new_chat_name: str = ""

    # Whether the drawer is open.
    drawer_open: bool = False

    # Whether the modal is open.
    modal_open: bool = False

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []

        # Toggle the modal.
        self.modal_open = False

    def toggle_modal(self):
        """Toggle the new chat modal."""
        self.modal_open = not self.modal_open

    def toggle_drawer(self):
        """Toggle the drawer."""
        self.drawer_open = not self.drawer_open

    def delete_chat(self):
        """Delete the current chat."""
        del self.chats[self.current_chat]
        if len(self.chats) == 0:
            self.chats = DEFAULT_CHATS
        self.current_chat = list(self.chats.keys())[0]
        self.toggle_drawer()

    def set_chat(self, chat_name: str):
        """Set the name of the current chat.

        Args:
            chat_name: The name of the chat.
        """
        self.current_chat = chat_name
        self.toggle_drawer()

    @rx.var
    def chat_titles(self) -> list[str]:
        """Get the list of chat titles.

        Returns:
            The list of chat names.
        """
        return list(self.chats.keys())

    async def process_question(self, form_data: dict[str, str]):
        # Get the question from the form
        question = form_data["question"]

        # Check if the question is empty
        if question == "":
            return

        async for value in self.process_question_model(question):
            yield value

    async def process_question_model(self, question: str):
        """Get the response from the API.

        Args:
            form_data: A dict with the current question.
        """

        # Add the question to the list of questions.
        qa = QA(question=question, answer="")
        self.chats[self.current_chat].append(qa)

        # Clear the input and start the processing.
        self.processing = True
        yield

        # Build the messages.
        messages = [
            {"role": "system", "content": "You are a friendly chatbot named Reflex."}
        ]
        for qa in self.chats[self.current_chat]:
            messages.append({"role": "user", "content": qa.question})
            messages.append({"role": "assistant", "content": qa.answer})

        # Remove the last mock answer.
        messages = messages[:-1]

        response = zephyr_rag.query(messages[-1]["content"])
        # Stream the results, yielding after every word.

        import requests

        url = "https://www.dummy.me"

        for item in response:
            if item[0] == "text":
                answer_text = item[1]
                json_request = {"content": answer_text}
                # post_request = requests.post(url, json = json_request)
                self.chats[self.current_chat][-1].answer += "Generating responses..."
                yield
        text_responses = ["Fulfilling request..."]
        for text in text_responses:
            # self.chats[self.current_chat][-1].answer += text
            response_qa = QA(question="", answer=text)
            response_qa.answer_only = True
            self.chats[self.current_chat].append(response_qa)

        # Toggle the processing flag.
        self.processing = False
