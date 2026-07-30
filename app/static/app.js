const messages = document.getElementById("messages");
const uploadForm = document.getElementById("upload-form");
const chatForm = document.getElementById("chat-form");
const uploadStatus = document.getElementById("upload-status");
const socketStatus = document.getElementById("socket-status");
const sendButton = chatForm.querySelector("button");
const history = [];

let socket = null;
let activeAssistant = null;
let activeText = "";
let activeSources = [];

function addMessage(role, text, sources = []) {
  const item = document.createElement("article");
  item.className = `message ${role}`;
  item.textContent = text;
  if (sources.length) appendSources(item, sources);
  messages.appendChild(item);
  messages.scrollTop = messages.scrollHeight;
  return item;
}

function appendSources(item, sources) {
  const sourceBox = document.createElement("div");
  sourceBox.className = "sources";
  sourceBox.textContent = "Sources: " + sources
    .map((source) => `${source.source} (${source.score})`)
    .join(", ");
  item.appendChild(sourceBox);
}

function setSocketStatus(text) {
  if (socketStatus) socketStatus.textContent = text;
}

function connectWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  socket = new WebSocket(`${protocol}://${window.location.host}/api/v1/chat/ws`);
  setSocketStatus("Connecting...");

  socket.addEventListener("open", () => {
    setSocketStatus("WebSocket connected");
    sendButton.disabled = false;
  });

  socket.addEventListener("close", () => {
    setSocketStatus("Disconnected. Reconnecting...");
    sendButton.disabled = true;
    window.setTimeout(connectWebSocket, 1500);
  });

  socket.addEventListener("error", () => {
    setSocketStatus("WebSocket error");
  });

  socket.addEventListener("message", (event) => {
    const data = JSON.parse(event.data);

    if (data.type === "start") {
      activeText = "";
      activeSources = [];
      activeAssistant = addMessage("assistant", "");
      sendButton.disabled = true;
      return;
    }

    if (data.type === "token") {
      activeText += data.content;
      activeAssistant.textContent = activeText;
      messages.scrollTop = messages.scrollHeight;
      return;
    }

    if (data.type === "sources") {
      activeSources = data.items || [];
      return;
    }

    if (data.type === "warning") {
      activeText = data.answer;
      activeAssistant = addMessage(
        "assistant",
        `${data.answer}\n\n${data.disclaimer}`
      );
      return;
    }

    if (data.type === "complete") {
      if (activeAssistant && activeSources.length) {
        appendSources(activeAssistant, activeSources);
      }
      if (activeText) history.push({ role: "assistant", content: activeText });
      activeAssistant = null;
      sendButton.disabled = socket.readyState !== WebSocket.OPEN;
      return;
    }

    if (data.type === "error") {
      if (activeAssistant && !activeText) {
        activeAssistant.textContent = `Error: ${data.message}`;
      } else {
        addMessage("assistant", `Error: ${data.message}`);
      }
      activeAssistant = null;
      sendButton.disabled = socket.readyState !== WebSocket.OPEN;
    }
  });
}

uploadForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  const file = document.getElementById("document").files[0];
  const data = new FormData();
  data.append("file", file);
  uploadStatus.textContent = "Indexing...";
  try {
    const response = await fetch("/api/v1/documents", { method: "POST", body: data });
    const result = await response.json();
    if (!response.ok) throw new Error(result.detail || "Upload failed");
    uploadStatus.textContent = `${result.filename}: ${result.chunks_added} chunks indexed.`;
  } catch (error) {
    uploadStatus.textContent = error.message;
  }
});

chatForm.addEventListener("submit", (event) => {
  event.preventDefault();
  const input = document.getElementById("question");
  const question = input.value.trim();
  if (!question || !socket || socket.readyState !== WebSocket.OPEN) return;

  const priorHistory = history.slice(-8);
  addMessage("user", question);
  history.push({ role: "user", content: question });
  input.value = "";
  socket.send(JSON.stringify({ question, history: priorHistory }));
});

sendButton.disabled = true;
connectWebSocket();
