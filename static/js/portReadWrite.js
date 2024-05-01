// this file is for managing the reading and writing from port function for all buttons

document.addEventListener("DOMContentLoaded", function () {
  let buffer = "";
  const currNote = document.getElementById("curr-note");
  // const noteMessage = document.getElementById("note-message");
  const feedbackBox = document.getElementById("feedback-box");
  const currIndicator = document.getElementById("currIndicator");
  const currFingering = document.getElementById("currFingering");
  const nextNote = document.getElementById("next-note");
  let port, reader, writer;
  let textDecoder = new TextDecoderStream();

  document
    .getElementById("replayButton")
    .addEventListener("click", async function () {
      console.log(buffer);
      fetch("upload_fingering/", {
        method: "POST",
        body: buffer,
        headers: {
          "Content-Type": "text/plain",
        },
      })
        .then((response) => response.json())
        .then((data) => console.log(data))
        .catch((error) => console.error("Error:", error));
    });

  // press connect button to connect
  document
    .getElementById("connectButton")
    .addEventListener("click", async function () {
      if ("serial" in navigator) {
        try {
          // This call is now inside a user gesture event
          port = await navigator.serial.requestPort();
          await port.open({ baudRate: 9600 });

          port.readable.pipeTo(textDecoder.writable).catch((error) => {
            console.error("Stream pipe failed:", error);
            port.close();
          });

          console.log("Port connected and ready.");
        } catch (err) {
          console.error("Connection error:", err.message);
        }
      } else {
        console.log("Serial not supported");
      }
    });

  // press start button to read fingering and display reference fingering
  document
    .getElementById("startButton")
    .addEventListener("click", async function () {
      buffer = "";
      if (intervalId !== null) {
        clearInterval(intervalId);
        intervalId = null;
      }
      // document.getElementById("note-message").innerHTML =
      //   "The practice session will start soon.<br><br>";
      songReset();
      currNote.style.display = "none";
      // noteMessage.style.display = "none";
      feedbackBox.style.display = "none";
      currIndicator.style.display = "none";
      currFingering.style.display = "none";
      nextNote.style.display = "block";

      if (port && port.writable) {
        const writer = port.writable.getWriter();
        const data = new TextEncoder().encode("4");
        try {
          await writer.write(data);
          console.log("Message sent");
        } catch (error) {
          console.error("Failed to send message:", error);
        }
        writer.releaseLock();
      } else {
        console.log("Port not connected or not writable");
      }

      if (reader) {
        console.log("Reading already started.");
        return;
      }

      if (textDecoder && textDecoder.readable) {
        reader = textDecoder.readable.getReader();
        readData();
      } else {
        console.log("Connect to the port first.");
      }

      async function readData() {
        try {
          while (true) {
            const { value, done } = await reader.read();
            if (done) {
              console.log("Stream closed");
              reader.releaseLock();
              break;
            }
            buffer += value;
          }
        } catch (error) {
          console.error("Read error:", error);
        } finally {
          reader.releaseLock();
          if (port) {
            await port.close();
            console.log("Port closed");
          }
        }
      }
      updateRefNote("start");
      updateRefFingering("start");
      updateRefDescription("start");

      setTimeout(function () {
        intervalId = setInterval(updateCurrentSong, 1000);
      }, 1000);
    });

  // press end button to end displaying reference note
  document
    .getElementById("endButton")
    .addEventListener("click", async function () {
      if (port && port.writable) {
        try {
          const writer = port.writable.getWriter();
          const data = new TextEncoder().encode("2");
          await writer.write(data);
          console.log("End message sent");
        } catch (error) {
          console.error("Failed to send end message:", error);
        } finally {
          if (writer) {
            writer.releaseLock();
          }
        }
      }

      if (intervalId !== null) {
        clearInterval(intervalId);
        intervalId = null;
      }
      // document.getElementById("note-message").innerHTML =
      //   "The practice session has ended.<br><br>";
      updateRefNote("end");
      updateRefFingering("end");
      updateRefDescription("end");

      currNote.style.display = "none";
      // noteMessage.style.display = "none";
      feedbackBox.style.display = "none";
      currIndicator.style.display = "none";
      currFingering.style.display = "none";
      nextNote.style.display = "block";
    });
});
