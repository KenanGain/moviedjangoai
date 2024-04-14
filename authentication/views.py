from django.shortcuts import redirect, render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate,login,logout
from django.http import HttpResponse
# Create your views here.
def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]
        password = request.POST["password"]
        
        # Check if the username already exists
        if User.objects.filter(username=username).exists():
            # You can return an error message here
            return render(request, "authentication/register.html", {
                'error': "Username already exists. Please choose a different one."
            })
        
        # If the username does not exist, create the user
        user = User.objects.create_user(username=username, email=email, password=password)
        login(request, user)
        return render(request, "home/index.html")  # Redirect to a home page or another appropriate page

    else:
        return render(request, "authentication/register.html")
def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")
        user = authenticate(request, username=username, password=password)

        if user is not None:
            login(request, user)
            return render(request, "home/index.html")# Assuming you have a URL name 'home' that points to 'home/index.html'
        else:
            # Return an error message to the login template
            return render(request, "authentication/login.html", {
                'error': 'Invalid username or password. Please try again.'
            })
    else:
        return render(request, "authentication/login.html")
    
def logout_view(request):
    logout(request)
    return render(request, "home/index.html")