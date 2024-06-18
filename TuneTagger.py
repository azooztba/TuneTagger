import asyncio
import os
import requests
from shazamio import Shazam ,Serialize
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TCON, error, TALB

async def recognize_and_modify_metadata(file_path):
    try:
        shazam = Shazam()
        out = await shazam.recognize(file_path)
        # Extract track information
        track_title = out['track']['title']
        artists = out['track']['subtitle']  # Adjust based on actual structure
        artist_name = ''.join(artists) if artists else "Unknown Artist"
        genre = out['track']['genres']['primary']
        cover_image_url = out['track']['images']['coverarthq']
        artist_photo_url = out['track']['images']['background']  # Example, adjust based on Shazam's API response
        #album = out['sections'][0]['metadata'][0]['text']

        new_version_path = out
        album_info = await shazam.search_album(album_id=new_version_path["track"]["albumadamid"])
        album_serialized = Serialize.album_info(data=album_info)
        
        # Get album name
        album=album_serialized.data[0].attributes.name
        # Modify audio file metadata
        modify_audio_metadata(file_path, track_title, artist_name,album, genre, cover_image_url, artist_photo_url)

        # Rename file to track title
        rename_file(file_path, track_title)

        # Print the modified information
        print(f"Modified Metadata and Renamed File for: {file_path}")
        print(f"Song Title: {track_title}")
        print(f"Artist(s): {artist_name}")
        print(f"Genre: {genre}")
        print(f"Album: {album}")
        print("\n")

    except Exception as e:
        print(f"Error processing {file_path}: {str(e)}")
        print("\n")

def modify_audio_metadata(file_path, title, artist,album, genre, cover_image_url, artist_photo_url):
    try:
        audio = MP3(file_path, ID3=ID3)
        try:
            audio.add_tags()
        except error:
            pass
        
        # Embed cover image into audio file
        if cover_image_url:
            response = requests.get(cover_image_url)
            if response.status_code == 200:
                image_data = response.content
                audio.tags.add(
                    APIC(
                        encoding=3,  # 3 is for utf-8
                        mime='image/jpeg',  # image/jpeg or image/png
                        type=3,  # 3 is for the cover image
                        desc=u'Cover',
                        data=image_data
                    )
                )
        
        # Embed artist photo into audio file (if available)
        if artist_photo_url:
            response = requests.get(artist_photo_url)
            if response.status_code == 200:
                image_data = response.content
                audio.tags.add(
                    APIC(
                        encoding=3,  # 3 is for utf-8
                        mime='image/jpeg',  # image/jpeg or image/png
                        type=4,  # 4 is for artist photo
                        desc=u'Artist Photo',
                        data=image_data
                    )
                )
        
        # Set other metadata
        audio.tags.add(TIT2(encoding=3, text=title))  # Title
        audio.tags.add(TPE1(encoding=3, text=artist))  # Artist
        audio.tags.add(TCON(encoding=3, text=genre))  # Genre
        audio.tags.add(TALB(encoding=3, text=album))  # Album

        audio.save()

    except Exception as e:
        print(f"Error modifying metadata for {file_path}: {str(e)}")

def rename_file(file_path, new_name):
    try:
        directory = os.path.dirname(file_path)
        extension = os.path.splitext(file_path)[1]
        new_file_path = os.path.join(directory, f"{new_name}{extension}")
        os.rename(file_path, new_file_path)
        print(f"File renamed to: {new_file_path}")

    except Exception as e:
        print(f"Error renaming file {file_path} to {new_name}: {str(e)}")

async def process_directory(directory_path):
    tasks = []
    for filename in os.listdir(directory_path):
        file_path = os.path.join(directory_path, filename)
        if os.path.isfile(file_path):
            task = asyncio.create_task(recognize_and_modify_metadata(file_path))
            tasks.append(task)
    await asyncio.gather(*tasks)

async def main():
    directory_path = 'baba music usb\منوعات\اغاني حماسية ' # Replace with your directory path
    await process_directory(directory_path)

# Run the main function
asyncio.run(main())
