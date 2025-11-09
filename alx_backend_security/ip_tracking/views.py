from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.http import HttpResponse
from ratelimit.decorators import ratelimit

# Create your views here.

# limit anonymous users: 5 requests/minute
# limit authenticated users: 10 requests/minute
@ratelimit(key='ip', rate='5/m', method='POST', block=True)
@ratelimit(key='user_orip', rate='10/m', method='POST', block=True)
def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect('home')
        else:
            return HttpResponse("Invalide credentials", status=401)

    return render(request, 'login.html')
