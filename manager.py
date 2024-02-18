from uagents import Agent, Bureau, Context, Model
from uagents.setup import fund_agent_if_low

from rag_src.zephyr_rag import ZephyrRAG

API_ENDPT = "http://localhost:3001"
FRONT_END_ADDR = "agent1qvwqu6a0km09mq4f6j6kmke9smswmgcergmml9a54av9449rqtmmxy4qwe6"
company = "Sand Hill Pharmaceuticals"

import requests
import asyncio

async def send_message(phone_number, message):
    try:
        payload = {'phoneNumber': phone_number, 'message': message}
        response = requests.post(f"{API_ENDPT}/send-message", json=payload)
        if response.status_code == 200:
            print(f"Message sent successfully to {phone_number}")
        else:
            print(f"Failed to send message to {phone_number}: {response.json().get('error')}")
    except Exception as e:
        print(f"Exception occurred while sending message to {phone_number}: {str(e)}")

def fetch_phone_numbers():
    try:
        response = requests.get(f"{API_ENDPT}/phone-numbers")
        print(f"Responses: {response}")
        phone_numbers = response.json()
        print(f"Fetched phone numbers: {phone_numbers}")
        return phone_numbers or []
    except Exception as e:
        print(f"Failed to fetch phone numbers: {str(e)}")

def fetch_messages(phone_number):
    try:
        response = requests.get(f"{API_ENDPT}/fetch-messages/{phone_number}")
        messages = response.json()
        print(f"Messages for {phone_number}: {messages}")
        return messages or []
    except Exception as e:
        print(f"Failed to fetch messages for {phone_number}: {str(e)}")

class Manager:
    def __init__(self, bureau, data_path, clients) -> None:
        print(f"Initializing Manager")
        self.agent = Agent(name="Manager", seed=f"manager recovery phrase")
        fund_agent_if_low(self.agent.wallet.address())
        self.bureau = bureau
        self.rag = ZephyrRAG(
            model="zephyr-7b-beta",
            temperature=0.75,
            context_window=1024,
            embed_model="local:BAAI/bge-small-en-v1.5",
            init_data_path=data_path
            )
        self.rag.start_rag()
        bureau.add(self.agent)
        self.clients = clients
    
        @self.agent.on_event("startup")
        async def start_handler(ctx: Context):
            for client in self.clients:
                await ctx.send(client.agent.address, Message(message=f"Establishing manager contact"))
        
        @self.agent.on_message(model=OnBoard)
        async def onboard_client(ctx: Context, sender: str, msg: OnBoard):
            ctx.logger.info(f"Registering new client with number {msg.phone}")
            client_data_path = f"{base_path}/data/clients/{msg.phone}"
            if not os.path.exists(client_data_path):
                os.makedirs(client_data_path)
                with open(os.path.join(client_data_path, "chat.txt"), "w") as chat_file:
                    chat_file.write("")
            newClient = Client(msg.phone, msg.phone, self.bureau, client_data_path)
            self.clients.append(newClient)
            send_message(msg.number, newClient.rag.query(f"""
                You are the owner of a business. There is a new client. Here's some context:
                !START OF CONTEXT! {msg.context} !END OF CONTEXT!

                You must craft a two-sentence welcome text, that embodies at least one key idea from the context.
                Remember, your output must STRICTLY BE TWO SENTENCES! Begin your output with "Welcome".
            """))
        
        @self.agent.on_message(model=Message)
        async def message_handler(ctx: Context, sender: str, message: Message):
            print(f"Received message: {message.message}")
            # generate template
            user_prompt = message.message
            user_template = self.rag.query(f"""
                Generate a general response to a customer based on the following instructions from {company}.
                
                Instructions: \"\"\"{user_prompt}\"\"\"

                Your response is a text message, it should be worded in that manner.
                """).response
            #user_template = "boilerplate template"
            print(f"Generated template: {user_template}")
            # send combined prompt and prompt
            for client in self.clients:
                await ctx.send(client.agent.address, Directive(template=user_template, prompt=user_prompt))             
    
    def refresh_clients(self):
        for client in self.clients:
            fetch_messages(client.phone)
    
    def add_prompt(self, prompt):
        self.prompt_buffer.append(prompt)
        self.send_directive()
    
