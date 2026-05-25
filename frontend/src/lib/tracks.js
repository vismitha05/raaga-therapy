export const TRIAL_RAAGAS = [
  { id: "ahir-bhairav", name: "Raga Ahir Bhairav", url: "/audio/Raga Ahir Bhairav.mp3", band: "T1", slot: "morning", modulation: "slow_tempo_soft_timbre_drone" },
  { id: "madhmad-sarang", name: "Madhmad Sarang", url: "/audio/Madhmad Sarang Jod.mp3", band: "T1", slot: "afternoon", modulation: "slow_tempo_soft_timbre_drone" },
  { id: "malkauns", name: "Raga Malkauns", url: "/audio/Raga Malkauns.mp3", band: "T1", slot: "night", modulation: "slow_tempo_soft_timbre_drone" },

  { id: "todi", name: "Raga Todi", url: "/audio/Raga Desi Todi - Raga Desi Todi - Tala Teentaal.mp3", band: "T2", slot: "morning", modulation: "gentle_rhythm_sweeping_legato" },
  { id: "bhimpalasi", name: "Raga Bhimpalasi", url: "/audio/Raga Bhimpalasi (Alap).mp3", band: "T2", slot: "afternoon", modulation: "gentle_rhythm_sweeping_legato" },
  { id: "darbari-kanada", name: "Raga Darbari Kanada", url: "/audio/Raga Darbari Kanada Alap and Jor.mp3", band: "T2", slot: "night", modulation: "gentle_rhythm_sweeping_legato" },

  { id: "bhairav", name: "Raga Bhairav", url: "/audio/Raga Bhairav.mp3", band: "A1", slot: "morning", modulation: "moderate_tempo_warm_harmonics" },
  { id: "shuddha-sarang", name: "Shuddha Sarang", url: "/audio/Shuddha Sarang (From “Bansuri”).mp3", band: "A1", slot: "afternoon", modulation: "moderate_tempo_warm_harmonics" },
  { id: "yaman", name: "Raag Yaman", url: "/audio/Raag Yaman (Aalap, Jod & Jhala).mp3", band: "A1", slot: "night", modulation: "moderate_tempo_warm_harmonics" },

  { id: "alhaiya-bilawal", name: "Alhaiya Bilawal", url: "/audio/Alhaiya Bilawal.mp3", band: "A2", slot: "morning", modulation: "flowing_tempo_bright_crisp" },
  { id: "multani", name: "Raga Multani", url: "/audio/Raga Multani.mp3", band: "A2", slot: "afternoon", modulation: "flowing_tempo_bright_crisp" },
  { id: "bhupali", name: "Raag Bhupali", url: "/audio/Raag Bhupali.mp3", band: "A2", slot: "night", modulation: "flowing_tempo_bright_crisp" },

  { id: "jaunpuri", name: "Raga Jaunpuri", url: "/audio/Raga Jaunpuri.mp3", band: "B1", slot: "morning", modulation: "fast_tempo_sharp_structured" },
  { id: "kafi", name: "Raaga Kafi", url: "/audio/Raaga Kafi.mp3", band: "B1", slot: "afternoon", modulation: "fast_tempo_sharp_structured" },
  { id: "khamaj", name: "Khamaj", url: "/audio/Koyaliya Kook Sunave.mp3", band: "B1", slot: "night", modulation: "fast_tempo_sharp_structured" },

  { id: "hindol", name: "Raag Hindol", url: "/audio/Raag Hindol.mp3", band: "B2", slot: "morning", modulation: "complex_polyrhythms_driving_percussion" },
  { id: "marwa", name: "Raga Marwa", url: "/audio/Raga Marwa.mp3", band: "B2", slot: "afternoon", modulation: "complex_polyrhythms_driving_percussion" },
  { id: "shankara", name: "Raag Shankara", url: "/audio/Raag Shankara.mp3", band: "B2", slot: "night", modulation: "complex_polyrhythms_driving_percussion" },
];

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function getTimeSlotFromDate(d = new Date()) {
  const hour = d.getHours();
  if (hour >= 6 && hour < 12) return "morning";
  if (hour >= 12 && hour < 18) return "afternoon";
  return "night";
}

export function shuffleTracks(list) {
  const arr = [...list];
  for (let i = arr.length - 1; i > 0; i -= 1) {
    const j = Math.floor(Math.random() * (i + 1));
    [arr[i], arr[j]] = [arr[j], arr[i]];
  }
  return arr;
}

function getTracksForTargetState(targetState) {
  const state = normalize(targetState);
  if (state === "focused") return TRIAL_RAAGAS.filter((t) => t.band === "B1" || t.band === "A2");
  if (state === "sleep") return TRIAL_RAAGAS.filter((t) => t.band === "T1" || t.band === "T2");
  if (state === "relaxed") return TRIAL_RAAGAS.filter((t) => t.band === "A1" || t.band === "A2");
  return TRIAL_RAAGAS;
}

export function buildTrialQueue(targetState, preferredName) {
  const pool = getTracksForTargetState(targetState);
  const slot = getTimeSlotFromDate();
  const slotPool = pool.filter((t) => t.slot === slot);
  const base = (slotPool.length ? slotPool : pool).length ? (slotPool.length ? slotPool : pool) : TRIAL_RAAGAS;
  const shuffled = shuffleTracks(base);
  if (!preferredName) return shuffled;
  const preferred = base.find((t) => normalize(t.name) === normalize(preferredName));
  if (!preferred) return shuffled;
  return [preferred, ...shuffled.filter((t) => t.id !== preferred.id)];
}

export function resolveTrialTrack(targetState, preferredName) {
  const pool = getTracksForTargetState(targetState);
  const base = pool.length ? pool : TRIAL_RAAGAS;
  if (!preferredName) return shuffleTracks(base)[0];
  return base.find((t) => normalize(t.name) === normalize(preferredName)) || shuffleTracks(base)[0];
}
