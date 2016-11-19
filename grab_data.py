import requests
import youtube_dl
from bs4 import BeautifulSoup
import json

from constants import JSON_FORMAT_KWARGS
from utils import slugify

base_url = 'https://www.youtube.com/playlist?list=PLGVZCDnMOq0qLoYpkeySVtfdbQg1A_GiB'
conf_url = 'http://pydata.org/dc2016/schedule/'
conf_base_url = 'http://pydata.org'
video_dir = 'pydata-dc-2016/videos/'
tags_url = 'http://pyvideo.org/tags.html'
tag_base_url = 'http://pyvideo.org/tag/'

tough_tags = ['with', 'building', 'python']

def get_tags():
    """Gets all tags from pyvideo"""
    r = requests.get(tags_url)
    soup = BeautifulSoup(r.text)
    links = soup.find_all('a')
    links = [link for link in links if link['href'].startswith(tag_base_url)]
    return [link.text for link in links]

def get_youtube_data():
    try:
        with open('test.json') as f:
            info_dict = json.load(f)
    except:
        ydl_opts = {
            'dump_single_json': True,
            'simulate': True
        }
        with youtube_dl.YoutubeDL(ydl_opts) as ydl:
            info_dict = ydl.extract_info(base_url, download=False)
        with open('test.json', 'w') as f:
            json.dump(info_dict, f)
    
    return info_dict

def get_speakers(video):
    """Return list of speakers"""
    if ' | ' in video['title']:
        speakers = video['title'].split(' | ')[0]
        return [s.strip() for s in speakers.split(',')]
    elif ' - ' in video['title']:
        speakers = video['title'].split(' - ')[0]
        return [s.strip() for s in speakers.split(',')]
    else:
        return ['']


def get_title(video):
    """Return title"""
    print('Trying: ' + video['title'])
    if ' | ' in video['title']:
        return video['title'].split(' | ')[1]
    elif ' - ' in video['title']:
        return video['title'].split(' - ')[1]
    else:
        return video['title']

def get_related_urls(video):
    """Get related urls"""
    to_return = []
    for word in video['description'].split():
        if word.startswith('http://') or word.startswith('https://'):
            if 20 < len(word) < 100:
                to_return.append(word)
    return to_return

def get_upload_date(video):
    upload_date = video['upload_date']
    return upload_date[:4] + '-' + upload_date[4:6] + '-' + upload_date[6:8]

if __name__ == '__main__':
    info_dict = get_youtube_data()

    conf_data = requests.get(conf_url)
    soup = BeautifulSoup(conf_data.text)
    hrefs = soup.find_all(['a', 'h3'])
    conf_list = []
    for href in hrefs:
        if 'Friday Oct. 7, 2016' in href.text:
            curr_date = '2016-10-07'
        elif 'Saturday Oct. 8, 2016' in href.text:
            curr_date = '2016-10-08'
        elif 'Sunday Oct. 9, 2016' in href.text:
            curr_date = '2016-10-09'
        elif href.get('href') and 'presentation' in href['href']:
            conf_list.append((href.text, conf_base_url + href['href'], curr_date))

    all_tags = get_tags()

    for video in info_dict['entries']:
        this_video_tags = video['tags']
        recorded = ''
        title = get_title(video)
        for tag in all_tags:
            if tag in tough_tags:
                pass
            elif tag.lower() in title.lower().split():
                this_video_tags.append(tag)
            elif ' ' in tag and tag.lower() in title.lower():
                this_video_tags.append(tag)

        related_urls = get_related_urls(video)
        for presentation in conf_list:
            if title.lower().strip().replace('-', ' ') == presentation[0].lower().strip().replace('-', ' '):
                related_urls.append(presentation[1])
                recorded = presentation[2]

        upload_date = video['upload_date']

        video_dict = {
            'description': video['description'],
            'speakers': get_speakers(video),
            'thumbnail_url': video['thumbnail'],
            'title': title,
            'recorded': recorded or get_upload_date(video),
            'videos': [
                {
                    'type': 'youtube',
                    'url': video['webpage_url']
                }
                ],
            'duration': video['duration'],
            'copyright_text': video['license'],
            'language': 'eng',
            'related_urls': related_urls,
            'tags': this_video_tags
        }

        file_name = video_dir + slugify(title) + '.json'
        with open(file_name, 'w') as f:
            json.dump(video_dict, f, **JSON_FORMAT_KWARGS)