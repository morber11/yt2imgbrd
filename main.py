import config_utils
from video_utils import VideoUtility

def main():
    print("Hello World!")

    if not (config_utils.config_exists()):
        config_utils.get_first_time_config()

    url = input(r"Enter url")
    vid_util = VideoUtility(url, config_utils.read_key("yt2imgbrd", "default_download_path"))
    try:
        vid_util.download()
        print("Video downloaded... now converting to webm\n")
        vid_util.convert()

        print(f"Process complete. Video available at:\n{vid_util.output_file_location}")

    except Exception as e:
        print(f"An error has occurred!")
        raise Exception(e)

if __name__ == "__main__":
    main()