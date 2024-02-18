from uagents import Agent, Context, Model
from uagents.setup import fund_agent_if_low
 
class Message(Model):
    message: str
 
RECIPIENT_ADDRESS="agent1qfjcg2h5c2d2qkzksc8wntkpcyflntz0w8lsh2q6nwqpe6a2dn5ps88aqq3"
 
sigmar = Agent(
    name="sigmar",
    port=8001,
    seed="sigmar secret phrase",
    endpoint=["http://0.0.0.0:8001/submit"],
)
 
fund_agent_if_low(sigmar.wallet.address())
 
@sigmar.on_interval(period=10.0)
async def send_message(ctx: Context):
    await ctx.send(RECIPIENT_ADDRESS, Message(message=input("prompt:")))
 
@sigmar.on_message(model=Message)
async def message_handler(ctx: Context, sender: str, msg: Message):
    ctx.logger.info(f"Received message from {sender}: {msg.message}")
 
if __name__ == "__main__":
    sigmar.run()