const socket = io();

socket.on('connect', () => {
    console.log('Connected to server');
});

socket.on('disconnect', () => {
    console.log('Disconnected from server');
});

socket.on('file_changed', (data) => {
    console.log(`File ${data.event}: ${data.path}`);
    location.reload();
});