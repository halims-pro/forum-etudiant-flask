const socket = io(BASE_URL);
const user = JSON.parse(localStorage.getItem("user"));

socket.on("receiveMessage", data => {
    const div = document.createElement("div");
    div.textContent = `${data.sender} : ${data.message}`;
    document.getElementById("messages").appendChild(div);
});

function sendMessage() {
    const message = document.getElementById("message");
    const room = document.getElementById("room").value || "general";
    socket.emit("sendMessage", {
        sender: user.username,
        message: message.value,
    });
}