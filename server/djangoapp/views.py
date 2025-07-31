from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import logging
import json

from .models import CarModel
from .populate import initiate
from .restapis import get_request, analyze_review_sentiments

# Get an instance of a logger
logger = logging.getLogger(__name__)


# Create your views here.

def get_cars(request):
    initiate()  # force run
    car_models = CarModel.objects.select_related('car_make')
    cars = [
        {"CarModel": cm.name, "CarMake": cm.car_make.name} for cm in car_models
        ]
    return JsonResponse({"CarModels": cars})


# Handle sign in request
@csrf_exempt
def login_user(request):
    if request.method == "POST":
        try:
            data = json.loads(request.body)
            username = data.get('userName')
            password = data.get('password')

            user = authenticate(username=username, password=password)

            if user is not None:
                login(request, user)
                return JsonResponse({
                    "userName": user.username,
                    "status": "Authenticated"
                })
            else:
                return JsonResponse({
                    "status": "Unauthorized",
                    "message": "Invalid username or password"
                }, status=401)

        except json.JSONDecodeError:
            return JsonResponse({
                "status": "Bad Request",
                "message": "Invalid JSON"
            }, status=400)
        except Exception as e:
            logger.error(f"Login error: {str(e)}")
            return JsonResponse({
                "status": "Error",
                "message": "An error occurred during login"
            }, status=500)

    return JsonResponse({
        "status": "Method Not Allowed",
        "message": "Only POST requests are allowed"
    }, status=405)


# Handle sign out request
def logout_user(request):
    logout(request)
    return JsonResponse({"userName": ""})


# Handle user registration
@csrf_exempt
def registration(request):
    data = json.loads(request.body)
    username = data['userName']
    password = data['password']
    first_name = data['firstName']
    last_name = data['lastName']
    email = data['email']
    username_exist = False

    try:
        User.objects.get(username=username)
        username_exist = True
    except Exception:
        logger.debug(f"{username} is new user")

    if not username_exist:
        user = User.objects.create_user(
            username=username,
            first_name=first_name,
            last_name=last_name,
            password=password,
            email=email
        )
        login(request, user)
        return JsonResponse({"userName": username, "status": "Authenticated"})
    else:
        return JsonResponse(
            {"userName": username, "error": "Already Registered"}
            )


# List dealerships (optionally filtered by state)
def get_dealerships(request, state="All"):
    endpoint = "/fetchDealers" if state == "All" else f"/fetchDealers/{state}"
    dealerships = get_request(endpoint)
    return JsonResponse({"status": 200, "dealers": dealerships})


# Render the reviews of a dealer
def get_dealer_reviews(request, dealer_id):
    if dealer_id:
        endpoint = f"/fetchReviews/dealer/{dealer_id}"
        reviews = get_request(endpoint)
        for review in reviews:
            response = analyze_review_sentiments(review['review'])
            review['sentiment'] = response.get('sentiment', 'neutral')
        return JsonResponse({"status": 200, "reviews": reviews})
    return JsonResponse({"status": 400, "message": "Bad Request"})


# Render the dealer details
def get_dealer_details(request, dealer_id):
    if dealer_id:
        endpoint = f"/fetchDealer/{dealer_id}"
        dealership = get_request(endpoint)
        return JsonResponse({"status": 200, "dealer": dealership})
    return JsonResponse({"status": 400, "message": "Bad Request"})


# Submit a review
@csrf_exempt
def add_review(request):
    if request.method == "POST":
        data = json.loads(request.body)
        print("Review received:", data)
        return JsonResponse({"message": "Review received"}, status=200)
    return JsonResponse({"error": "Invalid method"}, status=400)
