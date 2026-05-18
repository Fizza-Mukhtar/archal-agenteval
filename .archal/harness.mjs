const task = process.env.ARCHAL_ENGINE_TASK;
if (!task) {
  console.error("Missing ARCHAL_ENGINE_TASK");
  process.exit(1);
}

const agentEndpoint = process.env.AGENT_ENDPOINT || "http://localhost:9001/run";

try {
  const response = await fetch(agentEndpoint, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ task, context: {} }),
  });

  if (!response.ok) {
    console.error(`Agent returned ${response.status}`);
    process.exit(1);
  }

  const result = await response.json();
  const text = result.final_output || "Task completed";
  console.log(JSON.stringify({ text }));

} catch (err) {
  console.error("Agent call failed:", err.message);
  process.exit(1);
}