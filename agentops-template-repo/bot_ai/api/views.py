import json
import os
import re
import uuid
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

DATA_PATH = os.path.join(settings.BASE_DIR, 'api', 'data/knowledge_chunks.json')
try:
    with open(DATA_PATH, 'r', encoding='utf-8') as f:
        knowledge_chunks = json.load(f)
except Exception:
    knowledge_chunks = []

city_outlets = {
    'bangalore': ['indiranagar', 'koramangala','Electronic city'],
    'delhi': ['janakpuri', 'connaught place'],
}

def home(request):
    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>BBQ Chatbot</title>
        <style>
            body { font-family: Arial, sans-serif; background: #f9f9f9; padding: 2rem; }
            .chat-container { max-width: 600px; margin: auto; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 10px rgba(0,0,0,0.1); }
            .chat-box { min-height: 150px; border: 1px solid #ddd; padding: 10px; border-radius: 5px; background: #fff; margin-bottom: 10px; overflow-y: auto; }
            .bot, .user { margin: 10px 0; }
            .bot { color: #333; background: #eef; padding: 10px; border-radius: 8px; display: inline-block; }
            .user { text-align: right; font-weight: bold; }
            button { padding: 10px 15px; border: none; background: #007bff; color: white; border-radius: 5px; cursor: pointer; }
            button:hover { background: #0056b3; }
            input[type="text"] { width: 100%; padding: 10px; border-radius: 5px; border: 1px solid #ccc; }
        </style>
    </head>
    <body>
        <div class="chat-container">
            <h2>Location Chatbot</h2>
            <div class="chat-box" id="chatBox"></div>
            <input type="text" id="userInput" placeholder="Enter details" style="display:none;">
            <button id="startBtn" onclick="startChat()">Start</button>
            <button id="sendBtn" onclick="sendMessage()" style="display:none;">Send</button>
        </div>

        <script>
            const chatBox = document.getElementById('chatBox');
            const userInput = document.getElementById('userInput');
            const startBtn = document.getElementById('startBtn');
            const sendBtn = document.getElementById('sendBtn');

            function addMessage(sender, text) {
                const div = document.createElement('div');
                div.className = sender;
                div.innerHTML = text;
                chatBox.appendChild(div);
                chatBox.scrollTop = chatBox.scrollHeight;
            }

            function startChat() {
                startBtn.style.display = 'none';
                userInput.style.display = 'block';
                sendBtn.style.display = 'inline-block';
                addMessage('bot', 'Hi! Please enter your location or address:');
                userInput.focus();
            }

            async function sendMessage() {
                const query = userInput.value.trim();
                if (!query) return;

                addMessage('user', query);
                userInput.value = '';

                try {
                    const response = await fetch('/chatbot_api/', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ message: query })
                    });
                    const data = await response.json();
                    addMessage('bot', data.response);
                } catch (e) {
                    addMessage('bot', 'Error processing request.');
                }
            }
        </script>
    </body>
    </html>
    """
    return HttpResponse(html)

@csrf_exempt
def search(request):
    query = request.GET.get('q', '').strip().lower()
    if not query:
        return JsonResponse({"error": "Missing query parameter ?q="}, status=400)

    matched = []
    available_locations = set()

    known_cities = ['bangalore','new delhi', 'mumbai', 'pune', 'chennai', 'hyderabad', 'kolkata', 'janakpuri']

    for chunk in knowledge_chunks:
        content = chunk.get('content', '').lower()
        for city in known_cities:
            if city in content:
                available_locations.add(city.title())

    for chunk in knowledge_chunks:
        content = chunk.get('content', '').lower()
        if query in content:
            matched.append({
                "content": chunk.get('content', ''),
                "city": query.title()
            })

    if matched:
        return JsonResponse({"response": matched})
    else:
        return JsonResponse({"response": [], "available_locations": sorted(available_locations)})


@csrf_exempt
def chatbot_api(request):
    if request.method != 'POST':
        return JsonResponse({"response": "Send a POST request with your message."})

    try:
        data = json.loads(request.body)
    except Exception:
        return JsonResponse({"response": "Invalid JSON."})

    user_msg = data.get('message', '').strip()
    if not user_msg:
        return JsonResponse({"response": "Please type something."})

    step = request.session.get('step', 'ask_location')

    def is_valid_phone(number):
        digits = re.sub(r'\D', '', number)
        return len(digits) == 10 and digits.isdigit()

    if step == 'ask_location':
        city = user_msg.lower()
        if city in city_outlets:
            request.session['location'] = city.title()
            request.session['step'] = 'ask_outlet'
            outlets_list = city_outlets[city]
            outlets_str = ', '.join([outlet.title() for outlet in outlets_list])
            return JsonResponse({
                "response": (
                    f"Great! You're looking for a BBQ outlet in {city.title()} — is that right? "
                    f"Here are the available outlets: {outlets_str}. "
                    f"Please specify which outlet you'd like to book."
                )
            })
        else:
            return JsonResponse({"response": f"Sorry, we don't have BBQ outlets in {city.title()} yet. Please enter another city."})

    elif step == 'ask_outlet':
        outlet = user_msg.lower()
        city = request.session.get('location', '').lower()
        if city and outlet in city_outlets.get(city, []):
            request.session['outlet'] = outlet.title()
            request.session['step'] = 'ask_name'
            return JsonResponse({"response": f"Thanks! May I please have your name?"})
        else:
            outlets_list = city_outlets.get(city, [])
            outlets_str = ', '.join([o.title() for o in outlets_list])
            return JsonResponse({
                "response": f"Sorry, we don't have an outlet named '{user_msg.title()}' in {city.title()}. "
                            f"Available outlets: {outlets_str}. Please specify one."
            })

    elif step == 'ask_name':
        refusals = ['no', 'prefer not to say', 'skip', 'nah']
        if user_msg.lower() in refusals:
            request.session['name'] = None
            request.session['step'] = 'ask_phone'
            return JsonResponse({"response": "Thanks, no problem. Could you share your 10-digit phone number clearly?"})
        else:
            request.session['name'] = user_msg.title()
            request.session['step'] = 'ask_phone'
            return JsonResponse({"response": f"Thanks, {user_msg.title()}. Could you share your 10-digit phone number clearly?"})

    elif step == 'ask_phone':
        if not is_valid_phone(user_msg):
            return JsonResponse({"response": "Please provide a valid 10-digit phone number."})
        request.session['phone'] = re.sub(r'\D', '', user_msg)
        request.session['step'] = 'confirm_details'
        name = request.session.get('name') or "there"
        phone = request.session['phone']
        return JsonResponse({"response": f"So, just to confirm, your name is {name} and your number is {phone} — is that correct?"})

    elif step == 'confirm_details':
        if user_msg.lower() in ['yes', 'correct', 'yup', 'right']:
            request.session['step'] = 'booking_pax'
            return JsonResponse({"response": "Thanks for confirming! How many people (pax) will be attending?"})
        else:
            request.session['step'] = 'ask_name'
            return JsonResponse({"response": "Okay, let's update your details. May I have your name again?"})

    elif step == 'booking_pax':
        if user_msg.isdigit() and 1 <= int(user_msg) <= 50:
            request.session['booking_pax'] = int(user_msg)
            request.session['step'] = 'booking_time'
            return JsonResponse({
                "response": "At what time would you like to book? Please provide the time in HH:MM format (24-hour)."
            })
        else:
            return JsonResponse({"response": "Please provide a valid number of people (1-50)."})

    elif step == 'booking_time':
        if re.match(r"^(?:[01]\d|2[0-3]):[0-5]\d$", user_msg):
            request.session['booking_time'] = user_msg
            booking_id = str(uuid.uuid4())[:8]
            request.session['booking_id'] = booking_id
            request.session['step'] = 'booking_confirm'

            outlet = request.session.get('outlet', 'Unknown Outlet')
            pax = request.session.get('booking_pax', 0)
            time = request.session.get('booking_time', 'Unknown Time')
            name = request.session.get('name', 'Guest')

            return JsonResponse({
                "response": (
                    f"Thanks {name}! Your booking for {pax} people at {outlet} at {time} is noted. "
                    f"Your booking ID is {booking_id}. You can use this ID to cancel your booking if needed. "
                    "Please confirm with 'yes' to finalize or 'no' to cancel."
                )
            })
        else:
            return JsonResponse({
                "response": "Please provide time in HH:MM 24-hour format (e.g., 18:30)."
            })

    elif step == 'booking_confirm':
        if user_msg.lower() in ['yes', 'y']:
            booking_id = request.session.get('booking_id')
            request.session.flush()
            return JsonResponse({
                "response": f"Your booking is confirmed! Your booking ID is {booking_id}. Thank you for choosing our BBQ outlets."
            })
        elif user_msg.lower() in ['no', 'n']:
            request.session.flush()
            return JsonResponse({
                "response": "Your booking request has been canceled. If you'd like to start over, please enter your location or address."
            })
        else:
            return JsonResponse({
                "response": "Please respond with 'yes' to confirm or 'no' to cancel the booking."
            })

    else:
        request.session['step'] = 'ask_location'
        return JsonResponse({"response": "Hi! Please enter your location or address."})
