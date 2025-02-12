const socket = io.connect("/sync");
const alertHanlder = new Alert()

document.addEventListener("DOMContentLoaded", function() {
    fetch('/get_playlists')
        .then(response => response.json())
        .then(data => {
            populatePlaylists('spotify', data.spotify_playlists);
            populatePlaylists('tidal', data.tidal_playlists);
        });
});

function populatePlaylists(service, playlists) {
    const container = document.getElementById(`${service}-playlists`);
    playlists.forEach(playlist => {
        container.innerHTML += `
            <div class="d-flex p-2">
                <input type="checkbox" class="checkbox" id="${service}-${playlist.id}" value="${playlist.id}">
                <label for="${service}-${playlist.id}">${playlist.name}</label>
            </div>
        `;
    });
}

function syncPlaylists() {
    socket.emit('hello', '');
    const selectedSpotify = getSelected('spotify');
    const selectedTidal = getSelected('tidal');

    fetch('/sync_selected_playlists', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ spotify_playlists: selectedSpotify, tidal_playlists: selectedTidal })
    });
}

function getSelected(service) {
    return Array.from(document.querySelectorAll(`#${service}-playlists .checkbox:checked`))
        .map(cb => cb.value);
}

function toggleAll(service) {
    const selectAll = document.getElementById(`select-all-${service}`);
    const checkboxes = document.querySelectorAll(`input[type="checkbox"][id^="${service}-"]`);
    checkboxes.forEach(checkbox => {
        checkbox.checked = selectAll.checked;
        console.log('check')
    });
    console.log('checked')
}

socket.on('progress', function(data) {
    alertHanlder.showBar({ message: data.message})
    console.log(data.message)
});

socket.on('refuse', function() {
    console.log("xxxx")
    alertHanlder.showBar({ message: "Removed from chat", error:true})
});

socket.on('message', function(msg) {
    console.log(msg)
});
