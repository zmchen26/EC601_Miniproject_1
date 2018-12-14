# Zhangming Chen zmchen26@bu.edu
import tweepy
import os
import requests
import ffmpeg
import io
import subprocess
from google.cloud import videointelligence
from PIL import Image
import mysql.connector
from mysql.connector import errorcode, connection
import platform
import getpass
import datetime

os.environ["GOOGLE_APPLICATION_CREDENTIALS"]="/Users/zhangmingchen/desktop/directed-truck-224723-e8fd8af459c9.json"

consumer_key = "dXrq8z9Ph6MZaoO4aIphPY7EA"
consumer_secret = "QB06nE5KvYqc9gdRPDSJvsqtzCHFeaPFXL4EHp2Bzpm1C00J0U"
access_key = "1039356566519074817-iFnyvMWjjJLEf1OEkAq9wCrehgtFBu"
access_secret = "jyYdMngKjFrM8yeJs8HzkIjsPHntwTlQPTB2EpR67fJFk"


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
    video_name = screen_name + '.mp4'
    return video_name


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

    dscp_list = []

    # first result is retrieved because a single video was processed
    segment_labels = result.annotation_results[0].segment_label_annotations
    for i, segment_label in enumerate(segment_labels):

        print('video label description: {}'.format(segment_label.entity.description))
        dscp_list.append(segment_label.entity.description)
        for category_entity in segment_label.category_entities:
            print('\rLabel category description: {}'.format(category_entity.description))

    return dscp_list


def creat_db():
    ''' check if database is existed '''

    try:
        db = mysql.connector.connect(
            user='root',
            password='1234',
            host='localhost',
            database='Mini3'
        )
        print('Database "Mini3" is existed')
    except mysql.connector.Error as err:
        if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
            print('Please re-enter your user name or password')
        elif err.errno == errorcode.ER_BAD_DB_ERROR:
            print('Database does not exist')
            db = connection.MySQLConnection(
                user='root',
                password='1234',
                host='localhost',
                database='Mini3'
            )
        else:
            print(err)
    else:
        db.close()


def create_table():
    db = mysql.connector.connect(user='root', password='1234', database='Mini3')
    cursor = db.cursor()
    cursor.execute(
        "CREATE TABLE IF NOT EXISTS `add_search_record`("
        "`user_ID` varchar(30) NOT NULL,"
        "`time` date NOT NULL,"
        "`user_system` varchar(40) NOT NULL,"
        "`twitter_ID` varchar(40) NOT NULL,"
        "`video_name` varchar(46) NOT NULL,"
        "`pic_num` int(10) NOT NULL,"
        "`video_description` varchar(100) NOT NULL"
        ") ENGINE=INNODB")
    print('TABLE search_record is built')
    db.commit()
    db.close()


def add_twitter_ID(user_ID, time, user_system, screen_name, video_name, pic_num, video_description):
    db = mysql.connector.connect(user='root', password='1234', database='Mini3')
    cursor = db.cursor()
    add_twitter = ("INSERT INTO `add_search_record`"
                   "(user_ID,"
                   "time,"
                   "user_system,"
                   "twitter_ID,"
                   "video_name,"
                   "pic_num,"
                   "video_description)"
                   "VALUES (%s, %s, %s, %s, %s, %s, %s)")
    add_twitter_data = (user_ID, time, user_system, screen_name, video_name, pic_num, convert_to_string(video_description))
    cursor.execute(add_twitter, add_twitter_data)
    db.commit()
    print('TABLE add_search_record has been updated')
    db.close()


def search_word(word):
    db = mysql.connector.connect(user='root', password='1234', database='Mini3')
    cursor = db.cursor()
    query = "SELECT * FROM `add_search_record`"
    cursor.execute(query)
    match = cursor.fetchall()
    user_list = []
    for row in match:
        if word in list(row)[6]:
            if list(row)[0] not in user_list:
                user_list.append(list(row)[0])
    print('The following is the users who received the description')
    for i in user_list:
        print('\n', i)


def most_popular_descriptor():
    # delete row with empty description
    db = mysql.connector.connect(user='root', password='1234', database='Mini3')
    cursor = db.cursor()
    cursor.execute("DELETE FROM `add_search_record` WHERE video_description= ''")
    db.commit()

    query = "SELECT * FROM `add_search_record`"
    cursor.execute(query)
    match = cursor.fetchall()
    popular_dict = {}
    for row in match:
        temp_list = list(row)[6].split(';')
        temp_list = list(filter(lambda a: a!= '', temp_list))

        for word in temp_list:
            if word in popular_dict:
                popular_dict[word] += 1
            else:
                popular_dict[word] = 1
    print(popular_dict)
    for key in popular_dict.keys():
        if popular_dict[key] == max(popular_dict.values()):
            print(key)


def convert_to_string(a_list):
    string = ''
    for s in a_list:
        string = string + s + ';'
    return string


def main():
    user_ID = getpass.getuser()
    time = datetime.datetime.now()
    user_system = platform.platform()
    screen_name = input('please input twitterID:\n')
    # screen_name = '@taylorswift13'
    # screen_name = '@vangoghartist'
    # screen_name = '@zixia'
    # screen_name = '@NatGeo'
    pic_num = twitter_api(screen_name)
    video_name = make_video(screen_name, pic_num)
    video_description = video_analysis(screen_name)
    creat_db()
    create_table()
    add_twitter_ID(user_ID, time, user_system, screen_name, video_name, pic_num, video_description)
    most_popular_descriptor()
    word = input('input word:\n')
    search_word(word)


if __name__ == '__main__':
    main()



    # screen_name = '@taylorswift13'
    # screen_name = '@vangoghartist'
    # pic_num = twitter_api(screen_name)
    # make_video(screen_name, pic_num)
    # video_analysis(screen_name)



