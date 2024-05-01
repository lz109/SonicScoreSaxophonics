// this file is the js script for updating the diagrams on practice page

let intervalId = null;

// update the reference fingering
function updateRefFingering(refFingering) {
  for (let i = 0; i < 23; i++) {
    var path = "#Layer_1 " + "#refkey" + i;
    if (refFingering == "start" || refFingering == "end") {
      document.querySelector(path).setAttribute("fill", "white");
      continue;
    }
    if (refFingering[i] == "1") {
      if (i <= 12) {
        // left hand
        document.querySelector(path).setAttribute("fill", "#ff914d");
      } else {
        // right hand
        document.querySelector(path).setAttribute("fill", "#004aad");
      }
    } else if (refFingering[i] == "0") {
      if (i <= 12) {
        // left hand
        document.querySelector(path).setAttribute("fill", "white");
      } else {
        // right hand
        document.querySelector(path).setAttribute("fill", "white");
      }
    }
  }
}

// update the reference description
function updateRefDescription(note) {
  fetch("/static/data/fingeringDict.json")
    .then((response) => response.json())
    .then((data) => {
      if (note == "start" || note == "end") {
        document.getElementById("left-hand").innerHTML =
          "Left Hand:<br>A desciption for left hand fingering<br> will display here once the practice starts.<br><br><br>";
        document.getElementById("right-hand").innerHTML =
          "Right Hand:<br>A desciption for right hand fingering<br> will display here once the practice starts.<br><br><br>";
      } else {
        const leftHand = note + "-left";
        const rightHand = note + "-right";
        document.getElementById("left-hand").innerHTML =
          data[leftHand] || "Description not found.";
        document.getElementById("right-hand").innerHTML =
          data[rightHand] || "Description not found.";
      }
    })
    .catch((error) =>
      console.error("Error fetching fingering dictionary:", error)
    );
}

// update the reference note
function updateRefNote(note) {
  var newText = "Current Note: " + note;
  if (note == "start") {
    nextText = "Waiting to start...";
  } else if (note == "end") {
    nextText = "ended";
  } else {
    document.getElementById("ref-note").textContent = newText;
    const newSrc = "/static/images/" + note + "-note.png";
    document.getElementById("ref-note-img").src = newSrc;
  }
}

// update current fingering
function updateCurrFingering(refFingering, currFingering) {
  for (let i = 0; i < currFingering.length; i++) {
    var path = "#Layer_1 " + "#key" + i;
    if (refFingering == "start" || refFingering == "end") {
      document.querySelector(path).setAttribute("fill", "white");
      continue;
    }
    if (refFingering[i] != currFingering[i]) {
      if (refFingering[i] == "1") {
        document.querySelector(path).setAttribute("fill", "#a4a4a4");
      } else if (refFingering[i] == "0") {
        document.querySelector(path).setAttribute("fill", "#ff3131");
      }
    } else {
      if (refFingering[i] == "1") {
        document.querySelector(path).setAttribute("fill", "#348c0c");
      } else if (refFingering[i] == "0") {
        document.querySelector(path).setAttribute("fill", "white");
      }
    }
  }

  if (refFingering == "start" || refFingering == "end") {
    document.getElementById("correct-indicator").src =
      "/static/images/correctIndicator.png";
  } else if (refFingering == currFingering) {
    document.getElementById("correct-indicator").src =
      "/static/images/correctIndicator.png";
  } else {
    document.getElementById("correct-indicator").src =
      "/static/images/incorrectIndicator.png";
  }
}

// update current note
function updateCurrNote(note) {
  var newText = "Played Note: " + note + "<br>";
  if (note == "R") {
    newText = "No Note detected";
  }
  document.getElementById("curr-note").innerHTML = newText;
}

// update next up note
function updateNext(next) {
  document.getElementById("next-note").textContent = next;
}

// update message
function updateMessage(refNote, currNote) {
  var newText = "";
  if (refNote == "start") {
    return;
  } else if (refNote == "end") {
    newText = "The practice session ends!<br><br>";
  } else if (refNote == currNote) {
    newText = "You played the note correctly!<br><br>";
  } else if (currNote == "R") {
    newText = "Your note is not detected.<br><br>";
  } else {
    newText =
      "You played " + currNote + " instead of correct " + refNote + ".<br><br>";
  }
  // document.getElementById("note-message").innerHTML = newText;
}

// update the feedback
function updateFeedback(refNote, currNote, refFingering, currFingering) {
  let newText = "";
  if (refNote == "start") {
    return;
  }
  if (refNote == "end") {
    newText = "Press Start to start practicing.";
  } else if (refFingering == currFingering && refNote == currNote) {
    newText =
      "Your fingering and note pitch match with the reference. Good Job!";
  } else if (currNote == "R") {
    newText =
      "Your note is not detected. If you are playing, please check the microphone.";
  } else if (refFingering == currFingering && refNote != currNote) {
    newText =
      "Your fingering is correct but pitch is not.<br> Please check: <br>1. Is your embouchure overly tight or loose?<br> 2. Is your mouthpiece positioned correctly? <br>3. Is your air flow consistent?";
  } else if (refFingering != currFingering) {
    newText =
      "Your fingering is incorrect. Please adjust fingering based on the fingering diagram.";
  }
  console.log(newText);
  document.getElementById("feedback").innerHTML = newText;
}

// update current song, should be modified to contain the song name
function updateCurrentSong() {
  fetch("playsong", {
    method: "GET",
  })
    .then((response) => response.json())
    .then((data) => {
      updateRefFingering(data.refFingering);
      updateRefDescription(data.refNote);
      updateRefNote(data.refNote);
      updateNext(data.next);
      console.log(data);
    });
}
