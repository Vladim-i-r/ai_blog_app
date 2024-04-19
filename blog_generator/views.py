from django.shortcuts import render
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
from django.conf import settings
import json, os
from pytube import YouTube
import assemblyai as aai
#import openai
from .models import BlogPost

# Create your views here.
@login_required
def index(request):
    return render(request, 'index.html')

@csrf_exempt
def generate_blog(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body) #This body calls the json body from the js script
            yt_link = data['link']  # link is how it was named on the script so we specify that
            # return JsonResponse({'content': yt_link})
        except (KeyError, json.JSONDecodeError):
            return JsonResponse({'error':'Invalid request method'}, status=400)
        
        #? get title
        title = yt_title(yt_link)

        #? get transcript and show it
        transcription = get_transcription(yt_link)
        blog_content = transcription                    #HERE WE USE THE TRANSCRIPTION AS IT IS FROM ASSEMBLY AI TO DISPLAY IT
        if not blog_content:                            #transcription
            return JsonResponse({'error':'Failed to get transcript'}, status=500)

        #! 'INCLUDES PRICING' use OpenAI to generate the blog, if willing to pay, delete blog_content variable form on top and change if not transcription and uncomment whats under this
        # blog_content = generate_blog_from_transcription(transcription)
        # if not blog_content:
        #     return JsonResponse({'error':'Failed to generate blog article'}, status=500)

        #? save blog article to database
        new_blog_article = BlogPost.objects.create(
            user = request.user,
            youtube_title = title,
            youtube_link = yt_link,
            generated_content=blog_content
        )
        new_blog_article.save()

        #? return blog article as a response
        return JsonResponse({'content': blog_content})


    else:
        return JsonResponse({'error':'Invalid request method'}, status=405)

def yt_title(link):
    yt = YouTube(link)
    title = yt.title
    return title

def download_audio(link):
    yt = YouTube(link)
    video = yt.streams.filter(only_audio=True).first()
    out_file = video.download(output_path=settings.MEDIA_ROOT)  #IT WILL BE SAVED IN THIS FOLDER
    base, ext = os.path.splitext(out_file)
    new_file = base + '.mp3'
    os.rename(out_file, new_file)
    return new_file

def get_transcription(link):
    audio_file = download_audio(link)
    aai.settings.api_key = ''    #ADD ASSEMBLY API

    transcriber = aai.Transcriber()
    transcript = transcriber.transcribe(audio_file)

    if transcript.status == aai.TranscriptStatus.error:
        print(transcript.error)
    else:
        print(transcript.text)

    return transcript.text

#! INCLUDES PRICING
# def generate_blog_from_transcription(transcription):  
     #openai.api_key = ""  #Place here the api key for the openai
     
#    prompt = f"Based on the following transcript from a YouTube video, write a comprehensive blog article, write it based on the transcript, but dont make it look like a youtube video, make it look like a proper blog article:\n\n{transcription}\n\nArticle:"

#    response = openai.completions.create(
#     #  model="text-davinci-003",
#        model="gpt-3.5-turbo-instruct",
#        prompt=prompt,
#        max_tokens=1000
#    )

#    generated_content = response.choices[0].text.strip()  # Gets the text that we need
#    return generated_content

def blog_list(request):
    blog_articles = BlogPost.objects.filter(user=request.user)
    return render(request, 'all-blogs.html', {'blog_articles':blog_articles})

def blog_details(request, ok):
    blog_article_detail = BlogPost.objects.get(id=ok)
    if request.user == blog_article_detail.user:
        return render(request, 'blog-details.html', {'blog_article_detail':blog_article_detail})
    else: 
        return redirect('/')

def user_login(request):
    if request.method == 'POST':
        username = request.POST['username']  
        password = request.POST['password']

        user = authenticate(request, username=username, password=password)
        if user is not None: 
            login(request, user)
            return redirect('/')
        else: 
            error_message = 'Invalid username or password'
            return render(request, 'login.html', {'error_message':error_message} )
    return render(request, 'login.html')

def user_signup(request):
    if request.method == 'POST':
        username = request.POST['username']
        email = request.POST['email']
        password = request.POST['password']
        repeatPassword = request.POST['repeatPassword']

        if password == repeatPassword:
            try: 
                user = User.objects.create_user(username, email, password)
                user.save()
                login(request, user)
                return redirect('/')
            except: 
                error_message = 'Error creating account'
                return render(request, 'signup.html', {'error_message':error_message})

            pass
        else:
            error_message = 'Password do NOT match'
            return render(request, 'signup.html', {'error_message':error_message})
        
    return render(request, 'signup.html')

def user_logout(request):
    logout(request)
    
    return redirect('/')