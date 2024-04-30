// this file is the js script for integration

// mimic integration
function sendHttpRequest() {
  fetch("update", {
    method: "GET",
  })
    .then((response) => {
      if (!response.ok) {
        throw new Error("Network response was not ok");
      }
      return response.json();
    })
    .then((data) => {
      if (data.refNote == "end") {
        clearInterval(intervalId);
        intervalId = null;
      }
      updateCurrFingering(data.refFingering, data.currFingering);
      updateCurrNote(data.currNote);
      updateMessage(data.refNote, data.currNote);
      updateFeedback(
        data.refNote,
        data.currNote,
        data.refFingering,
        data.currFingering
      );
    })
    .catch((error) => {
      console.error(
        "There has been a problem with your fetch operation:",
        error
      );
    });
}

// helper function to find the most common line in every five lines
function findMostCommonLine(group) {
  const lineCount = {};
  let maxLine = "";
  let maxCount = 0;

  // Count each line's occurrences in the group
  group.forEach((line) => {
    if (lineCount[line]) {
      lineCount[line]++;
    } else {
      lineCount[line] = 1;
    }

    // Check if this line is now the most common
    if (lineCount[line] > maxCount) {
      maxLine = line;
      maxCount = lineCount[line];
    }
  });

  return maxLine;
}

// process the fingering info
function fingeringProcess(text) {
  const lines = text.split(/\r?\n/);
  const lineFrac = 5;
  let filteredBuffer = [];
  for (const line of lines) {
    if (line.length == 23) {
      filteredBuffer.push(line);
    }
  }
  let result = [];
  // Process groups of lines
  for (let i = 0; i < filteredBuffer.length; i += lineFrac) {
    const group = filteredBuffer.slice(i, i + lineFrac); // Get next group of 5 lines
    result.push(findMostCommonLine(group)); // Find and add the most common line
  }
  return result;
}

// the function when the replay button is clicked, responsible for sending integration requests
async function replayClicked() {
  try {
    // Process the audio
    console.log("clicking on replay");
    const response1 = await fetch("process", {
      method: "GET",
    });

    if (!response1.ok) {
      throw new Error("Response from process was not ok");
    }

    const data1 = await response1.json();

    if (data1.status === "success") {
      console.log("Audio processed successfully:", data1.result);
    } else {
      console.error("Error processing audio:", data1.message);

      return;
    }

    // Send a request to start integration
    const response2 = await fetch("integration", {
      method: "GET",
    });

    if (!response2.ok) {
      throw new Error("Response from integration was not ok");
    }

    const data2 = await response2.json();

    if (data2.status === "success") {
      console.log("Integration done:", data2.data);
      const intervalInSeconds = data2.data * 1000; // Convert seconds to milliseconds

      // Set up the interval to fetch feedback
      const feedbackInterval = setInterval(async () => {
        try {
          const feedbackResponse = await fetch("get_feedback", {
            method: "GET",
          });

          if (!feedbackResponse.ok) {
            throw new Error("Feedback request failed");
          }

          const feedbackData = await feedbackResponse.json();
          console.log(feedbackData);
          if (feedbackData.status == "success") {
            updateRefFingering(feedbackData.data.ref_fingering);
            updateRefNote(feedbackData.data.ref_audio);
            updateCurrFingering(
              feedbackData.data.ref_fingering,
              feedbackData.data.current_fingering
            );
            updateCurrNote(feedbackData.data.current_audio);
            updateFeedback(
              feedbackData.data.ref_audio,
              feedbackData.data.current_audio,
              feedbackData.data.ref_fingering,
              feedbackData.data.current_fingering
            );
            updateMessage(
              feedbackData.data.ref_audio,
              feedbackData.data.current_audio
            );
            updateRefDescription(feedbackData.data.ref_audio);
          }
        } catch (feedbackError) {
          console.error("Error fetching feedback:", feedbackError);
          clearInterval(feedbackInterval); // Stop the interval on error
        }
      }, intervalInSeconds);
    } else {
      console.error("Error in integration:", data2.message);
      alert("Error in integration: " + data2.message);
    }
  } catch (error) {
    console.error("Fetch error:", error);
  }

  // Elements display update
  document.getElementById("curr-note").style.display = "block";
  document.getElementById("note-message").style.display = "block";
  document.getElementById("feedback-box").style.display = "block";
  document.getElementById("currIndicator").style.display = "block";
  document.getElementById("currFingering").style.display = "block";
  document.getElementById("next-note").style.display = "none";
}
