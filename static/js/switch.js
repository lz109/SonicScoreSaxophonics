document
  .getElementById("switchButton")
  .addEventListener("click", async function () {
    var h1 = document.querySelector(".song-name h1");
    if (h1.textContent.includes("Mary had a little lamb")) {
      h1.textContent = "Currently Practicing: Entire Range";
      const response = await fetch("load_data", {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: "entire_range",
      });
      const data = await response.json();
      console.log(data);
    } else if (h1.textContent.includes("Entire Range")) {
      h1.textContent = "Currently Practicing: B Flat Scale";
      const response = await fetch("load_data", {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: "b_flat",
      });
      const data = await response.json();
      console.log(data);
    } else {
      h1.textContent = "Currently Practicing: Mary had a little lamb";
      const response = await fetch("load_data", {
        method: "POST",
        headers: { "Content-Type": "text/plain" },
        body: "mhall",
      });
      const data = await response.json();
      console.log(data);
    }
  });
