export async function fetchLiveEEG(baseUrl) {
  const res = await fetch(`${baseUrl}/eeg/live`);
  if (!res.ok) throw new Error("Failed to fetch EEG");
  return res.json();
}

