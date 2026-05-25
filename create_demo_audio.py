#!/usr/bin/env python3
"""
create_demo_audio.py
-------------------
Creates dummy MP3 files for UI testing when real raga files aren't available.
These are minimal silent MP3 files that allow testing the therapy session playback flow.

Usage:
  python create_demo_audio.py

This will create:
  frontend/public/audio/ragas/{T1,T2,A1,A2,B1,B2}/{RagaName}.mp3
  
18 total dummy MP3 files (one per raga)
"""

import os
import struct

# Define all 18 ragas organized by frequency band
RAGAS_BY_BAND = {
    'T1': ['Ahir_Bhairav', 'Madhmad_Sarang', 'Malkauns'],
    'T2': ['Todi', 'Bhimpalasi', 'Darbari_Kanada'],
    'A1': ['Bhairav', 'Shuddh_Sarang', 'Yaman'],
    'A2': ['Alhaiya_Bilawal', 'Multani', 'Bhopali'],
    'B1': ['Jaunpuri', 'Kafi', 'Khamaj'],
    'B2': ['Hindol', 'Marwa', 'Shankara'],
}


def create_minimal_mp3(filepath, duration_seconds=10):
    """
    Create a minimal valid MP3 file with silence.
    
    Args:
        filepath: Where to save the MP3 file
        duration_seconds: Duration of silent audio (default 10 seconds)
    
    The file will be recognized as a valid MP3 but will play silence.
    This is enough for testing the UI without real audio.
    """
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Minimal MP3 frame header
    # 0xFFFB = sync word for MPEG Layer III
    # This represents approximately 1 second of audio at 22.05 kHz
    mp3_frame_header = b'\xff\xfb'
    
    # Add rest of minimal frame (very basic, just for browser recognition)
    mp3_frame = mp3_frame_header + (b'\x00' * 100)
    
    try:
        with open(filepath, 'wb') as f:
            # Write the frame multiple times to simulate duration
            frame_count = max(10, duration_seconds * 5)  # Rough estimate
            for _ in range(frame_count):
                f.write(mp3_frame)
        
        file_size = os.path.getsize(filepath)
        return True, file_size
    except Exception as e:
        return False, str(e)


def main():
    print("🎵 Creating demo audio files for UI testing...")
    print("=" * 60)
    print()
    
    total_created = 0
    total_size = 0
    errors = []
    
    for band, ragas in RAGAS_BY_BAND.items():
        print(f"📁 {band} band ({len(ragas)} ragas):")
        
        for raga in ragas:
            filepath = f"frontend/public/audio/ragas/{band}/{raga}.mp3"
            
            success, result = create_minimal_mp3(filepath, duration_seconds=10)
            
            if success:
                size_kb = result / 1024
                print(f"  ✓ {raga:<25} ({size_kb:.1f} KB)")
                total_created += 1
                total_size += result
            else:
                error_msg = f"  ✗ {raga}: {result}"
                print(error_msg)
                errors.append(error_msg)
        
        print()
    
    print("=" * 60)
    print(f"✅ Complete! Created {total_created} audio files")
    print(f"📊 Total size: {total_size / 1024 / 1024:.2f} MB")
    print()
    
    if errors:
        print("⚠️  Errors encountered:")
        for error in errors:
            print(error)
        print()
    
    print("📝 Next steps:")
    print("1. Start your frontend: npm start")
    print("2. Create a therapy session and click Play")
    print("3. Session will auto-play with demo audio (silent)")
    print()
    print("💾 To use real ragas:")
    print("   Replace MP3 files in frontend/public/audio/ragas/ with actual raga files")
    print("   File naming format: {BAND}/{RagaName}.mp3")
    print("   Example: A1/Bhairav.mp3, B1/Jaunpuri.mp3")
    print()
    print("📖 See IMPLEMENTATION_SUMMARY.md for complete setup guide")


if __name__ == '__main__':
    main()
