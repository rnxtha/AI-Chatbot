import json
import os
import requests
import tempfile
import subprocess
import sys
from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

from .models import Conversation, Message

def signup_view(request):
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        password_confirm = data.get('password_confirm')
        
        if password != password_confirm:
            return render(request, 'signup.html', {'error': 'Passwords do not match.'})
        
        if User.objects.filter(username=username).exists():
            return render(request, 'signup.html', {'error': 'Username already exists.'})
            
        user = User.objects.create_user(username=username, password=password)
        login(request, user)
        return redirect('index')
        
    return render(request, 'signup.html')

def login_view(request):
    if request.method == 'POST':
        data = request.POST
        username = data.get('username')
        password = data.get('password')
        
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('index')
        else:
            return render(request, 'login.html', {'error': 'Invalid username or password.'})
            
    return render(request, 'login.html')

def logout_view(request):
    logout(request)
    return redirect('login')


@login_required(login_url='login')
def index(request):
    conversations = Conversation.objects.filter(user=request.user).order_by('-created_at')
    
    conversation_id = request.GET.get('c')
    
    if conversation_id and conversation_id != 'new':
        try:
            active_conversation = Conversation.objects.get(id=conversation_id, user=request.user)
        except Conversation.DoesNotExist:
            active_conversation = None
    else:
        # Default to a new, empty conversation
        active_conversation = None
        
    messages = active_conversation.messages.all().order_by('timestamp') if active_conversation else []
    
    return render(request, 'chat.html', {
        'conversations': conversations,
        'active_conversation': active_conversation,
        'messages': messages
    })

@csrf_exempt
@login_required(login_url='login')
def api_chat(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get('message')
            conversation_id = data.get('conversation_id')
            
            if not user_message:
                return JsonResponse({'error': 'Message is empty'}, status=400)
                
            # Handle conversation
            if conversation_id:
                conversation = Conversation.objects.get(id=conversation_id, user=request.user)
            else:
                conversation = Conversation.objects.create(
                    user=request.user, 
                    title=user_message[:30] + '...' if len(user_message) > 30 else user_message
                )
            
            # Save user message
            Message.objects.create(conversation=conversation, role='user', content=user_message)
            
            # Get Groq API key from .env file securely
            GROQ_API_KEY = os.environ.get('GROQ_API_KEY', '')
            
            # Build conversation history
            recent_msgs = conversation.messages.order_by('timestamp')
            system_instruction = "You are RN AI. Speak in a very simple, conversational, and easy-to-understand way. Avoid overly complex jargon. Use bullet points and paragraphs to make your answers easy to read. Always format code using markdown blocks."
            
            if GROQ_API_KEY:
                # === GROQ API (Llama 3) ===
                messages_payload = [{"role": "system", "content": system_instruction}]
                
                for msg in list(recent_msgs):
                    if msg.content:
                        # Append the history so the AI has context
                        messages_payload.append({
                            "role": msg.role,
                            "content": msg.content
                        })
                
                url = "https://api.groq.com/openai/v1/chat/completions"
                headers = {
                    "Authorization": f"Bearer {GROQ_API_KEY}",
                    "Content-Type": "application/json"
                }
                payload = {
                    "model": "llama-3.3-70b-versatile",
                    "messages": messages_payload,
                    "temperature": 0.7,
                    "max_tokens": 1500
                }
                
                try:
                    response = requests.post(url, headers=headers, json=payload, timeout=30)
                    
                    if response.status_code == 200:
                        response_data = response.json()
                        assistant_message = response_data['choices'][0]['message']['content']
                    elif response.status_code == 429:
                        assistant_message = "⚠️ Groq Rate limit reached. Slow down your requests."
                    else:
                        error_data = response.json()
                        error_msg = error_data.get('error', {}).get('message', response.text[:200])
                        print(f"Groq API Error ({response.status_code}): {error_msg}")
                        assistant_message = f"⚠️ API Error: {error_msg}"
                        
                except requests.exceptions.Timeout:
                    assistant_message = "⚠️ Request timed out. Please try again."
                except Exception as e:
                    print(f"Groq Exception: {e}")
                    assistant_message = f"⚠️ Core System Error: {str(e)}"
            
            else:
                assistant_message = "⚠️ Core Identity Offline: No API key configured."
            
            # Save assistant message
            Message.objects.create(conversation=conversation, role='assistant', content=assistant_message)
            
            return JsonResponse({
                'message': assistant_message,
                'conversation_id': conversation.id,
                'title': conversation.title
            })
            
        except Exception as e:
            return JsonResponse({'error': str(e)}, status=500)
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@csrf_exempt
@login_required(login_url='login')
def api_run_code(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            code = data.get('code', '')
            stdin_data = data.get('stdin', '')
            
            if not code.strip():
                return JsonResponse({'output': 'Error: No code provided to run.'})
                
            # Write code to a secure temporary execution file
            with tempfile.NamedTemporaryFile(suffix='.py', mode='w', delete=False, encoding='utf-8') as f:
                f.write(code)
                temp_path = f.name
                
            try:
                # Safely execute python script using the exact same python environment 
                result = subprocess.run([sys.executable, temp_path], input=stdin_data, capture_output=True, text=True, timeout=10)
                
                output = result.stdout
                if result.stderr:
                    output += "\n[Code Execution Error]\n" + result.stderr
                    
                if not output.strip():
                    output = "[Code executed successfully with no print output]"
                    
            except subprocess.TimeoutExpired:
                output = "Runtime Error: Execution artificially terminated. Code timed out after 10 seconds."
            finally:
                # Cleanup the ephemeral disk file manually
                if os.path.exists(temp_path):
                    os.remove(temp_path)
                    
            return JsonResponse({'output': output})
        except Exception as e:
            return JsonResponse({'output': f'Server Error: {str(e)}'})
            
    return JsonResponse({'error': 'Invalid request method'}, status=405)
