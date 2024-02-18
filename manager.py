from uagents import Agent, Bureau, Context, Model
from protocol import MessageRequest, MessageResponse, message_proto

class Message(Model):
    message: str

# master agent
manager = Agent(name="Manager", seed=f"manager recovery phrase")

# dummy clients
client_agents = {}
clients = [
    ("Mike", 9999999999),
    ("Stanley", 8888888888),
    ("Guru", 7777777777)
]

bureau = Bureau()
bureau.add(manager)


def add_client(name, phone):
    client_agents[name] = Agent(name=name, seed=f"{name} recovery phrase")
    bureau.add(client_agents[name])
    @client_agents[name].on_message(model=Message)
    async def message_handler(ctx: Context, sender: str, msg: MessageRequest):
        ctx.logger.info(f"{ctx.name} received message: {msg.message}")

for name, phone in clients:
    add_client(name, phone)
#mike = client_agents["Mike"]
#stanley = Agent(name="Stanley", seed="Stanley recovery phrase")
#guru = Agent(name="Guru", seed="Guru recovery phrase")
"""
bureau.add(mike)
bureau.add(stanley)
bureau.add(guru)

@mike.on_message(model=Message)
async def mike_message_handler(ctx: Context, sender: str, msg: MessageRequest):
    ctx.logger.info(f"{ctx.name} received message from {sender}: {msg.message}")
    return MessageResponse(response_text="Hello from Mike!")

@stanley.on_message(model=Message)
async def stanley_message_handler(ctx: Context, sender: str, msg: MessageRequest):
    ctx.logger.info(f"{ctx.name} received message from {sender}: {msg.message}")
    return MessageResponse(response_text="Hello from Stanley!")

@guru.on_message(model=Message)
async def guru_message_handler(ctx: Context, sender: str, msg: MessageRequest):
    ctx.logger.info(f"{ctx.name} received message from {sender}: {msg.message}")
    return MessageResponse(response_text="Hello from Guru!")
"""

@manager.on_interval(period=3)
async def start_handler(ctx: Context):
    for name, agent in client_agents.items():
        await ctx.send(agent.address, Message(message=f"Hello, {name}!"))
    # await ctx.send(mike.address, Message(message="Hello, Mike!"))
    # await ctx.send(stanley.address, Message(message="Hello, Stanley!"))
    # await ctx.send(guru.address, Message(message="Hello, Guru!"))    

if __name__ == "__main__":
    bureau.run()



