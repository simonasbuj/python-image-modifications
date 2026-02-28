export async function raiseForStatus(res) {
  if (!res.ok) {
    let message;
    try {
      const data = await res.json();
      message = data?.message || JSON.stringify(data);
    } catch {
      message = await res.text();
    }
    throw new Error(`HTTP ${res.status}: ${message}`);
  }

  const data = await res.json();
  return data;
}
