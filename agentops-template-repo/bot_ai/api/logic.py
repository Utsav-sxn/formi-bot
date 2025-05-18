def handle_state(state, user_input, context):
    if state == "capture_location":
        return capture_location(user_input, context)
    elif state == "capture_user_details":
        return capture_user_details(user_input, context)
    elif state == "inform_customer":
        return inform_customer(user_input, context)
    # Add other states...

    return "I'm not sure how to proceed.", context

def capture_location(user_input, context):
    outlets = get_available_outlets()
    matched = next((o for o in outlets if o in user_input), None)

    if not matched:
        return (
            f"Sorry, we don’t have any BBQ Nation outlet in that area. Would you like to try another location?",
            {"state": "capture_location"}
        )
    
    context.update({"location": matched, "state": "capture_user_details"})
    return f"Great! You’re looking for BBQ Nation in {matched}, correct?", context

def capture_user_details(user_input, context):
    if not context.get("name"):
        context["name"] = user_input.title()
        return "Thanks! Could you now share your 10-digit phone number?", context

    phone = re.sub(r"\D", "", user_input)
    if len(phone) != 10:
        return "That doesn't seem to be a valid 10-digit number. Please try again.", context

    context["phone"] = phone
    context["state"] = "confirm_reservation"
    return f"Thanks, {context['name']}! Your number is {phone}, right?", context

def inform_customer(user_input, context):
    location = context.get("location", "")
    outlet_info = get_outlet_info(location)
    return f"{outlet_info['name']} is open from {outlet_info['timings']}. Want me to help with a booking?", context
