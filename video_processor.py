import os
import asyncio
from moviepy.editor import VideoFileClip, AudioFileClip, concatenate_videoclips
from pydub import AudioSegment
import ffmpeg
import aiofiles
from config import TEMP_DIR, get_temp_path
import subprocess
from typing import List, Tuple

class VideoProcessor:
    @staticmethod
    async def convert_video(input_path: str, output_format: str, quality: str = "high", progress_callback=None) -> str:
        """Convert video to different format with quality options"""
        output_path = get_temp_path(f"converted_{os.path.basename(input_path).split('.')[0]}.{output_format}")
        
        if progress_callback:
            await progress_callback(10, "Starting conversion...")
        
        # Quality settings
        quality_settings = {
            "high": {"crf": "23", "preset": "medium"},
            "medium": {"crf": "28", "preset": "fast"},
            "low": {"crf": "32", "preset": "veryfast"}
        }
        
        settings = quality_settings.get(quality, quality_settings["high"])
        
        try:
            # Using ffmpeg for better control
            (
                ffmpeg
                .input(input_path)
                .output(output_path, 
                       crf=settings["crf"],
                       preset=settings["preset"],
                       vcodec='libx264' if output_format in ['mp4', 'mkv'] else 'copy',
                       acodec='aac')
                .overwrite_output()
                .run(quiet=True)
            )
            
        except Exception as e:
            # Fallback to moviepy
            clip = VideoFileClip(input_path)
            clip.write_videofile(output_path, verbose=False, logger=None, 
                               bitrate="1000k" if quality == "high" else "500k")
            clip.close()
        
        if progress_callback:
            await progress_callback(100, "Conversion completed!")
        
        return output_path

    @staticmethod
    async def convert_document(input_path: str, output_format: str, progress_callback=None) -> str:
        """Convert documents between formats"""
        file_ext = os.path.splitext(input_path)[1].lower()
        output_path = get_temp_path(f"converted_{os.path.basename(input_path).split('.')[0]}.{output_format}")
        
        if progress_callback:
            await progress_callback(20, f"Converting {file_ext} to {output_format}...")
        
        try:
            if file_ext == '.pdf' and output_format in ['docx', 'txt']:
                await VideoProcessor.pdf_to_docx(input_path, output_path, output_format, progress_callback)
            elif file_ext in ['.doc', '.docx'] and output_format == 'pdf':
                await VideoProcessor.docx_to_pdf(input_path, output_path, progress_callback)
            elif file_ext in ['.jpg', '.jpeg', '.png', '.bmp'] and output_format in ['jpg', 'png', 'pdf']:
                await VideoProcessor.convert_image(input_path, output_path, output_format, progress_callback)
            else:
                raise ValueError(f"Unsupported conversion: {file_ext} to {output_format}")
                
        except Exception as e:
            raise e
        
        if progress_callback:
            await progress_callback(100, "Document conversion completed!")
        
        return output_path

    @staticmethod
    async def pdf_to_docx(input_path: str, output_path: str, output_format: str, progress_callback=None):
        """Convert PDF to DOCX or TXT"""
        try:
            if output_format == 'docx':
                # Using pdf2docx (install: pip install pdf2docx)
                from pdf2docx import Converter
                cv = Converter(input_path)
                cv.convert(output_path)
                cv.close()
            elif output_format == 'txt':
                # Using PyPDF2 for text extraction
                import PyPDF2
                with open(input_path, 'rb') as file:
                    pdf_reader = PyPDF2.PdfReader(file)
                    text = ""
                    for page in pdf_reader.pages:
                        text += page.extract_text() + "\n"
                    
                    async with aiofiles.open(output_path, 'w', encoding='utf-8') as f:
                        await f.write(text)
                        
        except ImportError:
            # Fallback: copy file with new extension
            import shutil
            shutil.copy2(input_path, output_path)

    @staticmethod
    async def docx_to_pdf(input_path: str, output_path: str, progress_callback=None):
        """Convert DOCX to PDF"""
        try:
            # Using python-docx and reportlab
            from docx import Document
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            from reportlab.lib.utils import ImageReader
            import io
            
            doc = Document(input_path)
            c = canvas.Canvas(output_path, pagesize=letter)
            y = 750  # Starting y position
            line_height = 15
            
            for paragraph in doc.paragraphs:
                text = paragraph.text
                if text.strip():
                    c.drawString(50, y, text)
                    y -= line_height
                    if y < 50:
                        c.showPage()
                        y = 750
            
            c.save()
            
        except ImportError:
            # Fallback: copy file
            import shutil
            shutil.copy2(input_path, output_path)

    @staticmethod
    async def convert_image(input_path: str, output_path: str, output_format: str, progress_callback=None):
        """Convert images between formats"""
        from PIL import Image
        
        img = Image.open(input_path)
        
        if output_format == 'pdf':
            # Convert image to PDF
            if img.mode != 'RGB':
                img = img.convert('RGB')
            img.save(output_path, "PDF", resolution=100.0)
        else:
            # Convert to other image formats
            img.save(output_path, output_format.upper())
        
        img.close()

    @staticmethod
    async def get_file_info(file_path: str) -> dict:
        """Get detailed information about file"""
        import magic
        from moviepy.editor import VideoFileClip
        from PIL import Image
        import PyPDF2
        
        file_info = {
            'size': os.path.getsize(file_path),
            'format': os.path.splitext(file_path)[1].lower(),
            'type': 'unknown'
        }
        
        mime = magic.Magic(mime=True)
        mime_type = mime.from_file(file_path)
        
        if mime_type.startswith('video/'):
            file_info['type'] = 'video'
            try:
                clip = VideoFileClip(file_path)
                file_info.update({
                    'duration': clip.duration,
                    'resolution': f"{clip.size[0]}x{clip.size[1]}",
                    'fps': clip.fps
                })
                clip.close()
            except:
                pass
                
        elif mime_type.startswith('audio/'):
            file_info['type'] = 'audio'
            
        elif mime_type.startswith('image/'):
            file_info['type'] = 'image'
            try:
                img = Image.open(file_path)
                file_info.update({
                    'resolution': f"{img.width}x{img.height}",
                    'mode': img.mode
                })
                img.close()
            except:
                pass
                
        elif mime_type == 'application/pdf':
            file_info['type'] = 'pdf'
            try:
                with open(file_path, 'rb') as f:
                    pdf = PyPDF2.PdfReader(f)
                    file_info['pages'] = len(pdf.pages)
            except:
                pass
                
        elif mime_type in ['application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document']:
            file_info['type'] = 'document'
            
        return file_info

    # Existing video methods (merge, split, etc.) remain the same
    @staticmethod
    async def merge_videos(video_paths: list, progress_callback=None) -> str:
        """Merge multiple videos"""
        output_path = get_temp_path("merged_video.mp4")
        
        if progress_callback:
            await progress_callback(10, "Loading videos...")
        
        clips = []
        for i, path in enumerate(video_paths):
            if progress_callback:
                await progress_callback(10 + (i * 30 // len(video_paths)), f"Loading video {i+1}...")
            clips.append(VideoFileClip(path))
        
        if progress_callback:
            await progress_callback(70, "Merging videos...")
        
        final_clip = concatenate_videoclips(clips)
        final_clip.write_videofile(output_path, verbose=False, logger=None)
        
        for clip in clips:
            clip.close()
        final_clip.close()
        
        if progress_callback:
            await progress_callback(100, "Merge completed!")
        
        return output_path

    @staticmethod
    async def video_to_audio(input_path: str, audio_format: str, progress_callback=None) -> str:
        """Extract audio from video"""
        output_path = get_temp_path(f"audio_{os.path.basename(input_path).split('.')[0]}.{audio_format}")
        
        if progress_callback:
            await progress_callback(20, "Extracting audio...")
        
        video = VideoFileClip(input_path)
        audio = video.audio
        
        if progress_callback:
            await progress_callback(60, "Saving audio file...")
        
        audio.write_audiofile(output_path, verbose=False, logger=None)
        video.close()
        audio.close()
        
        if progress_callback:
            await progress_callback(100, "Audio extraction completed!")
        
        return output_path

    @staticmethod
    async def compress_video(input_path: str, target_size_mb: int, progress_callback=None) -> str:
        """Compress video to target size"""
        output_path = get_temp_path(f"compressed_{os.path.basename(input_path)}")
        
        if progress_callback:
            await progress_callback(10, "Analyzing video...")
        
        clip = VideoFileClip(input_path)
        duration = clip.duration
        original_size = os.path.getsize(input_path) / (1024 * 1024)  # MB
        
        # Calculate target bitrate
        target_bitrate = (target_size_mb * 8192) / duration  # in kbps
        
        if progress_callback:
            await progress_callback(50, f"Compressing to {target_size_mb}MB...")
        
        clip.write_videofile(output_path, bitf=f"{target_bitrate}k", verbose=False, logger=None)
        clip.close()
        
        if progress_callback:
            await progress_callback(100, "Compression completed!")
        
        return output_path