class Client:
    def __init__(self, name, phone, bureau, chat_path) -> None:
        print(f"Initializing {name}")
        self.agent = Agent(name=name, seed=f"{name} recovery phrase")
        self.agent.storage.set("phone", phone)
        fund_agent_if_low(self.agent.wallet.address())
        bureau.add(self.agent)
        self.rag = ZephyrRAG(
            model="zephyr-7b-beta",
            temperature=0.75,
            context_window=1024,
            embed_model="local:BAAI/bge-small-en-v1.5",
            init_data_path=chat_path
            )
        self.rag.start_rag()
        self.refresh_chat()
        @self.agent.on_message(model=Message)
        async def message_handler(ctx: Context, sender: str, msg: Message):
            ctx.logger.info(f"{ctx.name} received message: {msg.message}")
        
        @self.agent.on_message(model=Directive)
        async def directive_handler(ctx: Context, sender: str, msg: Directive):
            # TODO: call API to refresh chat history in data/[name]
            fits_prompt = self.rag.query(f"""
                You are the representative for a customer.
                As a representative, your job is to filter out requests to contact your customer from business owners.
                In order to filter the requests, you use the chat history of the customer to decide if they would be interested in the request of the business owner.
                In your output, you strictly write a ONE SENTENCE explanation of why you arrived at that conclusion, that starts with either a "YES" or a "NO".
                
                Here are 3 examples:
                1) The business owner makes a request to advertise dog food and you allow (YES) this request because the chat history of your customer indicates the customer has a dog.
                2) The business owner makes a request to advertise a new lotion and you deny (NO) this request because the chat history of your customer indicates they already bought the item.
                3) The business owner makes a request to update all his customers about his hours for the long weekend and you allow (YES) this request because the chat history of your customer indicates they have shopped at that business before.
                
                Now, the business owner makes a request:
                {msg.prompt}
                
                How would you filter this request? Remember, your ONE SENTENCE output explanation should strictly start with a YES or NO.
                

                """).response
            print(fits_prompt)
            await ctx.send(FRONT_END_ADDR, Justification(fits_prompt))
            if 'yes' in fits_prompt.lower().split()[0]:
                ctx.logger.info(f"{ctx.name} matches directive {msg.prompt}")

                # refresh phone number cache
                self.refresh_chat()

                message = self.rag.query(f"""
                    You are a senior customer relationship manager at {company} and your are customer focused.
                    Your job is to write text messages to customers.
                    All you know about the customer is their chat history, so you ALWAYS connect your response with the chat history.
                    You are given a prompt and template for the text message from your boss. 
                    Given the following prompt, PERSONALIZE the template message according to the chat history.
                    Some strategies you use are mentioning conversational details and appealing to their interests. 
                    At all costs, do not mention details that were not provided verbatim in the prompt. 
                    
                    Here is the Prompt: \"\"\" {msg.prompt} \"\"\"
                    Here is the Template: \"\"\" {msg.template} \"\"\"

                    Remember, your text message should read well and BE DIRECTED TO THE CUSTOMER.
                    Generate your text message response.
                """).response
                # TODO: send out using WhatsApp
                ctx.logger.info(f"Personalized message: {message}")
                await send_message(self.agent.storage.get("phone"), message)
                await ctx.send(FRONT_END_ADDR, Message(message))
            else:
                ctx.logger.info("Did not match prompt")
            
    def refresh_chat(self):
        phone_number = self.agent.storage.get("phone")
        new_messages = fetch_messages(phone_number)
        chat_path = f"./data/clients/{self.agent.name}/chat.txt"
        with open(chat_path, "w") as chat_file:
            for message in new_messages:
                chat_file.write(f"{message}\n")
        print("Refreshed chat history")

class Directive(Model):
    template: str
    prompt: str

class Message(Model):
    message: str

class Justification(Model):
    message: str

class OnBoard(Model):
    phone: int
    context: str

import os
current_path = os.getcwd()
base_path = current_path.split("TreeHacks2024")[0] + "TreeHacks2024"
class Application:
    def __init__(self):
        self.bureau = Bureau(port=8001, endpoint=["http://0.0.0.0:8001/submit"])
        
        self.clients = []
        self.load_clients()
        self.manager = Manager(self.bureau, f"{base_path}/data/business", self.clients)
    
    def load_clients(self):
        client_numbers = fetch_phone_numbers()        
        for phone in client_numbers:
            print(f"Returning user {phone}")
            client_data_path = f"{base_path}/data/clients/{phone}"
            if not os.path.exists(client_data_path):
                os.makedirs(client_data_path)
                with open(os.path.join(client_data_path, "chat.txt"), "w") as chat_file:
                    chat_file.write("")  # Create an empty chat.txt file
            self.clients.append(Client(str(phone), phone, self.bureau, client_data_path))

    def run(self):
        print(self.manager.agent.address)
        # self.manager.add_prompt("Fix this problem please")
        self.bureau.run()

if __name__ == "__main__":
    app = Application()
    app.run()
    print("bruh")
    app.manager.add_prompt("Respectfully, please work. Otherwise I will kill you.")

    #manager.send_directive("I want to launch a new line of shampoo, assess interest amongst teenagers.")


"""
def send_directive(self):
        # self.prompt_buffer.append(input("prompt: "))
        print(self.prompt_buffer)
        if len(self.prompt_buffer) > 0:
            # generate template
            user_prompt = self.prompt_buffer[0]
            self.prompt_buffer.pop(0)
            user_template = self.rag.query(f"Generate a general customer outreach template for the following prompt from {company}. \n\n Prompt: \"\"\"{user_prompt}\"\"\"").response
            #user_template = "boilerplate template"
            print(f"Generated template: {user_template}")
            # send combined prompt and prompt
            for client in self.clients:
                asyncio.run(self.agent._ctx.send(client.agent.address, Directive(template=user_template, prompt=user_prompt)))
                # await ctx.send(client.agent.address, Directive(template=user_template, prompt=user_prompt))
"""