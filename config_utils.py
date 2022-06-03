import os
import configparser

config = configparser.ConfigParser()
CONFIG_PATH = ".\config.ini"


def config_exists():
    return os.path.exists(CONFIG_PATH)


def get_first_time_config():
    print("NO CONFIG FILE DETECTED\n"
          "Some configuration is neccesary to continue.\n")

    ffmpeg_path = get_ffmpeg_path_from_user()
    create_first_time_config(ffmpeg_path)

    print("\nConfiguration complete\n")


def get_ffmpeg_path_from_user():
    while True:
        ffmpeg_path = input("Please enter the path to ffmpeg")

        # Windows only for now
        if ffmpeg_path.endswith((".exe")):
            print(f"Using {ffmpeg_path}!")
            return ffmpeg_path

        elif os.path.exists(os.path.join(ffmpeg_path, "ffmpeg.exe")):
            print(f"Found ffmpeg.exe at {ffmpeg_path}!")
            ffmpeg_path = os.path.join(ffmpeg_path, "ffmpeg.exe")

            return ffmpeg_path

        print(
            f"There does not appear to be a valid ffmpeg installation in location: {ffmpeg_path}."
            f"\nDouble check the path and try again\n")


def create_first_time_config(ffmpeg_path):
    """Writes the initial config file"""

    # yt2imgbrd
    config["yt2imgbrd"] = {
        "default_download_path": get_system_download_path(),
        "prefer_webm": "1",
        "logging" : "0"
    }

    # ffmpeg
    config["ffmpeg"] = {
        "path": ffmpeg_path,
        "default_threads": "16",
        "default_crf": "30",
        "default_bit_rate": "128k"
    }

    with open(CONFIG_PATH, "w") as configfile:
        config.write(configfile)


def get_system_download_path():
    """Returns the default downloads path for linux or windows"""
    if os.name == 'nt':
        import winreg
        sub_key = r'SOFTWARE\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders'
        downloads_guid = '{374DE290-123F-4565-9164-39C4925E467B}'
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, sub_key) as key:
            location = winreg.QueryValueEx(key, downloads_guid)[0]
        return location
    else:
        return os.path.join(os.path.expanduser('~'), 'downloads')


def read_key(section, key):
    """Reads in a key from a section in the config.ini"""
    config.read(CONFIG_PATH)
    x = config[section]
    return x[key]
