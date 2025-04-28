import asyncio

user_states = {}

def set_product_selection(user_id, value):
    if user_id not in user_states:
        user_states[user_id] = {
            "product": {"event": asyncio.Event(), "value": None},
            "confirmation": {"event": asyncio.Event(), "value": None}
        }
    user_states[user_id]["product"]["value"] = value
    user_states[user_id]["product"]["event"].set()
    print(f"✅ set_product_selection: {user_id} -> {value}")

def set_order_confirmation(user_id, value):
    if user_id not in user_states:
        user_states[user_id] = {
            "product": {"event": asyncio.Event(), "value": None},
            "confirmation": {"event": asyncio.Event(), "value": None}
        }
    user_states[user_id]["confirmation"]["value"] = value
    user_states[user_id]["confirmation"]["event"].set()
    print(f"✅ set_order_confirmation: {user_id} -> {value}")

async def wait_for_product_selection(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            "product": {"event": asyncio.Event(), "value": None},
            "confirmation": {"event": asyncio.Event(), "value": None}
        }

    try:
        await asyncio.wait_for(user_states[user_id]["product"]["event"].wait(), timeout=30)
        value = user_states[user_id]["product"]["value"]

        # ✅ Clear only AFTER successful wait
        user_states[user_id]["product"]["event"].clear()
        user_states[user_id]["product"]["value"] = None

        print(f"📥 wait_for_product_selection returned: {value}")
        return value

    except asyncio.TimeoutError:
        user_states[user_id]["product"]["event"].clear()
        user_states[user_id]["product"]["value"] = None
        print(f"⏰ wait_for_product_selection timeout")
        return "skip"

async def wait_for_order_confirmation(user_id):
    if user_id not in user_states:
        user_states[user_id] = {
            "product": {"event": asyncio.Event(), "value": None},
            "confirmation": {"event": asyncio.Event(), "value": None}
        }

    try:
        await asyncio.wait_for(user_states[user_id]["confirmation"]["event"].wait(), timeout=30)
        value = user_states[user_id]["confirmation"]["value"]

        # ✅ Clear only AFTER successful wait
        user_states[user_id]["confirmation"]["event"].clear()
        user_states[user_id]["confirmation"]["value"] = None

        print(f"📥 wait_for_order_confirmation returned: {value}")
        return value

    except asyncio.TimeoutError:
        user_states[user_id]["confirmation"]["event"].clear()
        user_states[user_id]["confirmation"]["value"] = None
        print(f"⏰ wait_for_order_confirmation timeout")
        return "skip"
