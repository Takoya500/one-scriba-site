# from django.utils import translation

# class ForceLanguageMiddleware:
#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Controlla se nell'URL c'è ?lang=en o ?lang=it
#         lang = request.GET.get('lang')
#         if lang:
#             # Attiva la lingua richiesta
#             translation.activate(lang)
#             request.LANGUAGE_CODE = lang
#         # Prosegui con la risposta normale
#         response = self.get_response(request)
#         return response
