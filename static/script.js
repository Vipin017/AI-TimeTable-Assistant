const chatBox = document.getElementById("chatBox");
const messageInput = document.getElementById("messageInput");

const dashboard = document.getElementById("dashboard");
const fullTimetable = document.getElementById("fullTimetable");
const fullTimetableContent = document.getElementById("fullTimetableContent");

const batchDisplay = document.getElementById("batchDisplay");
const todayName = document.getElementById("todayName");
const tomorrowName = document.getElementById("tomorrowName");
const schedule = document.getElementById("schedule");


/* =========================
   DATE
========================= */

function loadDates() {

    const today = new Date();

    const tomorrow = new Date();
    tomorrow.setDate(today.getDate() + 1);

    todayName.textContent = today.toLocaleDateString(
        "en-US",
        { weekday: "long" }
    );

    tomorrowName.textContent = tomorrow.toLocaleDateString(
        "en-US",
        { weekday: "long" }
    );
}

loadDates();


/* =========================
   ADD MESSAGE
========================= */

function addMessage(message, type = "bot") {

    const wrapper = document.createElement("div");
    wrapper.className = `message ${type}-message`;

    const avatar = document.createElement("div");
    avatar.className = "avatar";
    avatar.textContent = type === "bot" ? "🤖" : "👤";

    const content = document.createElement("div");
    content.className = "message-content";

    const name = document.createElement("b");
    name.textContent = type === "bot"
        ? "AI Assistant"
        : "You";

    const text = document.createElement("p");
    text.innerHTML = message;

    content.appendChild(name);
    content.appendChild(text);

    wrapper.appendChild(avatar);
    wrapper.appendChild(content);

    chatBox.appendChild(wrapper);

    chatBox.scrollTop = chatBox.scrollHeight;
}


/* =========================
   SEND MESSAGE
========================= */

async function sendMessage() {

    const message = messageInput.value.trim();

    if (!message) {
        return;
    }

    addMessage(message, "user");

    messageInput.value = "";

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: message
            })

        });

        const data = await response.json();

        addMessage(data.reply, "bot");

        updateDashboard(message, data.reply);

    } catch (error) {

        addMessage(
            "❌ Something went wrong. Please check whether the Flask server is running.",
            "bot"
        );

        console.error(error);
    }
}


/* =========================
   ENTER KEY
========================= */

messageInput.addEventListener("keydown", function(event) {

    if (event.key === "Enter") {
        sendMessage();
    }

});


/* =========================
   QUICK ACTION
========================= */

function askBot(message) {

    dashboard.classList.remove("hidden");
    fullTimetable.classList.add("hidden");

    messageInput.value = message;

    sendMessage();
}


/* =========================
   FOCUS CHAT
========================= */

function focusChat() {

    document.querySelector(".assistant-section").scrollIntoView({
        behavior: "smooth"
    });

    setTimeout(() => {
        messageInput.focus();
    }, 500);
}


/* =========================
   DASHBOARD
========================= */

function showDashboard() {

    dashboard.classList.remove("hidden");
    fullTimetable.classList.add("hidden");

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


/* =========================
   FULL TIMETABLE
========================= */

async function showFullTimetable() {

    dashboard.classList.add("hidden");
    fullTimetable.classList.remove("hidden");

    fullTimetableContent.innerHTML = "Loading timetable...";

    try {

        const response = await fetch("/chat", {

            method: "POST",

            headers: {
                "Content-Type": "application/json"
            },

            body: JSON.stringify({
                message: "Show my full timetable"
            })

        });

        const data = await response.json();

        fullTimetableContent.innerHTML = data.reply;

    } catch (error) {

        fullTimetableContent.innerHTML =
            "❌ Unable to load timetable.";

        console.error(error);
    }

    window.scrollTo({
        top: 0,
        behavior: "smooth"
    });
}


/* =========================
   UPDATE DASHBOARD
========================= */

function updateDashboard(message, reply) {

    const lowerMessage = message.toLowerCase();

    /* Detect roll number */

    const rollMatch = lowerMessage.match(
        /(?:roll\s*(?:no|number)?\s*(?:is)?\s*)(\d{1,2})/
    );

    if (rollMatch) {

        const roll = parseInt(rollMatch[1]);

        let batch = null;

        if (roll >= 1 && roll <= 23) {
            batch = "T1";
        }

        else if (roll >= 24 && roll <= 46) {
            batch = "T2";
        }

        else if (roll >= 47 && roll <= 69) {
            batch = "T3";
        }

        else if (roll >= 70 && roll <= 92) {
            batch = "T4";
        }

        if (batch) {
            batchDisplay.textContent = batch;
        }
    }

    /* Detect batch from backend reply */

    const batchMatch = reply.match(
        /(?:Batch|batch)\s*[:.]?\s*(T[1-4])/
    );

    if (batchMatch) {
        batchDisplay.textContent = batchMatch[1];
    }

    /* Update today's schedule */

    if (
        lowerMessage.includes("today") ||
        lowerMessage.includes("timetable today")
    ) {

        schedule.innerHTML = `
            <div class="schedule-result">
                ${reply}
            </div>
        `;
    }
}


/* =========================
   INITIAL UI
========================= */

showDashboard();