from typing import List
 
from uagents import Context, Model, Protocol
 
# Define models for the restaurant table management system
# TableStatus: Represents the status of a table including seats, start time, and end time
# QueryTableRequest: Represents a request to query tables based on number of guests, start time, and duration
# QueryTableResponse: Represents the response to a query, listing available table IDs
# GetTotalQueries: Represents a request to get the total number of table queries made
# TotalQueries: Represents the response with the total number of queries
# query_proto: Protocol instance for handling query messages

class TableStatus(Model):
    seats: int
    time_start: int
    time_end: int
 
class QueryTableRequest(Model):
    guests: int
    time_start: int
    duration: int
 
class QueryTableResponse(Model):
    tables: List[int]
 
class GetTotalQueries(Model):
    pass
 
class TotalQueries(Model):
    total_queries: int
query_proto = Protocol()
 
# Define handlers for query requests and total queries
# handle_query_request: Asynchronously handles table query requests, checking table availability and responding
# handle_get_total_queries: Asynchronously handles requests for the total number of queries, responding with the count
@query_proto.on_message(model=QueryTableRequest, replies=QueryTableResponse)
async def handle_query_request(ctx: Context, sender: str, msg: QueryTableRequest):
    # Convert stored table data into TableStatus objects, filtering out non-integer keys
    tables = {
        int(num): TableStatus(**status)
        for (
            num,
            status,
        ) in ctx.storage._data.items()
        if isinstance(num, int)
    }
    available_tables = []
    # Check each table for availability based on the request parameters
    for number, status in tables.items():
        if (
            status.seats >= msg.guests  # Enough seats for the guests
            and status.time_start <= msg.time_start  # Available at the requested start time
            and status.time_end >= msg.time_start + msg.duration  # Available for the entire duration
        ):
            available_tables.append(int(number))
    # Log the query and the resulting available tables
    ctx.logger.info(f"Query: {msg}. Available tables: {available_tables}.")
    # Respond to the sender with the available tables
    await ctx.send(sender, QueryTableResponse(tables=available_tables))
    # Increment and store the total number of queries
    total_queries = int(ctx.storage.get("total_queries") or 0)
    ctx.storage.set("total_queries", total_queries + 1)
 
@query_proto.on_query(model=GetTotalQueries, replies=TotalQueries)
async def handle_get_total_queries(ctx: Context, sender: str, _msg: GetTotalQueries):
    total_queries = int(ctx.storage.get("total_queries") or 0)
    await ctx.send(sender, TotalQueries(total_queries=total_queries))