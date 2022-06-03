import subprocess
import os
import shutil
from config_utils import read_key
from pytube import YouTube
import requests
import json
from bs4 import BeautifulSoup


class RedditVideoEntity:
    def __init__(self, title, video_url, audio_url, headers):
        self.title = title
        self.video_url = video_url
        self.audio_url = audio_url
        self.headers = headers


class VideoUtility:
    def __init__(self, url, path):
        self.url = url
        self.path = clean_string(path)

        yt = YouTube(url)
        self.title = clean_string(yt.title)
        del yt

        self.output_file_location = os.path.join(self.path, self.title + ".webm")

    def download(self):
        download_youtube_video(self.url, self.title + ".mp4")

    def convert(self):
        path = os.path.join(self.path, self.title + ".mp4")
        convert_to_webm(path)


def download_youtube_video(url, filename, output_path=None):

    if output_path is None:
        output_path = read_key("yt2imgbrd", "default_download_path")

    try:
        yt = YouTube(url)
    except ConnectionError as e:
        raise ConnectionError(f"A connection error has occurred! \n{e}")

    try:
        yt.streams.filter(progressive=True,
                          file_extension="mp4").first().download(output_path=output_path,
                                                                 filename=filename)

    except Exception as e:
        raise Exception(f"An error has occurred: \n{e}")


def download_reddit_video(url, output_path=None):
    if output_path is None:
        output_path = read_key("yt2imgbrd", "default_download_path")

    # create a temporary working folder
    working_directory = output_path
    working_directory = os.path.join(working_directory, ".tmp")

    if not os.path.exists((working_directory)):
        os.mkdir(working_directory)

    try:
        # get the main video entity
        reddit_video_entity = get_reddit_data(url)

        # need to download the mp3 and mp4 seperately
        download_reddit_parts(reddit_video_entity, working_directory)
        combine_mp3_and_mp4(working_directory, reddit_video_entity.title)

        combined_path = os.path.join(working_directory, (reddit_video_entity.title + "_combined.mp4"))

        convert_to_webm(combined_path, os.path.join(output_path, reddit_video_entity.title))

    except Exception as e:
        print(f"An error has occurred!")
        raise Exception(e)

    finally:
        # cleanup - delete working directory
        shutil.rmtree(working_directory)


def get_reddit_data(url, title=None):
    """Returns a representation of the data about a reddit video"""

    headers = {"User-Agent": "Mozilla/5.0"}
    response = requests.get(url, headers=headers)
    post_id = url[url.find("comments/") + 9:]
    post_id = f"t3_{post_id[:post_id.find('/')]}"

    if (response.status_code == 200):
        soup = BeautifulSoup(response.text, "lxml")
        required_js = soup.find("script", id="data")
        json_data = json.loads(required_js.text.replace("window.___r = ", '')[:-1])

        if title is None:
            title = json_data["posts"]["models"][post_id]["title"]
            title = title.replace(' ', '_')

        dash_url = json_data["posts"]["models"][post_id]["media"]["dashUrl"]
        height = json_data["posts"]["models"][post_id]["media"]["height"]
        dash_url = dash_url[:int(dash_url.find("DASH")) + 4]
        video_url = f"{dash_url}_{height}.mp4"
        audio_url = f"{dash_url}_audio.mp4"

        return RedditVideoEntity(title, video_url, audio_url, headers)


def download_reddit_parts(reddit_video_entity, path):
    """Downloads the reddit videos components (mp3 and mp4) to a given folder"""

    title = reddit_video_entity.title
    video_url = reddit_video_entity.video_url
    audio_url = reddit_video_entity.audio_url
    headers = reddit_video_entity.headers

    with open(os.path.join(path, title + "_video.mp4"), "wb") as file:
        print("Downloading Video...", end='', flush=True)
        response = requests.get(video_url, headers=headers)
        if (response.status_code == 200):
            file.write(response.content)
            print("\rVideo Downloaded...!")
        else:
            print("\rVideo Download Failed..!")

    with open(os.path.join(path, title + "_audio.mp3"), "wb") as file:
        print("Downloading Audio...", end='', flush=True)
        response = requests.get(audio_url, headers=headers)
        if (response.status_code == 200):
            file.write(response.content)
            print("\rAudio Downloaded...!")
        else:
            print("\rAudio Download Failed..!")


def combine_mp3_and_mp4(path, title, combined_path=None):
    """Combines an mp3 audio track with an mp4 video"""

    ffmpeg = read_key("ffmpeg", "path")
    base_path = os.path.join(path, title)

    if combined_path is None:
        combined_path = base_path + "_combined.mp4"

    commands = [
                ffmpeg,
                "-i",
                f"{base_path}_video.mp4",
                "-i",
                f"{base_path}_audio.mp3",
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:v",
                "copy",
                "-y",
                f"{combined_path}"]


    return_code = subprocess.run(commands)

    if return_code.returncode == 0:
        print(f"Video & Audio downloaded succesfully")
    else:
        print("An error has occurred during the combination process")
        raise Exception(return_code)


def convert_to_webm(input, output=None):
    commands = buildFFmpegConversionCommand(input, output)

    return_code = subprocess.run(commands)

    if return_code.returncode == 0:
        print("Conversion completed succesfully!")
    else:
        print("An error has occurred during the conversion process")


def buildFFmpegConversionCommand(input, output=None):
    ffmpeg = read_key("ffmpeg", "path")

    # strip .mp4
    if output is None:
        output = input[:-4]

    threads = read_key("ffmpeg", "default_threads")
    crf = read_key("ffmpeg", "default_crf")
    bit_rate = read_key("ffmpeg", 'default_bit_rate')
    overwrite = read_key("ffmpeg", "overwrite")

    # bit rate must be at a certain value otherwise ffmpeg will not work !
    if bit_rate[-1] != "k":
        print(f"Warning, bit rate was detected as {bit_rate}. Proceeding with {bit_rate}k instead\n")
        bit_rate = bit_rate + "k"

    # mandatory commands
    commands = [
        ffmpeg,
        "-i",
        input,
        "-c:v",
        "libvpx-vp9",
        "-threads",
        threads,
        "-crf",
        crf,
        "-b:v",
        "0",
        "-b:a",
        bit_rate,
        "-c:a",
        "libopus"
    ]

    # optional commands
    if overwrite:
        commands.append("-y")

    # output must be at the end
    commands.append(output + ".webm")

    return commands


def clean_string(x):
    # x = x.replace(":","")
    x = x.replace("?", "")
    x = x.replace("<", "")
    x = x.replace(">", "")
    x = x.replace("|", "")
    x = x.replace("*", "")
    return x
