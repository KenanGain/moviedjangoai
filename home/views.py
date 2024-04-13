from django.shortcuts import redirect, render
import requests
from django.http import HttpResponse
from django.http import JsonResponse
from .models import Review
from django.contrib.auth.models import User
from django.conf import settings
import json
import pandas
import joblib
import pandas as pd

api_key = "c887d2e670d1e01224b4cd27ccf79d31"


from django import template

register = template.Library()

@register.filter
def humanize_money(value):
    try:
        value = int(value)
        if value < 1000000:
            return f"${value:,}"
        elif value < 1000000000:
            return f"${value / 1000000:.1f} million"
        else:
            return f"${value / 1000000000:.1f} billion"
    except (ValueError, TypeError):
        return value
    
import json  # Ensure json is imported

def openai(openaiapi_key, prompt, model="gpt-4-turbo-preview", max_tokens=4096, temperature=1):
    api_url = 'https://api.openai.com/v1/chat/completions'
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {openaiapi_key}'
    }
    openaidata = {
        'model': model,
        "messages": [{"role": "user", "content": prompt}],
        'max_tokens': max_tokens,
        'temperature': temperature,
    }
    try:
        openairesponse = requests.post(api_url, headers=headers, json=openaidata)  # Changed data to json
        openairesponse.raise_for_status()  # This will raise an exception for 4xx/5xx errors
        response_json = openairesponse.json()
        if "choices" in response_json and len(response_json["choices"]) > 0:
            # Corrected path to extract generated text
            generated_text = response_json['choices'][0]['message']['content']
            return generated_text
        else:
            return "No response generated."
    except requests.exceptions.RequestException as e:
        return f"Request failed: {e}"


def search(request):
    query = request.GET.get('q')
    results = []
    if query:
        # Construct the URL for searching movies with the query
        url = f"https://api.themoviedb.org/3/search/movie?api_key={api_key}&query={query}"
        data = requests.get(url)
        if data.status_code == 200:
            temp = []
            for m in data.json()["results"]:
                    temp.append({"name":m["title"], "poster":m["poster_path"], "overview":m["overview"], "releasedate":m["release_date"],"id":m["id"] })
            results.append(temp) if len(temp)> 0 else None

        else:
            # Handle API errors
            return HttpResponse(f"TMDB API Error: {data.status_code}", status=data.status_code)
    else:
        # Handle case where no search query was provided
        return HttpResponse("Please enter a search query.")

    # Render the template with the list of movies
    return render(request, 'home/results.html', {
        "results": results,
        "query":query
    })

# Your index view
def index(request):
    return render(request, 'home/index.html')

def view_detail(request, id):
    # Initial TMDB API Call
    tmdb_data = requests.get(f"https://api.themoviedb.org/3/movie/{id}?api_key={api_key}&language=en-US").json()
    tmdb_cast = requests.get(f"https://api.themoviedb.org/3/movie/{id}/credits?api_key={api_key}&language=en-US").json()
    moviegenxrec=recommend(id)
    # Prepare variables
    title = tmdb_data.get("title", "").replace(' ', '_')
    release_date = tmdb_data.get("release_date", "")
    revenue = tmdb_data.get("revenue", "No Data")
    new_revenue = humanize_money(revenue) if revenue != "No Data" else revenue
    # actors = [actor['name'] for actor in tmdb_cast['cast'][:5]]
    actors_info = []
    for actor in tmdb_cast['cast'][:5]:  # Limiting to top 5 actors
        actor_name = actor['name']
        profile_path = actor.get('profile_path', '')
        actors_info.append({"name": actor_name, "image_url": profile_path})

    
    # Wikipedia API Calls
    if title and release_date:
        release_year = release_date.split("-")[0]
        wiki_responses = []
        for suffix in [f"_{release_year}_film", "_(film)"]:
            search_query = f"{title}{suffix}"
            wiki_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{search_query}"
            response = requests.get(wiki_url)
            if response.status_code == 200:
                wiki_responses.append(response.json().get("extract", ""))
            else:
                wiki_responses.append(f"Could not fetch details from Wikipedia for {search_query}")
    
    # Ensure all necessary data is collected
    if tmdb_data and all(wiki_responses):
        prompt = (
            "you are an amazing AI assistant which only provides good movie descriptions using this knowledge base: "
            + " ".join([title, tmdb_data.get("overview", "")] + wiki_responses + [str(revenue)])
        )
        openaiapi_key = "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"
        ai_summary = openai(openaiapi_key,prompt)
    return render(request, 'home/detail.html', {
                "data": tmdb_data,
                "id":id,
                "ai_summary": ai_summary,
                "revenue": new_revenue,
                "cast": actors_info,
                "moviegenxrec":moviegenxrec
    })
 
def review_page(request, movie_id):
    if request.method == "POST":
        user = request.user
        review = request.POST.get("review")

        if not request.user.is_authenticated:
            user = User.objects.get(username='AnonymouseUser')
        Review(review=review, user=user, movie_id=movie_id).save()

        return redirect(f"/movie/{movie_id}/review/")
    else:
        # return render(request, "home/review.html")
        tmdbdata = requests.get(f"https://api.themoviedb.org/3/movie/{movie_id}?api_key={api_key}&language=en-US")
        # return JsonResponse(data.json())
        data = tmdbdata.json()
        title = data.get("title","")
        review = Review.objects.filter(movie_id=movie_id)
        return render(request, "home/review.html", {
            "title": title,
            "review": review
        })
    

def recommend(movie_id):
    # Assume 'movies' is a pandas DataFrame and 'similarity' is a similarity matrix loaded into your Django app
    if movie_id in movies['movie_id'].values:
        movie_index = movies[movies['movie_id'] == movie_id].index[0]
        distances = similarity[movie_index]
        movies_list = sorted(list(enumerate(distances)), reverse=True, key=lambda x: x[1])[1:6]  # Top 5 recommendations

        detailed_movies = []
        for index, _ in movies_list:
            movie_info = movies.iloc[index]
            movie_data = recommendation_details(movie_info['movie_id'])
            if movie_data:
                detailed_movies.append(movie_data)

        return detailed_movies
    else:
        return []
    
def recommendation_details(id):
    moviegenxdata = requests.get(f"https://api.themoviedb.org/3/movie/{id}?api_key={api_key}&language=en-US").json()
    return moviegenxdata

movies_path = settings.RESOURCES_DIR / 'movies.joblib'
similarity_path = settings.RESOURCES_DIR / 'similarity.joblib'

# Load the joblib files
movies = joblib.load(movies_path)
similarity = joblib.load(similarity_path)

# Ensure movies is a DataFrame
movies = pd.DataFrame(movies)
movies_titles = movies['movie_id'].values




