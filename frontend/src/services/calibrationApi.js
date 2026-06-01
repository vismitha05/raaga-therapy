export async function getCalibrationStatus(baseUrl) {
  const res = await fetch(`${baseUrl}/calibration/status`);
  if (!res.ok) throw new Error("Failed to fetch calibration status");
  return res.json();
}

