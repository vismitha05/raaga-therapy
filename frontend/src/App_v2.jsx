/**
 * App.jsx (Updated)
 * ---------------
 * Main application component orchestrating the complete Raga Therapy workflow.
 * Routes between EEG monitoring → State selection → Duration → Playback → Completion.
 */

import React from 'react';
import { EEGMonitoringScreen } from './screens/EEGMonitoringScreen';
import { TargetStateScreen } from './screens/TargetStateScreen';
import { DurationScreen } from './screens/DurationScreen_v2';
import { TherapyPlayerScreen } from './screens/TherapyPlayerScreen';
import { SessionCompletionScreen } from './screens/SessionCompletionScreen';
import { LandingScreen } from './screens/LandingScreen';
import {
  useTherapyWorkflow,
  WORKFLOW_SCREENS,
} from './hooks/useTherapyWorkflow';
import './App.css';

function App() {
  const workflow = useTherapyWorkflow();

  const renderScreen = () => {
    const {
      currentScreen,
      sessionId,
      eegDetection,
      targetState,
      selectedDuration,
      playlist,
      sessionComplete,
    } = workflow;

    const {
      startWorkflow,
      handleEEGScanComplete,
      handleStateSelected,
      handleDurationSelected,
      handleSessionComplete,
      startNewSession,
      goBack,
      setSessionId,
    } = workflow;

    switch (currentScreen) {
      case WORKFLOW_SCREENS.INITIAL:
        return (
          <LandingScreen
            onStart={startWorkflow}
          />
        );

      case WORKFLOW_SCREENS.EEG_MONITORING:
        return (
          <EEGMonitoringScreen
            onScanComplete={handleEEGScanComplete}
            sessionId={sessionId}
            setSessionId={setSessionId}
          />
        );

      case WORKFLOW_SCREENS.STATE_SELECTION:
        return (
          <TargetStateScreen
            sessionId={sessionId}
            detection={eegDetection}
            onStateSelected={handleStateSelected}
            onBack={goBack}
          />
        );

      case WORKFLOW_SCREENS.DURATION_SELECTION:
        return (
          <DurationScreen
            sessionId={sessionId}
            targetState={targetState}
            detection={eegDetection}
            onDurationSelected={handleDurationSelected}
            onBack={goBack}
          />
        );

      case WORKFLOW_SCREENS.THERAPY_PLAYBACK:
        return (
          <TherapyPlayerScreen
            sessionId={sessionId}
            playlist={playlist}
            detection={eegDetection}
            targetState={targetState}
            onSessionComplete={handleSessionComplete}
          />
        );

      case WORKFLOW_SCREENS.COMPLETION:
        return (
          <SessionCompletionScreen
            detection={eegDetection}
            targetState={targetState}
            duration={selectedDuration}
            playlist={playlist}
            onNewSession={startNewSession}
          />
        );

      default:
        return null;
    }
  };

  return (
    <div className="app">
      <main className="app-main">
        {renderScreen()}
      </main>

      {/* Global UI elements */}
      <style jsx>{`
        .app {
          width: 100%;
          min-height: 100vh;
          background: linear-gradient(135deg, #1a1a2e 0%, #16213e 100%);
          color: #fff;
          font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen',
            'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue',
            sans-serif;
          -webkit-font-smoothing: antialiased;
          -moz-osx-font-smoothing: grayscale;
        }

        .app-main {
          width: 100%;
          max-width: 1200px;
          margin: 0 auto;
          padding: 20px;
        }

        @media (max-width: 768px) {
          .app-main {
            padding: 10px;
          }
        }
      `}</style>
    </div>
  );
}

export default App;
