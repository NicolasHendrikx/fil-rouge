// Écran de porte : affiche l'état d'une salle à l'instant T, d'après l'API Salles.
// Paramètres d'URL : room (identifiant de la salle), at (AAAA-MM-JJTHH:MM, facultatif : maintenant
// par défaut), api (URL de l'API, http://127.0.0.1:8000 par défaut).

const params = new URLSearchParams(window.location.search);
const roomId = params.get("room") ?? "1";
const apiUrl = params.get("api") ?? "http://127.0.0.1:8000";
const REFRESH_MS = 60_000;

const DATE_FORMAT = new Intl.DateTimeFormat("fr-BE", {
  weekday: "long",
  day: "numeric",
  month: "long",
  hour: "2-digit",
  minute: "2-digit",
});

function pad(value) {
  return String(value).padStart(2, "0");
}

// Instant affiché : le paramètre at, ou l'heure locale courante (sans fuseau, comme l'API).
function currentMoment() {
  const at = params.get("at");
  if (at) {
    return at.length === 16 ? `${at}:00` : at;
  }
  const now = new Date();
  return (
    `${now.getFullYear()}-${pad(now.getMonth() + 1)}-${pad(now.getDate())}` +
    `T${pad(now.getHours())}:${pad(now.getMinutes())}:00`
  );
}

// L'API raisonne par quarts d'heure : on interroge le début du quart d'heure en cours.
function floorToQuarter(moment) {
  const [day, time] = moment.split("T");
  const [hours, minutes] = time.split(":").map(Number);
  const total = hours * 60 + minutes - (minutes % 15 || 15);
  return `${day}T${pad(Math.floor(total / 60))}:${pad(total % 60)}:00`;
}

function hourOf(isoMoment) {
  return isoMoment.slice(11, 16);
}

function render(status, moment) {
  document.getElementById("moment").textContent = DATE_FORMAT.format(new Date(moment));
  document.getElementById("room-name").textContent = status.room.name;

  const state = document.getElementById("state");
  const detail = document.getElementById("detail");
  if (status.state === "occupied") {
    state.textContent = "Occupée";
    state.className = "state occupied";
    detail.textContent =
      `Réservée par ${status.current.organizer} jusqu'à ${hourOf(status.current.end)}`;
  } else {
    state.textContent = "Libre";
    state.className = "state free";
    detail.textContent = status.next
      ? `Prochaine réservation à ${hourOf(status.next.start)} (${status.next.organizer})`
      : "Aucune autre réservation aujourd'hui";
  }
}

function renderError(message) {
  document.getElementById("room-name").textContent = "Écran indisponible";
  document.getElementById("state").textContent = "";
  document.getElementById("state").className = "state";
  document.getElementById("detail").textContent = message;
}

async function refresh() {
  const moment = currentMoment();
  const query = new URLSearchParams({ at: floorToQuarter(moment) });
  try {
    const response = await fetch(`${apiUrl}/rooms/${roomId}/status?${query}`);
    if (response.status === 404) {
      renderError(`Salle ${roomId} inconnue`);
      return;
    }
    if (!response.ok) {
      renderError(`Erreur ${response.status} de l'API`);
      return;
    }
    render(await response.json(), moment);
  } catch (error) {
    renderError("API injoignable");
  }
}

refresh();
setInterval(refresh, REFRESH_MS);
