#!/bin/bash
# setup-demo-audio.sh
# Creates folder structure and dummy audio files for testing

echo "🎵 Setting up demo audio structure..."

# Create folder structure for all 18 ragas across 6 bands
mkdir -p frontend/public/audio/ragas/{T1,T2,A1,A2,B1,B2}

# Define ragas for each band
declare -A RAGAS
RAGAS[T1]="Ahir_Bhairav Madhmad_Sarang Malkauns"
RAGAS[T2]="Todi Bhimpalasi Darbari_Kanada"
RAGAS[A1]="Bhairav Shuddh_Sarang Yaman"
RAGAS[A2]="Alhaiya_Bilawal Multani Bhopali"
RAGAS[B1]="Jaunpuri Kafi Khamaj"
RAGAS[B2]="Hindol Marwa Shankara"

# Create dummy audio files
for band in T1 T2 A1 A2 B1 B2; do
  for raga in ${RAGAS[$band]}; do
    echo "Creating frontend/public/audio/ragas/$band/$raga.mp3"
    
    # Create a minimal valid MP3 file (silence for testing)
    # This is a very small valid MP3 header that plays silence for ~1 second
    printf '\xFF\xFB\x10\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' > "frontend/public/audio/ragas/$band/$raga.mp3"
    
    # Add more silence to make it playable (expand to 10KB)
    for i in {1..500}; do
      printf '\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00' >> "frontend/public/audio/ragas/$band/$raga.mp3"
    done
  done
done

echo "✓ Demo audio structure created!"
echo ""
echo "Folder structure:"
find frontend/public/audio/ragas -type d | head -10
echo "..."
echo ""
echo "Files created:"
find frontend/public/audio/ragas -type f | wc -l
echo "audio files"
echo ""
echo "Note: These are dummy/silent files for UI testing only."
echo "Replace with actual raga MP3 files for real playback."
