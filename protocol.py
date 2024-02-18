from uagents import Protocol, Model, Context

class MessageRequest(Model):
    message: str

class MessageResponse(Model):
    response_text: str

message_proto = Protocol()

@message_proto.on_message(model=MessageRequest, replies=MessageResponse)
async def handle_message_request(ctx: Context, sender: str, msg: MessageRequest):
    # Process the message request here
    # For example, simply echo back the received message with some modification
    response_text = f"Received your message: {msg.message}"
    # Log the received message and the response
    ctx.logger.info(f"Received message from {sender}: {msg.message}. Responding with: {response_text}")
    # Send back a response to the sender
    await ctx.send(sender, MessageResponse(response_text=response_text))
