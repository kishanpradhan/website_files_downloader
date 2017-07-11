from flask import Flask, render_template, Response
#from BeautifulSoup import BeautifulStoneSoup
from BeautifulSoup import *
import requests
import re
import shutil
from urlparse import urlparse
import browsercookie

app = Flask(__name__)

url = "https://videos.raywenderlich.com/courses/53-beginning-ios-10-part-1-getting-started/lessons/1"
#url = "https://player.vimeo.com/external/189237975.m3u8?s=e2edb5d1897eb54dee8cbe4b800202ed6848267b&amp;oauth2_token_id=897711146"
#url = "https://skyfire.vimeocdn.com/1499534243-0xb2c299bfad2c14a21a5035864e523705b29c1dd3/189237975/video/627169733/playlist.m3u8"

def resolve_host(url):
    parsed_uri = urlparse(url)
    host = '{uri.scheme}://{uri.netloc}'.format(uri=parsed_uri)
    return host

@app.route('/parse', methods=['GET'])
def parse_html():
    cj = browsercookie.chrome()
    print dir(cj)
    result = requests.get(url, cookies=cj)
    return Response(result.content)
    soup = BeautifulSoup(result.content)
    videos = soup.body.findAll('video')
    current_host = resolve_host(url)
    video_urls = []
    next_urls = []
    #print soup.title.string
    course = soup.body.find('section', {'id' : 'course-lessons'})
    folder_name = course.find('div', {'class': 'table-header'}).h3.string.replace('Course Lessons:', '').strip()
    lessons = course.find('ul', {'class': 'lesson-table'}).findAll('li')
    for lesson in lessons:
        lesson_name_tag = lesson.find('span', {'class': 'lesson-name'})
        if lesson.get('class') == 'active':
            file_name = lesson_name_tag.string
        else:
            next_url = lesson_name_tag.a.get('href')
            if next_url[0] == '/':
                next_url = current_host + next_url
            else:
                next_url = url + next_url
            next_urls.append(next_url)
    print next_urls
    return Response(result.content)
    ts_file = 'file.mp4'
    for video in videos:
        master_data_url = video.findChild('source').get('src')
        master_data = requests.get(master_data_url).content
        playlist_url = master_data.split('\n')[-2] # max resolution url
        playlist_data = requests.get(playlist_url).content
        video_url = re.sub('playlist.m3u8$', '', playlist_url)
        with open(ts_file, 'wb') as merged_file:
            for playlist in playlist_data.split('\n'):
                if 'chop/segment' in playlist:
                    ts_url = video_url + playlist
                    video_urls.append(ts_url)
                    ts_response = requests.get(ts_url, stream=True)
                    if ts_response.status_code == 200:
                        ts_response.raw.decode_content = True
                        shutil.copyfileobj(ts_response.raw, merged_file)
    #return render_template('main.html', links=data)
    return Response(result.content)

if __name__ == '__main__':
    app.run(debug=True)
