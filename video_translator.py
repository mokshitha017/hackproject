import os
import shutil
import subprocess
import yt_dlp
import whisper
from gtts import gTTS
from pydub import AudioSegment
from deep_translator import GoogleTranslator
import warnings

warnings.filterwarnings("ignore", message="FP16 is not supported on CPU*")


def download_video_from_youtube(url, filename):
    outtmpl_path = os.path.join(os.getcwd(), "downloads")
    os.makedirs(outtmpl_path, exist_ok=True)
    try:
        print("Starting video download from YouTube...")
        ydl_opts = {
            'format': 'bestvideo+bestaudio/best',
            'outtmpl': os.path.join(outtmpl_path, filename),
            'merge_output_format': 'mp4',
            'ffmpeg_location': shutil.which("ffmpeg"),
        }
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            ydl.download([url])
        full_path = os.path.join(outtmpl_path, filename)
        if not os.path.exists(full_path):
            raise FileNotFoundError("Downloaded video file not found.")
        print(f"Video downloaded to: {full_path}")
        return full_path
    except Exception as e:
        raise RuntimeError(f"Failed to download video: {e}")


def extract_audio_from_video(video_path, audio_output_path="extracted_audio.wav"):
    try:
        print("Extracting audio from video...")
        subprocess.run([
            "ffmpeg", "-y", "-i", video_path, "-vn", "-acodec", "pcm_s16le",
            "-ar", "16000", "-ac", "1", audio_output_path
        ], check=True)
        print(f"Audio extracted to: {audio_output_path}")
        return audio_output_path
    except subprocess.CalledProcessError:
        raise RuntimeError("Failed to extract audio from video.")


def transcribe_audio(audio_file):
    try:
        print("Transcribing audio...")
        model = whisper.load_model("base")
        result = model.transcribe(audio_file)
        print("Transcription complete.")
        return result['text']
    except Exception as e:
        raise RuntimeError(f"Failed to transcribe audio: {e}")


def translate_text(text, target_language="kn"):
    try:
        print(f"Translating text to {target_language}...")
        max_chunk = 500
        chunks = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]
        translated_chunks = [
            GoogleTranslator(source='auto', target=target_language).translate(chunk)
            for chunk in chunks
        ]
        translated_text = ' '.join(translated_chunks)
        print(f"Translated text:\n{translated_text}")
        return translated_text
    except Exception as e:
        raise RuntimeError(f"Failed to translate text: {e}")


def text_to_speech(text, output_audio_path, lang="kn"):
    try:
        if not text.strip():
            raise ValueError("No text to synthesize.")
        print(f"Converting text to speech in {lang}...")

        max_chunk = 100
        chunks = [text[i:i + max_chunk] for i in range(0, len(text), max_chunk)]

        combined = AudioSegment.empty()

        for i, chunk in enumerate(chunks):
            temp_mp3 = f"temp_tts_{i}.mp3"
            tts = gTTS(chunk, lang=lang)
            tts.save(temp_mp3)
            audio = AudioSegment.from_mp3(temp_mp3)
            combined += audio
            os.remove(temp_mp3)

        combined.export(output_audio_path, format="mp3")
        print(f"TTS audio saved to: {output_audio_path}")
    except Exception as e:
        raise RuntimeError(f"Failed to convert text to speech: {e}")


def convert_mp3_to_aac(mp3_file, aac_file):
    try:
        print("Converting MP3 to AAC...")
        subprocess.run([
            "ffmpeg", "-y", "-i", mp3_file, "-c:a", "aac", "-b:a", "192k", aac_file
        ], check=True)
        print(f"AAC audio saved as: {aac_file}")
    except subprocess.CalledProcessError:
        raise RuntimeError("Failed to convert MP3 to AAC.")


def merge_audio_with_video(video_file, audio_file, output_video_file):
    try:
        print("Merging audio and video with ffmpeg...")
        result = subprocess.run([
            "ffmpeg", "-y", "-i", video_file, "-i", audio_file,
            "-c:v", "copy", "-c:a", "aac",
            "-map", "0:v:0", "-map", "1:a:0",
            output_video_file
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        print(result.stdout)
        print(result.stderr)

        if result.returncode != 0:
            raise RuntimeError("ffmpeg failed during merging.")
        if not os.path.exists(output_video_file):
            raise FileNotFoundError("Merged video file was not created.")
        print(f"Merged video saved as: {output_video_file}")
    except Exception as e:
        raise RuntimeError(f"Failed to merge audio with video: {e}")


def _process_transcription_and_translation(video_path, selected_langs, available_languages):
    final_output_dir = "final_outputs"
    os.makedirs(final_output_dir, exist_ok=True)

    extracted_audio_file = extract_audio_from_video(video_path)
    transcribed_text = transcribe_audio(extracted_audio_file)

    output_files = []

    for lang_code in selected_langs:
        lang_name = available_languages.get(lang_code, lang_code)
        print(f"\n--- Processing language: {lang_name} ({lang_code}) ---")

        mp3_audio = f"translated_audio_{lang_code}.mp3"
        aac_audio = f"translated_audio_{lang_code}.aac"
        final_video = os.path.join(final_output_dir, f"video_with_translated_audio_{lang_code}.mp4")

        translated_text = translate_text(transcribed_text, target_language=lang_code)
        text_to_speech(translated_text, mp3_audio, lang=lang_code)
        convert_mp3_to_aac(mp3_audio, aac_audio)
        merge_audio_with_video(video_path, aac_audio, final_video)

        output_files.append(final_video)

    print("\n✅ All selected language versions processed successfully!")
    return output_files


def process_youtube_video(youtube_url, selected_langs):
    try:
        available_languages = {
            "kn": "Kannada",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu",
            "ml": "Malayalam"
        }

        video_filename = "original_video.mp4"
        video_file = download_video_from_youtube(youtube_url, video_filename)
        return _process_transcription_and_translation(video_file, selected_langs, available_languages)
    except Exception as e:
        raise RuntimeError(f"Processing YouTube video failed: {e}")


def process_local_video(local_video_path, selected_langs):
    try:
        if not os.path.isfile(local_video_path):
            raise FileNotFoundError(f'The file "{local_video_path}" does not exist.')

        available_languages = {
            "kn": "Kannada",
            "hi": "Hindi",
            "ta": "Tamil",
            "te": "Telugu",
            "ml": "Malayalam"
        }

        return _process_transcription_and_translation(local_video_path, selected_langs, available_languages)
    except Exception as e:
        raise RuntimeError(f"Processing local video failed: {e}")
