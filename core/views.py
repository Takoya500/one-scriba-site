import os
import json
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


def privacy_policy(request):
    return render(request, "privacy_policy.html")


def terms_of_service(request):
    return render(request, "terms_of_service.html")


def contact(request):
    return render(request, "contact.html")


def _get_supabase_auth_client():
    from supabase import create_client
    import os

    url = os.environ.get("PROJECT_URL") or os.environ.get("SUPABASE_URL")
    key = os.environ.get("SUPABASE_KEY")

    if not url or not key:
        return None

    return create_client(url, key)


def _get_supabase_admin_client():
    from supabase import create_client
    import os

    url = os.environ.get("PROJECT_URL") or os.environ.get("SUPABASE_URL")
    key = os.environ.get("SERVICE_ROLE_KEY") or os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

    if not url or not key:
        return None

    return create_client(url, key)


@require_http_methods(["GET", "POST"])
def signup_view(request):
    """Signup using Supabase Auth. Stores minimal user info and access token in session on success."""
    client = _get_supabase_auth_client()
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
    client = _get_supabase_auth_client()
    if request.method == 'POST':
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        if not client:
            messages.error(request, "Client Supabase non configurato.")
            return render(request, 'login.html', {'email': email})
        try:
            res = client.auth.sign_in_with_password({"email": email, "password": password})
            # Extract access token and user across supabase-py response shapes
            access_token = None
            user = None

            if isinstance(res, dict):
                data = res.get('data') or {}
                session_data = res.get('session') or data.get('session') or {}
                access_token = (
                    res.get('access_token')
                    or data.get('access_token')
                    or session_data.get('access_token')
                )
                user = (
                    res.get('user')
                    or data.get('user')
                    or session_data.get('user')
                )
            else:
                session_obj = getattr(res, 'session', None)
                access_token = (
                    getattr(res, 'access_token', None)
                    or getattr(session_obj, 'access_token', None)
                )
                user = (
                    getattr(res, 'user', None)
                    or getattr(session_obj, 'user', None)
                )

            # Login is valid only if BOTH are present, to match dashboard checks
            if not user or not access_token:
                messages.error(request, "Credenziali non valide.")
                return render(request, 'login.html', {'email': email})

            request.session['supabase_access_token'] = access_token
            request.session['supabase_user'] = {
                'id': user.get('id') if isinstance(user, dict) else getattr(user, 'id', None),
                'email': user.get('email') if isinstance(user, dict) else getattr(user, 'email', None),
                'name': (user.get('user_metadata') or {}).get('full_name') if isinstance(user, dict) else None,
            }
            request.session.modified = True
            request.session.save()

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
    client = _get_supabase_admin_client()
    user = request.session.get('supabase_user')
    access_token = request.session.get('supabase_access_token')
    if not user or not access_token:
        return redirect('login')

    subscription_status = 'inactive'
    subscription = None
    customer_portal_url = None
    try:
        if client:
            email = (user.get('email') if isinstance(user, dict) else None) or ''
            email = email.strip().lower()
            if email:
                query = client.table('subscriptions').select('*').eq('email', email)
                try:
                    query = query.order('created_at', desc=True)
                except Exception:
                    pass
                resp = query.limit(1).execute()
                if isinstance(resp, dict):
                    data = resp.get('data')
                else:
                    data = getattr(resp, 'data', None)
                if isinstance(data, list) and data:
                    subscription = data[0]
                elif isinstance(data, dict):
                    subscription = data

            if subscription and str(subscription.get('status', '')).strip().lower() == 'active':
                subscription_status = 'active'
                raw_payload = subscription.get('raw_payload') if isinstance(subscription, dict) else None
                if isinstance(raw_payload, dict):
                    customer_portal_url = (
                        ((raw_payload.get('data') or {}).get('attributes') or {}).get('urls') or {}
                    ).get('customer_portal')
    except Exception:
        subscription_status = 'inactive'
        subscription = None
        customer_portal_url = None

    context = {
        'user': user,
        'subscription_status': subscription_status,
        'subscription': subscription,
        'customer_portal_url': customer_portal_url,
    }
    return render(request, 'dashboard.html', context)


