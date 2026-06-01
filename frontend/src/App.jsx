import React from "react";
import { AnimatePresence, motion } from "framer-motion";
import { AudioPlayerProvider } from "./context/AudioPlayerContext";
import { EEGRealtimeProvider } from "./context/EEGRealtimeContext";
import { TherapyProvider, useTherapy } from "./context/TherapyContext";
import { HeadsetSetup } from "./screens/HeadsetSetup";
import { LandingScreen } from "./screens/LandingScreen";
import { StateSelectionScreen } from "./screens/StateSelectionScreen";
import { DurationScreen } from "./screens/DurationScreen";
import { PlayerScreen } from "./screens/PlayerScreen";
import { CompletionScreen } from "./screens/CompletionScreen";
import "./App.css";

const SCREEN_MAP = {
  headset: HeadsetSetup,
  landing: LandingScreen,
  state: StateSelectionScreen,
  duration: DurationScreen,
  player: PlayerScreen,
  completion: CompletionScreen,
};

function AppShell() {
  const { screen } = useTherapy();
  const ActiveScreen = SCREEN_MAP[screen];

  return (
    <div className="app-root">
      <div className="ambient ambient-one" />
      <div className="ambient ambient-two" />
      <AnimatePresence mode="wait">
        <motion.div
          key={screen}
          initial={{ opacity: 0, y: 14 }}
          animate={{ opacity: 1, y: 0 }}
          exit={{ opacity: 0, y: -14 }}
          transition={{ duration: 0.4, ease: "easeOut" }}
          className="screen-shell"
        >
          <ActiveScreen />
        </motion.div>
      </AnimatePresence>
    </div>
  );
}

export default function App() {
  return (
    <EEGRealtimeProvider>
      <AudioPlayerProvider>
        <TherapyProvider>
          <AppShell />
        </TherapyProvider>
      </AudioPlayerProvider>
    </EEGRealtimeProvider>
  );
}
