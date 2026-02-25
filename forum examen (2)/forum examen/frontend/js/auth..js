function login() {
    fetch(`${BASE_URL}/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            username: username.value,
            password: password.value
        })
    })
    .then(res => res.json())
    .then(data => {
        if (data.success) {
            localStorage.setItem("user", JSON.stringify(data.user));
            window.location.href = "chat.html";
        } else {
            alert("Login incorrect");
        }
    });
}

function register() {
    fetch(`${BASE_URL}/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            nom: nom.value,
            prenom: prenom.value,
            pseudo: pseudo.value,
            username: username.value,
            password: password.value
        })
    })
    .then(res => res.json())
    .then(data => alert(data.message));
}
