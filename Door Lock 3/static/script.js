setInterval(() => {

    fetch("/api/status")
    .then(res => res.json())
    .then(data => {

        if(data.access === true){
            fetch("/api/reset", { method: "POST" });
            window.location.href = "dashboard.html";
        }

    });

}, 2000);
