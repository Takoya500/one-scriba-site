import os
from django.conf import settings
from django.contrib import messages
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

# Lazy import of supabase client; requires `supabase-py` installed in the environment
try:
    from supabase import create_client
except Exception:
    create_client = None

def home(request):
    return render(request, "home.html")


def pricing(request):
    return render(request, "pricing.html")


def magazine(request):
    return render(request, "magazine.html")


def autori(request):
    return render(request, "autori.html")


def autore(request, id):
    # in futuro questo può caricare dati reali dal DB
    context = {"author_id": id}
    return render(request, "autore.html", context)


def festival(request):
    return render(request, "festival.html")


def affiliazioni(request):
    return render(request, "affiliazioni.html")


def learn_more(request):
    return render(request, "learn_more.html")


def download(request):
    return render(request, "download.html")


def _get_supabase_client():
    url = os.environ.get('SUPABASE_URL') or getattr(settings, 'SUPABASE_URL', None)
    key = os.environ.get('SUPABASE_KEY') or getattr(settings, 'SUPABASE_KEY', None)
    if not url or not key:
        return None
    if create_client is None:
        return None
    return create_client(url, key)


@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Signup using Supabase Auth. Stores minimal user info and access token in session on success."""
    client = _get_supabase_client()
    if request.method == 'POST':
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        if not client:
            messages.error(request, "Client Supabase non configurato.")
            return render(request, 'signup.html', {'name': name, 'email': email})
        try:
            # supabase-py: sign_up requires dict or kwargs depending on version
            res = client.auth.sign_up({"email": email, "password": password})
            # res may contain 'user' and 'data' depending on version
            if hasattr(res, 'user') and res.user:
                user = res.user
            else:
                user = res.get('user') if isinstance(res, dict) else None

            # If confirmation required, still redirect to login with message
            if user:
                # store minimal info in session
                session_info = {'id': user.get('id') if isinstance(user, dict) else getattr(user, 'id', None),
                                'email': user.get('email') if isinstance(user, dict) else getattr(user, 'email', None),
                                }
                request.session['supabase_user'] = session_info
                # try to sign in immediately to obtain access token
                try:
                    auth = client.auth.sign_in_with_password({"email": email, "password": password})
                    access_token = None
                    if isinstance(auth, dict):
                        access_token = auth.get('access_token') or (auth.get('data') or {}).get('access_token')
                    else:
                        access_token = getattr(auth, 'access_token', None)
                    if access_token:
                        request.session['supabase_access_token'] = access_token
                except Exception:
                    pass

                return redirect('dashboard')
            else:
                # show friendly message
                messages.success(request, "Registrazione avvenuta. Controlla la tua email per confermare (se richiesto).")
                return redirect('login')
        except Exception as e:
            msg = str(e)
            # sanitize common Supabase errors
            if 'already exists' in msg or 'duplicate' in msg:
                messages.error(request, "Questa email è già registrata.")
            else:
                messages.error(request, msg)
            return render(request, 'signup.html', {'name': name, 'email': email})
    return render(request, 'signup.html')


@require_http_methods(["GET", "POST"])
def login_view(request):
    client = _get_supabase_client()
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        if not client:
            messages.error(request, "Client Supabase non configurato.")
            return render(request, 'login.html', {'email': email})
        try:
            res = client.auth.sign_in_with_password({"email": email, "password": password})
            # extract access token and user
            access_token = None
            user = None
            if isinstance(res, dict):
                access_token = res.get('access_token') or (res.get('data') or {}).get('access_token')
                user = (res.get('user') or (res.get('data') or {}).get('user'))
            else:
                access_token = getattr(res, 'access_token', None)
                user = getattr(res, 'user', None)

            if access_token:
                request.session['supabase_access_token'] = access_token
            if user:
                request.session['supabase_user'] = {'id': user.get('id') if isinstance(user, dict) else getattr(user, 'id', None), 'email': user.get('email') if isinstance(user, dict) else getattr(user, 'email', None), 'name': (user.get('user_metadata') or {}).get('full_name') if isinstance(user, dict) else None}
            if not user and not access_token:
                messages.error(request, "Credenziali non valide.")
                return render(request, 'login.html', {'email': email})
            return redirect('dashboard')
        except Exception as e:
            msg = str(e)
            messages.error(request, msg)
            return render(request, 'login.html', {'email': email})
    return render(request, 'login.html')


def logout_view(request):
    # Clear supabase session info
    request.session.pop('supabase_user', None)
    request.session.pop('supabase_access_token', None)
    return redirect('home')


def dashboard_view(request):
    client = _get_supabase_client()
    user = request.session.get('supabase_user')
    access_token = request.session.get('supabase_access_token')
    if not user or not access_token:
        return redirect('login')

    # try to fetch subscription status from Supabase table `subscriptions`
    subscription_status = 'none'
    try:
        if client:
            # Attempt to query subscriptions by user id (assumes column user_id)
            user_id = user.get('id')
            if user_id:
                resp = client.table('subscriptions').select('*').eq('user_id', user_id).limit(1).execute()
                data = None
                if isinstance(resp, dict):
                    data = resp.get('data')
                else:
                    data = getattr(resp, 'data', None)
                if data:
                    row = data[0] if isinstance(data, list) and len(data) else data
                    # expect a column named subscription_status or status
                    subscription_status = row.get('subscription_status') or row.get('status') or 'none'
    except Exception:
        subscription_status = 'none'

    context = {
        'user': user,
        'subscription_status': subscription_status,
    }
    return render(request, 'dashboard.html', context)


@csrf_exempt
def lemonsqueezy_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed.'}, status=405)
    return JsonResponse({'ok': True})
