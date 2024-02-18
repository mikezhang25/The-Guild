from uagents import Agent, Bureau, Context, Model
from rag_src.zephyr_rag import ZephyrRAG

company = "Sand Hill Pharmaceuticals"

class Manager:
    def __init__(self, bureau, data_path, clients) -> None:
        print(f"Initializing Manager")
        self.prompt_buffer = []
        self.agent = Agent(name="Manager", seed=f"manager recovery phrase")
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

        @self.agent.on_interval(period=1)    
        async def send_directive(ctx: Context):
            # self.prompt_buffer.append(input("prompt: "))
            if len(self.prompt_buffer) > 0:
                # generate template
                user_prompt = self.prompt_buffer[0]
                self.prompt_buffer.pop(0)
                user_template = self.rag.query(f"Generate a general customer outreach template for the following prompt from {company}. \n\n Prompt: \"\"\"{user_prompt}\"\"\"").response
                #user_template = "boilerplate template"
                print(f"Generated template: {user_template}")
                # send combined prompt and prompt
                for client in self.clients:
                    await ctx.send(client.agent.address, Directive(template=user_template, prompt=user_prompt))       
    
    def add_prompt(self, prompt):
        self.prompt_buffer.append(prompt)
    
class Client:
    def __init__(self, name, phone, bureau, chat_path) -> None:
        print(f"Initializing {name}")
        self.agent = Agent(name=name, seed=f"{name} recovery phrase")
        self.agent.storage.set("phone", phone)
        bureau.add(self.agent)
        self.rag = ZephyrRAG(
            model="zephyr-7b-beta",
            temperature=0.75,
            context_window=1024,
            embed_model="local:BAAI/bge-small-en-v1.5",
            init_data_path=chat_path
            )
        self.rag.start_rag()
        @self.agent.on_message(model=Message)
        async def message_handler(ctx: Context, sender: str, msg: Message):
            ctx.logger.info(f"{ctx.name} received message: {msg.message}")
        
        @self.agent.on_message(model=Directive)
        async def directive_handler(ctx: Context, sender: str, msg: Directive):
            # TODO: call API to refresh chat history in data/[name]
            fits_prompt = self.rag.query(f"Evaluate whether {ctx.name} satisfies the prompt {msg.prompt} given their chat history. Please begin your answer with exactly a yes or no. If no, please provide 1 sentence explaining why. For all other cases, begin with \"yes\" and 1 sentence explaining your decision.\n \[Yes or No\], {ctx.name} ").response
            print(fits_prompt)
            if 'yes' in fits_prompt.lower().split()[0]:
                ctx.logger.info(f"{ctx.name} matches directive {msg.prompt}")
                message = self.rag.query(f"Given the following prompt, personalize the template message for {ctx.name} according to their chat history, taking care to mention conversational details and appealing to their interests. At all costs, do not mention details that were not provided verbatim in the prompt. Embody a senior customer relationship manager at {company} who is deeply devoted to its success. \n\n Prompt: \"\"\" {msg.prompt} \"\"\" Template: \"\"\" {msg.template} \"\"\"\nDear {ctx.name}").response
                # TODO: send out using WhatsApp
                ctx.logger.info(f"Personalized message: {message}")
            else:
                ctx.logger.info("Did not match prompt")
            
class Directive(Model):
    template: str
    prompt: str

class Message(Model):
    message: str    

import os
current_path = os.getcwd()
base_path = current_path.split("TreeHacks2024")[0] + "TreeHacks2024"
class Application:
    def __init__(self):
        self.bureau = Bureau()
        self.clients = []
        self.load_clients()
        self.manager = Manager(self.bureau, f"{base_path}/data/business", self.clients)
    
    def load_clients(self):
        import csv
        client_info = []
        with open(f"{base_path}/clients.csv", mode='r') as csv_file:
            csv_reader = csv.reader(csv_file)
            for row in csv_reader:
                client_info.append((row[0], int(row[1])))
        
        for name, phone in client_info:
            self.clients.append(Client(name, phone, self.bureau, f"{base_path}/data/clients/{name}"))

    def run(self):
        self.bureau.run()

if __name__ == "__main__":
    app = Application()
    app.run()
    #manager.send_directive("I want to launch a new line of shampoo, assess interest amongst teenagers.")