@require_http_methods(["GET"])
def check_subscription_view(request):
    user = request.session.get('supabase_user')
    access_token = request.session.get('supabase_access_token')
    if not user or not access_token:
        return JsonResponse({"status": "unauthorized"}, status=401)

    email = (user.get('email') if isinstance(user, dict) else None) or ''
    email = email.strip().lower()
    if not email:
        return JsonResponse({"status": "inactive"})

    try:
        client = _get_supabase_admin_client()
        if not client:
            return JsonResponse({"status": "error"})

        query = client.table('subscriptions').select('*').eq('email', email)
        try:
            query = query.order('created_at', desc=True)
        except Exception:
            pass

        resp = query.limit(1).execute()
        if isinstance(resp, dict):
            data = resp.get('data')
        else:
            data = getattr(resp, 'data', None)

        subscription = None
        if isinstance(data, list) and data:
            subscription = data[0]
        elif isinstance(data, dict):
            subscription = data

        if not subscription:
            return JsonResponse({"status": "inactive"})

        if str(subscription.get('status', '')).strip().lower() == 'active':
            return JsonResponse({
                "status": "active",
                "renews_at": subscription.get('renews_at'),
                "ends_at": subscription.get('ends_at'),
            })

        return JsonResponse({"status": "inactive"})
    except Exception:
        return JsonResponse({"status": "error"})


@csrf_exempt
@require_http_methods(["POST"])
def desktop_login_view(request):
    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse(
            {"status": "error", "message": "Missing email or password"},
            status=400,
        )

    if not isinstance(payload, dict):
        return JsonResponse(
            {"status": "error", "message": "Missing email or password"},
            status=400,
        )

    email = str(payload.get("email", "")).strip()
    password = str(payload.get("password", ""))

    if not email or not password:
        return JsonResponse(
            {"status": "error", "message": "Missing email or password"},
            status=400,
        )

    try:
        client = _get_supabase_auth_client()
        if not client:
            return JsonResponse({"status": "error"}, status=500)

        try:
            auth_response = client.auth.sign_in_with_password({"email": email, "password": password})
        except Exception as exc:
            message = str(exc).lower()
            if any(token in message for token in ["invalid", "credential", "unauthorized", "login"]):
                return JsonResponse(
                    {"status": "unauthorized", "message": "Invalid credentials"},
                    status=401,
                )
            return JsonResponse({"status": "error"}, status=500)

        auth_user = None
        if isinstance(auth_response, dict):
            data = auth_response.get("data") or {}
            session_data = auth_response.get("session") or data.get("session") or {}
            auth_user = auth_response.get("user") or data.get("user") or session_data.get("user")
        else:
            session_obj = getattr(auth_response, "session", None)
            auth_user = getattr(auth_response, "user", None) or getattr(session_obj, "user", None)

        user_email = None
        if isinstance(auth_user, dict):
            user_email = auth_user.get("email")
        else:
            user_email = getattr(auth_user, "email", None)

        normalized_email = (user_email or email).strip().lower()
        if not normalized_email:
            return JsonResponse(
                {"status": "unauthorized", "message": "Invalid credentials"},
                status=401,
            )

        db_client = _get_supabase_admin_client()
        if not db_client:
            return JsonResponse({"status": "error"}, status=500)

        query = db_client.table("subscriptions").select("*").eq("email", normalized_email)
        try:
            query = query.order("created_at", desc=True)
        except Exception:
            pass

        response = query.limit(1).execute()
        if isinstance(response, dict):
            data = response.get("data")
        else:
            data = getattr(response, "data", None)

        subscription = None
        if isinstance(data, list) and data:
            subscription = data[0]
        elif isinstance(data, dict):
            subscription = data

        if subscription and str(subscription.get("status", "")).strip().lower() == "active":
            return JsonResponse(
                {
                    "status": "active",
                    "email": normalized_email,
                    "renews_at": subscription.get("renews_at"),
                    "ends_at": subscription.get("ends_at"),
                    "offline_valid_days": 30,
                },
                status=200,
            )

        return JsonResponse(
            {
                "status": "inactive",
                "email": normalized_email,
            },
            status=200,
        )
    except Exception:
        return JsonResponse({"status": "error"}, status=500)


@csrf_exempt
def lemonsqueezy_webhook(request):
    if request.method != 'POST':
        return JsonResponse({'detail': 'Method not allowed.'}, status=405)
    return JsonResponse({'ok': True})
