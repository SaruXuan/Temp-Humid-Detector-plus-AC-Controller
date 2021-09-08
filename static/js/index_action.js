$(document).ready(function(){
	var socket = io.connect('http://localhost:8080/lab_th');
	socket.on('connect', function(){
		console.log('socketio connected.');
	})

	socket.on('status_update', function(e){
		$('#title h1').text('Temperature: ' + e.temperature + ', Humidity: ' + e.humidity);
	})
});
