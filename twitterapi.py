# Zhangming Chen zmchen26@bu.edu
import tweepy
import os
import requests
import ffmpeg
import io
import subprocess
from google.cloud import videointelligence
from PIL import Image

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/zhangmingchen/desktop/directed-truck-224723-e8fd8af459c9.json"

consumer_key = "enter consumer key"
consumer_secret = "enter consumer secrete"
access_key = "enter access key"
access_secret = "enter access secrete"

auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
auth.set_access_token(access_key, access_secret)
api = tweepy.API(auth)

os.makedirs('./twitterpic', exist_ok=True)

def twitter_api(screen_name):
    auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
    auth.set_access_token(access_key, access_secret)
    api = tweepy.API(auth)

    alltweets = []
    new_tweets = api.user_timeline(screen_name=screen_name, count=10)
    alltweets.extend(new_tweets)
    oldest = alltweets[-1].id - 1

    while len(new_tweets) > 0:
        print("getting tweets before %s" % oldest)
        new_tweets = api.user_timeline(screen_name=screen_name, count=30, max_id=oldest)
        alltweets.extend(new_tweets)
        oldest = alltweets[-1].id - 1
        print("...%s tweets downloaded so far" % len(alltweets))
        if len(alltweets)>50:
            break

    pic_url = []
    for tweet in alltweets:
        try:
            tweet.entities['media'][0]['media_url'] == True
        except (NameError, KeyError):
            pass
        else:
            pic_url.append(tweet.entities['media'][0]['media_url'])

    for pic_index in range(len(pic_url)):
        file_name = 'pic_' + str(pic_index) + '.jpg'
        r = requests.get(pic_url[pic_index])
        with open('./twitterpic/%s' %file_name, 'wb') as f:
            for chunk in r.iter_content(chunk_size=32):
                f.write(chunk)

    return len(pic_url)


def make_video(screen_name, pic_num):
    for i in range(pic_num):
        pic = Image.open('./twitterpic/pic_' + str(i) + '.jpg').resize([500,500])
        pic.save('./twitterpic/pic_' + str(i) + '.jpg')
    subprocess.run(['ffmpeg','-f','image2', '-i', './twitterpic/%*.jpg', '-r', '48', './twitterpic/%s.mp4'%screen_name])


def video_analysis(screen_name):
    video_client = videointelligence.VideoIntelligenceServiceClient()
    features = [videointelligence.enums.Feature.LABEL_DETECTION]

    video_path = os.path.join('./twitterpic/' + '%s' %screen_name + '.mp4')
    with io.open(video_path, 'rb') as video:
        inputContent = video.read()

    operation = video_client.annotate_video(features=features, input_content=inputContent)
    print('\nProcessing video for label annotations:')
    result = operation.result(timeout=90)
    print('\nFinished processing.')

    # first result is retrieved because a single video was processed
    segment_labels = result.annotation_results[0].segment_label_annotations
    for i, segment_label in enumerate(segment_labels):
        print('video label description: {}'.format(segment_label.entity.description))
        for category_entity in segment_label.category_entities:
            print('\rLabel category description: {}'.format(category_entity.description))


if __name__ == '__main__':
    screen_name = '@taylorswift13'
    # screen_name = '@vangoghartist'
    pic_num = twitter_api(screen_name)
    make_video(screen_name, pic_num)
    video_analysis(screen_name)

