export function createLiveSocket(url, onMessage) {
  const ws = new WebSocket(url);
  ws.onmessage = (event) => {
    try {
      onMessage(JSON.parse(event.data));
    } catch (_e) {
      // ignore malformed frames
    }
  };
  return ws;
}

