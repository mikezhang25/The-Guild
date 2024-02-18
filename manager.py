from uagents import Agent, Bureau, Context, Model
from zephyr_rag import ZephyrRAG

class Manager:
    def __init__(self, bureau, data_path, clients) -> None:
        print(f"Initializing Manager")
        self.prompt_buffer = []
        self.agent = Agent(name="Manager", seed=f"manager recovery phrase")
        self.rag = ZephyrRAG(
            model="zephyr-7b-beta",
            temperature=0.75,
            context_window=1024,
            embed_model="local:BAAI/bge-small-en-v1.5",
            data_path=data_path
            )
        self.rag.run()
        bureau.add(self.agent)
        self.clients = clients
    
        @self.agent.on_event("startup")
        async def start_handler(ctx: Context):
            for client in self.clients:
                await ctx.send(client.agent.address, Message(message=f"Establishing manager contact"))

        @self.agent.on_interval(period=1)    
        async def send_directive(ctx: Context):
            if len(self.prompt_buffer) > 0:
                # generate template
                user_prompt = self.prompt_buffer[0]
                self.prompt_buffer.pop(0)
                user_template = self.rag.query(f"Generate a general customer outreach template for the following prompt from Mike: {user_prompt}").response
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
            data_path=chat_path
            )
        self.rag.run()
        @self.agent.on_message(model=Message)
        async def message_handler(ctx: Context, sender: str, msg: Message):
            ctx.logger.info(f"{ctx.name} received message: {msg.message}")
        
        @self.agent.on_message(model=Directive)
        async def directive_handler(ctx: Context, sender: str, msg: Directive):
            fits_prompt = self.rag.query(f"Does {ctx.name} express the smallest possibility of matching the prompt {msg.prompt} given their chat history? Please begin your answer with exactly a yes or no. If no, please provide 1 sentence explaining why. For all other cases, begin with \"yes\" and do not elaborate further.").response
            print(fits_prompt)
            if 'yes' in fits_prompt.lower():
                ctx.logger.info(f"{ctx.name} received directive {msg.prompt} and template {msg.template}")
                message = self.rag.query(f"Given the directive of {msg.prompt}, personalize this template message for {ctx.name} according to their chat history, taking care to mention conversational details and appealing to their interests. At all costs, do not mention details that were not provided verbatim in the prompt: {msg.template}").response
                # TODO: send out using WhatsApp
                ctx.logger.info(f"Personalized message: {message}")
            else:
                ctx.logger.info("Did not match prompt")
            
class Directive(Model):
    template: str
    prompt: str

class Message(Model):
    message: str    

if __name__ == "__main__":
    bureau = Bureau()
    clients = []
    client_info = [
        ("Mike", 9999999999),
        ("Stanley", 8888888888),
        ("Guru", 7777777777)
    ]
    
    for name, phone in client_info:
        clients.append(Client(name, phone, bureau, f"./data/clients/{name}"))
    
    manager = Manager(bureau, "./data/business", clients)
    manager.add_prompt("I want to launch a new line of moisturizers. Reach out to customers who have expressed any interest in moisturizers at all in the past.")
    bureau.run()
    #manager.send_directive("I want to launch a new line of shampoo, assess interest amongst teenagers.")


