/* Notificaciones y Alarma Sonora */

// Configuración
const POLL_INTERVAL = 10000; // 10 segundos
let lastInterestId = parseInt(localStorage.getItem('lastInterestId') || '0');
let audioCtx = null;

// Solicitar permiso de notificaciones al cargar
if (Notification.permission === "default") {
    Notification.requestPermission();
}

// Generador de Sonido (Sirena)
function playAlarm() {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }

    // Si el contexto está suspendido (por falta de interacción), intentar reanudar
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }

    const osc = audioCtx.createOscillator();
    const gainNode = audioCtx.createGain();

    osc.connect(gainNode);
    gainNode.connect(audioCtx.destination);

    // Configurar tipo de sonido (Sirena)
    osc.type = 'sawtooth';
    osc.frequency.setValueAtTime(440, audioCtx.currentTime); // La
    osc.frequency.linearRampToValueAtTime(880, audioCtx.currentTime + 0.5); // Subida de tono
    osc.frequency.linearRampToValueAtTime(440, audioCtx.currentTime + 1.0); // Bajada

    gainNode.gain.value = 0.5;

    osc.start();
    osc.stop(audioCtx.currentTime + 2); // Sonar 2 segundos
}

// Función de Polling
async function checkNewInterests() {
    try {
        // Obtenemos el ID más alto conocido por el servidor o el local
        // El endpoint recibe el último ID que conocíamos
        const res = await fetch(`/api/v1/interests/poll?last_id=${lastInterestId}`);
        const data = await res.json();

        if (data.has_new && data.last_id > lastInterestId) {
            console.log("¡Nuevos intereses detectados!", data);

            // Actualizar ID
            lastInterestId = data.last_id;
            localStorage.setItem('lastInterestId', lastInterestId);

            // 1. Alarma Sonora
            playAlarm();

            // 2. Vibración (móvil)
            if (navigator.vibrate) {
                navigator.vibrate([500, 200, 500, 200, 1000]);
            }

            // 3. Notificación Visual
            if (Notification.permission === "granted") {
                new Notification("¡Nueva Oferta de Interés!", {
                    body: `Tienes ${data.count} persona(s) interesada(s) en tus ofertas.`,
                    icon: "/static/img/logo.png" // Asegurar que existe o usar placeholder
                });
            } else {
                alert(`¡ALERTA! Tienes ${data.count} nuevo(s) interesado(s).`);
            }
        }
    } catch (e) {
        console.error("Error polling intereses:", e);
    }
}

// Iniciar Loop
setInterval(checkNewInterests, POLL_INTERVAL);

// Desbloqueo de AudioContext con primera interacción
document.addEventListener('click', function () {
    if (!audioCtx) {
        audioCtx = new (window.AudioContext || window.webkitAudioContext)();
    }
    if (audioCtx.state === 'suspended') {
        audioCtx.resume();
    }
}, { once: true });
