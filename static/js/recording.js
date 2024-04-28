// this file is the js script for start and stop recording the audio for buttons

let mediaRecorder;
let audioChunks = [];

// start recording the audio
async function startRecording() {
  try {
    const stream = await navigator.mediaDevices.getUserMedia({
      audio: true,
    });
    mediaRecorder = new MediaRecorder(stream);
    audioChunks = []; // Reset chunks at the start

    mediaRecorder.ondataavailable = (event) => {
      audioChunks.push(event.data);
    };

    mediaRecorder.start();
  } catch (error) {
    console.error("Error accessing the microphone:", error);
  }
}

// stop recording the audio and output it as mp3 file
function stopRecording() {
  if (mediaRecorder) {
    mediaRecorder.stop();
    mediaRecorder.onstop = async () => {
      const audioBlob = new Blob(audioChunks, { type: "audio/mp3" });

      // Create FormData and append the audio file
      const formData = new FormData();
      formData.append("audio", audioBlob, "recording.mp3");

      // Send the audio file to the server
      fetch("upload_audio/", {
        method: "POST",
        body: formData,
      })
        .then((response) => response.json())
        .then((data) => console.log(data))
        .catch((error) => console.error("Error:", error));

      audioChunks = [];
    };
  }
}
