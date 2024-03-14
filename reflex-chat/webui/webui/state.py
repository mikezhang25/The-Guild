import os
import requests
import json
import openai
import reflex as rx
import sys
import asyncio

current_path = os.getcwd()
base_path = current_path.split("TreeHacks2024")[0] + "TreeHacks2024"
sys.path.append(base_path)

from manager import Application
from manager import Message
from manager import OnBoard
from manager import Justification
from rag_src.zephyr_rag import ZephyrRAG
# intialize manager
# manager.run()

from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low
 
import re

def is_ten_numbers(s):
    # Define a regular expression pattern to match exactly 10 digits
    pattern = r'^\d{10}$'
    
    # Use the re.match() function to search for the pattern at the beginning of the string
    # If the pattern matches, return True; otherwise, return False
    return bool(re.match(pattern, s))
 
RECIPIENT_ADDRESS="agent1qfjcg2h5c2d2qkzksc8wntkpcyflntz0w8lsh2q6nwqpe6a2dn5ps88aqq3"
 
sigmar = Agent(
    name="sigmar",
    port=8001,
    seed="sigmar secret phrase",
    endpoint=["http://0.0.0.0:8001/submit"],
)
 
fund_agent_if_low(sigmar.wallet.address())
 
@sigmar.on_interval(period=2.0)
async def send_message(ctx: Context):
    await ctx.send(RECIPIENT_ADDRESS, Message(message="deez nuts"))
 
@sigmar.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")

print(sigmar.address)
 

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

    explain_bar_open: bool = True

    def initialize_manager(self):
        manager.run()

    def create_chat(self):
        """Create a new chat."""
        # Add the new chat to the list of chats.
        self.current_chat = self.new_chat_name
        self.chats[self.new_chat_name] = []
        self.manager = self.initialize_manager()
        self.explain_bar_open = False

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
        message_content = messages[-1]["content"]

        phone_numbers_response = requests.get("http://localhost:3001/phone-numbers")
        phone_numbers = phone_numbers_response.json()

        for phone_number in phone_numbers:
            messages_response = requests.get(f"http://localhost:3001/fetch-messages/{phone_number}")
            messages = str(messages_response.json())

            openai.api_key = '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'

            # Combining the context into a single string for the model
            prompt = f"Instruction for the small business owner: {question}\n\nConversation history:\n{messages}\n\nNext message the small business owner should send:"

            response = openai.Completion.create(
            engine="gpt-4",
            prompt=prompt,
            max_tokens=150,  # You can adjust the number of tokens based on your needs
            temperature=0.7,  # Adjust for creativity. Lower is more deterministic.
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
            )

            # Extracting and printing the generated message
            generated_message = response.choices[0].text.strip()
            print(generated_message)

            # Send the generated message to the phone number using the send-message endpoint
            send_message(phone_number, generated_message)


        # reach out to a new customer if we have key word new customer
        # if "new customer" in message_content.lower():
        #     import re

        #     # Define a regular expression pattern to match exactly 10 digits
        #     pattern = r'\b\d{10}\b'
            
        #     # Use the re.search() function to find the pattern in the message content
        #     match = re.search(pattern, message_content)
            
        #     phone_number = match.group()
        #     await sigmar._ctx.send(RECIPIENT_ADDRESS, OnBoard(phone=phone_number, context=f"{message_content}"))
        # else:
        #     await sigmar._ctx.send(RECIPIENT_ADDRESS, Message(message = message_content))
        # response = zephyr_rag.query(messages[-1]["content"])
        # Stream the results, yielding after every word.

        # import requests

        # url = "https://www.dummy.me"

        # for item in response:
        #     if item[0] == "text":
        #         answer_text = item[1]
        #         json_request = {"content": answer_text}
        #         # post_request = requests.post(url, json = json_request)
        #         self.chats[self.current_chat][-1].answer += "Generating responses..."
        #         yield
        text_responses = ["Fulfilling request..."]
        self.chats[self.current_chat][-1].answer += "Generating responses..."
        for text in text_responses:
            response_qa = QA(question="", answer=text)
            response_qa.answer_only = True
            self.chats[self.current_chat].append(response_qa)

        # Toggle the processing flag.
        self.processing = False
