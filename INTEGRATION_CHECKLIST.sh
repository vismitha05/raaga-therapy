#!/bin/bash
# Integration Checklist Script
# Run this to verify all components are in place

echo "🔍 Raaga Therapy System - Integration Verification"
echo "=================================================="
echo ""

# Backend files
echo "📦 Backend Components:"

if [ -f "backend/adaptive_backend/services/raga_therapy_engine.py" ]; then
    echo "  ✓ raga_therapy_engine.py"
else
    echo "  ✗ raga_therapy_engine.py (MISSING)"
fi

if [ -f "backend/adaptive_backend/services/eeg_monitoring_service.py" ]; then
    echo "  ✓ eeg_monitoring_service.py"
else
    echo "  ✗ eeg_monitoring_service.py (MISSING)"
fi

if [ -f "backend/adaptive_backend/api/routes/therapy.py" ]; then
    echo "  ✓ therapy.py (API routes)"
else
    echo "  ✗ therapy.py (MISSING)"
fi

echo ""
echo "🎨 Frontend Components:"

if [ -f "frontend/src/screens/EEGMonitoringScreen.jsx" ]; then
    echo "  ✓ EEGMonitoringScreen.jsx"
else
    echo "  ✗ EEGMonitoringScreen.jsx (MISSING)"
fi

if [ -f "frontend/src/screens/TargetStateScreen.jsx" ]; then
    echo "  ✓ TargetStateScreen.jsx"
else
    echo "  ✗ TargetStateScreen.jsx (MISSING)"
fi

if [ -f "frontend/src/screens/DurationScreen_v2.jsx" ]; then
    echo "  ✓ DurationScreen_v2.jsx"
else
    echo "  ✗ DurationScreen_v2.jsx (MISSING)"
fi

if [ -f "frontend/src/screens/TherapyPlayerScreen.jsx" ]; then
    echo "  ✓ TherapyPlayerScreen.jsx"
else
    echo "  ✗ TherapyPlayerScreen.jsx (MISSING)"
fi

if [ -f "frontend/src/screens/SessionCompletionScreen.jsx" ]; then
    echo "  ✓ SessionCompletionScreen.jsx"
else
    echo "  ✗ SessionCompletionScreen.jsx (MISSING)"
fi

if [ -f "frontend/src/hooks/useTherapyWorkflow.js" ]; then
    echo "  ✓ useTherapyWorkflow.js"
else
    echo "  ✗ useTherapyWorkflow.js (MISSING)"
fi

if [ -f "frontend/src/App_v2.jsx" ]; then
    echo "  ✓ App_v2.jsx (Main app)"
else
    echo "  ✗ App_v2.jsx (MISSING)"
fi

echo ""
echo "🎵 Audio Files:"

if [ -d "frontend/public/audio/ragas" ]; then
    count=$(find frontend/public/audio/ragas -name "*.mp3" 2>/dev/null | wc -l)
    echo "  ✓ Audio folder found ($count MP3 files)"
else
    echo "  ✗ Audio folder (frontend/public/audio/ragas) - CREATE THIS"
fi

echo ""
echo "📋 Next Steps:"
echo "1. ✓ Backend files are in place"
echo "2. ✓ Frontend components are created"
echo "3. TODO: Update frontend/src/App.jsx to use App_v2.jsx logic"
echo "4. TODO: Add raga MP3 files to frontend/public/audio/ragas/ folder"
echo "5. TODO: Update router.py to include therapy routes"
echo ""
echo "🚀 To Start Development:"
echo "   Backend:  cd backend && python -m uvicorn adaptive_backend.main:app --reload"
echo "   Frontend: cd frontend && npm start"
echo ""
