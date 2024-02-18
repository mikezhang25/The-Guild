from uagents import Agent, Context
alice = Agent(name="alice", seed="alice recovery phrase")

# set event triggers for actions
@alice.on_event("startup")
async def say_hello(ctx: Context):
    ctx.logger.info(f'hello, my name is {ctx.name}')

# set periodic events (in seconds) using storage counter
@alice.on_interval(period=1.0)
async def on_interval(ctx: Context):
    current_count = ctx.storage.get("count") or 0
 
    ctx.logger.info(f"My count is: {current_count}")
 
    ctx.storage.set("count", current_count + 1)

 
if __name__ == "__main__":
    alice.run()