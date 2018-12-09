# EC601_Miniproject_1
This project is to grab pictures from twitter, convert those pictures into video and analyse the content of the video using Google Vision API. 

Please run this file in Python3.6 and make sure you have all the packages below:
- tweepy
- requests
- ffmpeg
- subprocrss
- google.cloud
- pillow

This file contains three functions: twitter_api, make_video and video_analysis.
Twitter API is used for grabing pics from certain twitter account and the library "requests" is downloaded pics. 
"ffmeg" in make_video is used to convert pics into video. Some of the pics are needed to be resized in order to make the convertion successfully. 
Google.vision.videointelligence is an API that could analyse the content of a video.
