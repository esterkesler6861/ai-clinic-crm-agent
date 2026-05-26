from graph import graph


state = {
    "user_input": "where is my order 111",
    "request_type": None,
    "order_id": None,
    "refund_id": None,
    "answer": None,
    "status": None,
    "waiting_for_order_id": False,
    "waiting_for_refund_id": False,
}
state = graph.invoke(state)

print("FIRST RESULT:")
print(state)


state["user_input"] = "111"

state = graph.invoke(state)

print("SECOND RESULT:")
print(state)